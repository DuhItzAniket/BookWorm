from __future__ import annotations

import io

import fitz
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.pdf_service import validate_pdf_file


def _make_pdf_text_document(text: str, pages: int = 2) -> bytes:
    doc = fitz.open()
    for page_index in range(pages):
        page = doc.new_page()
        page.insert_text((72, 72), f"{text} - Page {page_index + 1}")
    pdf_bytes = doc.tobytes()
    doc.close()
    return pdf_bytes


def test_validate_pdf_accepts_valid_document() -> None:
    pdf_bytes = _make_pdf_text_document("This is a valid BookWorm test PDF.")

    result = validate_pdf_file(
        file_name="sample.pdf",
        content=pdf_bytes,
        content_type="application/pdf",
    )

    assert result.page_count == 2
    assert result.is_valid is True
    assert result.extension == ".pdf"


def test_validate_pdf_rejects_invalid_file() -> None:
    with pytest.raises(ValueError, match="Invalid PDF"):
        validate_pdf_file(
            file_name="sample.txt",
            content=b"not a real pdf",
            content_type="text/plain",
        )


def test_upload_document_endpoint_creates_document() -> None:
    client = TestClient(app)
    pdf_bytes = _make_pdf_text_document("BookWorm upload pipeline test.")

    response = client.post(
        "/documents",
        files={"file": ("sample.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
    )
    print(response.status_code, response.text)

    assert response.status_code == 200
    payload = response.json()
    assert payload["filename"] == "sample.pdf"
    assert payload["status"] == "READY"
    assert payload["page_count"] == 2
