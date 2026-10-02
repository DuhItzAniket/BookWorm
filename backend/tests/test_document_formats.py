from __future__ import annotations

from app.services.pdf_service import validate_document_file


def test_validate_document_accepts_plain_text_files() -> None:
    payload = b"This is a plain text book chapter.\nIt includes several lines of content for BookWorm."

    result = validate_document_file(
        file_name="chapter.txt",
        content=payload,
        content_type="text/plain",
    )

    assert result.is_valid is True
    assert result.extension == ".txt"
    assert result.page_count == 1
