from pathlib import Path

import pymupdf
import pytest
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app
from app.services.ocr_service import OCRUnavailable, enrich_pdf_pages
from app.services.pdf_service import extract_pdf_pages


def scanned_pdf(mixed=False):
    with pymupdf.open() as pdf:
        if mixed:
            pdf.new_page().insert_text((30, 40), "This is the original native text on the first page.")
        page = pdf.new_page(width=200, height=200)
        image = pymupdf.Pixmap(pymupdf.csRGB, pymupdf.IRect(0, 0, 20, 20), False)
        image.clear_with(255)
        page.insert_image(page.rect, stream=image.tobytes("png"))
        return pdf.tobytes()


class FakeGlypharis:
    def __init__(self):
        self.paths = []

    def predict(self, image_path):
        assert image_path.is_file()
        self.paths.append(image_path)
        return {"text": "Harry studies at Hogwarts.", "lines": [
            {"text": "Harry studies at Hogwarts.", "confidence": 0.4, "bbox": [1, 2, 190, 20]}
        ], "processing_time_ms": 8, "model_version": "test-fixture-only"}


def test_mixed_pdf_disabled_does_not_silently_skip_scanned_page():
    data = scanned_pdf(mixed=True)
    with pytest.raises(ValueError, match="pages 2 need OCR"):
        enrich_pdf_pages(data, extract_pdf_pages(data))


def test_mixed_pdf_preserves_native_page_and_ocr_provenance():
    data = scanned_pdf(mixed=True)
    pages = extract_pdf_pages(data)
    native = pages[0].copy()
    provider = FakeGlypharis()
    provenance = enrich_pdf_pages(data, pages, provider)
    assert pages[0] == native
    assert pages[1]["page_number"] == 2
    assert pages[1]["clean_text"] == "Harry studies at Hogwarts."
    assert provenance[0]["page_number"] == 2
    assert provenance[0]["details"]["lines"][0]["confidence"] == .4
    assert provenance[0]["details"]["review_required"]
    assert all(not path.exists() for path in provider.paths)


def test_invalid_ocr_output_is_not_indexed():
    class Invalid(FakeGlypharis):
        def predict(self, image_path):
            value = super().predict(image_path)
            value["lines"][0]["confidence"] = float("nan")
            return value
    data = scanned_pdf()
    with pytest.raises(OCRUnavailable, match="contract"):
        enrich_pdf_pages(data, extract_pdf_pages(data), Invalid())


def test_render_limit_prevents_inference(monkeypatch):
    monkeypatch.setattr(settings, "ocr_max_pixels", 1000)
    provider = FakeGlypharis()
    data = scanned_pdf()
    with pytest.raises(ValueError, match="pixel limit"):
        enrich_pdf_pages(data, extract_pdf_pages(data), provider)
    assert not provider.paths


def test_ocr_page_limit(monkeypatch):
    monkeypatch.setattr(settings, "ocr_max_pages", 1)
    with pymupdf.open(stream=scanned_pdf(), filetype="pdf") as single, pymupdf.open() as combined:
        combined.insert_pdf(single)
        combined.insert_pdf(single)
        data = combined.tobytes()
    with pytest.raises(ValueError, match="current limit is 1"):
        enrich_pdf_pages(data, extract_pdf_pages(data), FakeGlypharis())


def test_missing_release_fails_clearly_without_saving(monkeypatch):
    monkeypatch.setattr(settings, "ocr_provider", "glypharis")
    monkeypatch.setattr(settings, "glypharis_model_path", "")
    client = TestClient(app)
    response = client.post("/documents", files={"file": ("scan.pdf", scanned_pdf(), "application/pdf")})
    assert response.status_code == 503
    assert client.get("/documents").json() == []


def test_ocr_source_survives_upload_and_question(monkeypatch):
    from app.services import ocr_service, qa_service
    from test_qa import Reader
    monkeypatch.setattr(settings, "ocr_provider", "glypharis")
    monkeypatch.setattr(ocr_service, "_provider", FakeGlypharis())
    monkeypatch.setattr(qa_service, "get_reader", lambda: Reader())
    client = TestClient(app)
    uploaded = client.post("/documents", files={"file": ("mixed.pdf", scanned_pdf(True), "application/pdf")})
    assert uploaded.status_code == 200
    answer = client.post("/questions", json={"document_id": uploaded.json()["id"], "question": "Where does Harry study?"}).json()
    source = answer["sources"][0]
    assert source["page"] == 2
    assert source["ocr_model_version"] == "test-fixture-only"
    assert source["ocr_review_required"] is True
