"""Offline tests isolate storage and never download model weights."""
import re
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import settings
from app.db import Base, get_db
from app.main import app


class WordTokenizer:
    def __call__(self, text, **kwargs):
        return {"offset_mapping": [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]}
    def encode(self, text, **kwargs):
        return list(range(len(text.split())))


@pytest.fixture(autouse=True)
def isolated_app(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    def database():
        with factory() as db:
            yield db
    app.dependency_overrides[get_db] = database
    monkeypatch.setattr(settings, "upload_dir", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "demo_access_token", "")
    monkeypatch.setattr(settings, "brave_search_api_key", "")
    from app.services import chunking_service
    from app.api import routes_questions
    monkeypatch.setattr(chunking_service, "get_tokenizer", lambda: WordTokenizer())
    monkeypatch.setattr(routes_questions, "get_tokenizer", lambda: WordTokenizer())
    yield
    app.dependency_overrides.clear()
    engine.dispose()
