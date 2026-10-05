from __future__ import annotations
import logging
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db import get_db
from app.models.document import Chunk, Document
from app.services.chunking_service import ChunkingService
from app.services.qa_service import Passage, answer_question, get_tokenizer
from app.services.web_search import search_web

router = APIRouter(tags=["question answering"])
logger = logging.getLogger(__name__)


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=500)
    mode: Literal["document", "web"] = "document"
    document_id: int | None = Field(default=None, gt=0)

    @field_validator("question")
    @classmethod
    def trim_question(cls, value):
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Enter a question of at least three characters.")
        return value


@router.get("/capabilities")
def capabilities():
    return {"web_search": bool(settings.brave_search_api_key), "model": settings.qa_model_name,
            "max_file_size_mb": settings.max_file_size_mb,
            "formats": ["pdf", "docx", "epub", "txt", "md", "csv", "html", "htm"]}


@router.post("/questions")
def ask(payload: Question, db: Session = Depends(get_db)):
    try:
        if len(get_tokenizer().encode(payload.question, add_special_tokens=False)) > 64:
            raise HTTPException(422, "Please shorten your question to 64 model tokens or fewer.")
        if payload.mode == "web":
            passages = search_web(payload.question)
        else:
            if payload.document_id is None:
                raise HTTPException(422, "Choose a document first.")
            document = db.get(Document, payload.document_id)
            if document is None:
                raise HTTPException(404, "Document was not found.")
            chunks = document.chunks
            if not chunks:
                generated = ChunkingService().chunk_pages([
                    {"page_number": p.page_number, "clean_text": p.clean_text}
                    for p in sorted(document.pages, key=lambda p: p.page_number)])
                chunks = [Chunk(document_id=document.id, **vars(chunk)) for chunk in generated]
                db.add_all(chunks)
                db.commit()
            passages = [Passage(c.text, c.page_start, document.filename) for c in chunks]
        result = answer_question(payload.question, passages)
        return {**result, "mode": payload.mode,
                "evidence_type": "search snippets" if payload.mode == "web" else "uploaded document"}
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Question answering failed")
        detail = "Question answering is unavailable. Check model setup and backend logs."
        if payload.mode == "web" and not settings.brave_search_api_key:
            detail = "Web search is not configured on this server."
        raise HTTPException(503, detail) from exc
