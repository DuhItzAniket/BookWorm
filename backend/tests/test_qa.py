import io
import zipfile
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings
from app.services.chunking_service import ChunkingService
from app.services.qa_service import Passage, retrieve, answer_question
from app.services.pdf_service import extract_document_pages, validate_document_file


class Reader:
    def read(self, question, context):
        if "Hogwarts" not in context:
            return {"answer": "", "score": 0, "start": 0, "end": 0}
        start = context.index("Hogwarts")
        return {"answer": "Hogwarts", "score": .8, "start": start, "end": start + 8}


def test_retrieves_and_cites_exact_answer():
    passages = [Passage("Harry studies at Hogwarts.", page=3), Passage("The ocean is blue.")]
    answer = answer_question("Where does Harry study?", passages, Reader())
    assert answer["answer"] == "Hogwarts"
    assert answer["sources"][0]["page"] == 3
    assert not answer["no_answer"]


def test_abstains_without_relevant_evidence():
    assert answer_question("galaxy spaceship", [Passage("Harry studies at Hogwarts.")], Reader())["no_answer"]
    assert retrieve("test", [Passage("! ?")]) == []


def test_rejects_ungrounded_model_output():
    class BadReader:
        def read(self, *args):
            return {"answer": "made up", "score": .99, "start": 0, "end": 7}
    assert answer_question("Harry", [Passage("Harry studies at Hogwarts.")], BadReader())["no_answer"]


def test_overlap_and_page_attribution():
    chunks = ChunkingService(max_context_tokens=5, chunk_overlap_tokens=2).chunk_pages([
        {"page_number": 7, "clean_text": "one two three four five six seven eight nine"}])
    assert chunks[0].text.split()[-2:] == chunks[1].text.split()[:2]
    assert all(c.page_start == c.page_end == 7 for c in chunks)
    with pytest.raises(ValueError):
        ChunkingService(max_context_tokens=5, chunk_overlap_tokens=5)


def test_upload_ask_and_missing_document(monkeypatch):
    from app.services import qa_service
    monkeypatch.setattr(qa_service, "get_reader", lambda: Reader())
    client = TestClient(app)
    doc = client.post("/documents", files={"file": ("story.txt", b"Harry studies at Hogwarts.", "text/plain")}).json()
    result = client.post("/questions", json={"question": "Where does Harry study?", "document_id": doc["id"]})
    assert result.status_code == 200
    assert result.json()["answer"] == "Hogwarts"
    assert client.post("/questions", json={"question": "Where is Harry?", "document_id": 999}).status_code == 404
    assert client.post("/questions", json={"question": "   "}).status_code == 422
    assert client.post("/questions", json={"question": "Who is Harry?", "mode": "web"}).status_code == 503


def test_auth_and_search_capability(monkeypatch):
    monkeypatch.setattr(settings, "demo_access_token", "test-only-secret")
    client = TestClient(app)
    assert client.get("/documents").status_code == 401
    assert client.get("/documents", headers={"Authorization": "Bearer test-only-secret"}).status_code == 200
    assert client.get("/api/health").status_code == 200


def test_scanned_pdf_and_invalid_archive_rejected():
    import fitz
    pdf = fitz.open(); pdf.new_page()
    client = TestClient(app)
    assert client.post("/documents", files={"file": ("scan.pdf", pdf.tobytes(), "application/pdf")}).status_code == 400
    pdf.close()
    with pytest.raises(ValueError):
        validate_document_file("bad.epub", b"not a zip")
    with pytest.raises(ValueError):
        validate_document_file("old.doc", b"binary", "application/msword")
    with pytest.raises(ValueError):
        extract_document_pages("binary.txt", b"a\x00b")


def test_epub_spine_order_and_windows_paths():
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        z.writestr("META-INF/container.xml", '<container xmlns="urn:oasis:names:tc:opendocument:xmlns:container"><rootfiles><rootfile full-path="OEBPS/content.opf"/></rootfiles></container>')
        z.writestr("OEBPS/content.opf", '<package xmlns="http://www.idpf.org/2007/opf"><manifest><item id="two" href="two.xhtml" media-type="application/xhtml+xml"/><item id="one" href="one.xhtml" media-type="application/xhtml+xml"/></manifest><spine><itemref idref="one"/><itemref idref="two"/></spine></package>')
        z.writestr("OEBPS/one.xhtml", "<p>First chapter.</p>")
        z.writestr("OEBPS/two.xhtml", "<p>Second chapter.</p>")
    text = extract_document_pages("book.epub", buf.getvalue())[0]["clean_text"]
    assert text == "First chapter. Second chapter."


def test_web_mode_keeps_citations_and_does_not_read_document(monkeypatch):
    from app.api import routes_questions
    from app.services import qa_service
    monkeypatch.setattr(routes_questions, "search_web", lambda q: [Passage("Harry studies at Hogwarts.", title="Example", url="https://example.com/story")])
    monkeypatch.setattr(qa_service, "get_reader", lambda: Reader())
    result = TestClient(app).post("/questions", json={"question": "Where does Harry study?", "mode": "web"}).json()
    assert result["mode"] == "web"
    assert result["sources"][0]["url"] == "https://example.com/story"


def test_size_limit(monkeypatch):
    monkeypatch.setattr(settings, "max_file_size_mb", 1)
    response = TestClient(app).post("/documents", files={"file": ("large.txt", b"x" * (1024 * 1024 + 1), "text/plain")})
    assert response.status_code == 400
