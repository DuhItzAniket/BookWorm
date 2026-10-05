from __future__ import annotations

from pathlib import Path
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.document import Document, Page
from app.repositories.document_repository import DocumentRepository
from app.services.pdf_service import (extract_document_pages, save_document_to_storage,
                                      sanitize_filename, validate_document_file)


class DocumentService:
    def __init__(self, session: Session):
        self.repository = DocumentRepository(session)

    def create_document(self, file_name: str, content: bytes, content_type=None) -> Document:
        validated = validate_document_file(file_name, content, content_type)
        pages = extract_document_pages(file_name, content)
        count = sum(len(str(p["clean_text"])) for p in pages)
        if not count:
            raise ValueError("No readable text found. Scanned PDFs need OCR before uploading.")
        if count > settings.max_extracted_chars:
            raise ValueError("Extracted text exceeds the 2 million character limit. Split the document.")
        safe_name = sanitize_filename(file_name)[:200]
        location = save_document_to_storage(safe_name, content)
        document = Document(filename=safe_name, title=safe_name.rsplit(".", 1)[0],
                            size=len(content), page_count=validated.page_count,
                            status="READY", storage_location=location)
        document.pages = [Page(page_number=int(p["page_number"]), raw_text=str(p["raw_text"]),
                               clean_text=str(p["clean_text"])) for p in pages]
        try:
            return self.repository.create_document(document)
        except Exception:
            self.repository.session.rollback()
            Path(location).unlink(missing_ok=True)
            raise

    def get_document(self, document_id):
        return self.repository.get_document(document_id)

    def list_documents(self):
        return self.repository.list_documents()
