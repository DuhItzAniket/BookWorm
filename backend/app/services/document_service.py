from __future__ import annotations

from sqlalchemy.orm import Session

from app.models.document import Document, Page
from app.repositories.document_repository import DocumentRepository
from app.services.pdf_service import (
    extract_document_pages,
    save_document_to_storage,
    sanitize_filename,
    validate_document_file,
)


class DocumentService:
    def __init__(self, session: Session):
        self.repository = DocumentRepository(session)

    def create_document(self, file_name: str, content: bytes, content_type: str | None = None) -> Document:
        validated = validate_document_file(file_name=file_name, content=content, content_type=content_type)
        safe_name = sanitize_filename(file_name)
        storage_location = save_document_to_storage(safe_name, content)
        extracted_pages = extract_document_pages(file_name, content)

        document = Document(
            filename=safe_name,
            title=safe_name.rsplit(".", 1)[0] if "." in safe_name else safe_name,
            size=len(content),
            page_count=validated.page_count,
            status="READY",
            storage_location=storage_location,
            processing_error=None,
        )
        created_document = self.repository.create_document(document)

        for page_data in extracted_pages:
            page = Page(
                document_id=created_document.id,
                page_number=int(page_data["page_number"]),
                raw_text=str(page_data["raw_text"]),
                clean_text=str(page_data["clean_text"]),
            )
            self.repository.add_page(page)

        return created_document

    def get_document(self, document_id: int) -> Document | None:
        return self.repository.get_document(document_id)

    def list_documents(self) -> list[Document]:
        return self.repository.list_documents()
