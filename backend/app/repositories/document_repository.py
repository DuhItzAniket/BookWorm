from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.document import Chunk, Document, Page


class DocumentRepository:
    def __init__(self, session: Session):
        self.session = session

    def create_document(self, document: Document) -> Document:
        self.session.add(document)
        self.session.commit()
        self.session.refresh(document)
        return document

    def get_document(self, document_id: int) -> Document | None:
        return self.session.get(Document, document_id)

    def list_documents(self) -> list[Document]:
        return self.session.scalars(select(Document).order_by(Document.created_at.desc())).all()

    def delete_document(self, document_id: int) -> None:
        document = self.get_document(document_id)
        if document is not None:
            self.session.delete(document)
            self.session.commit()

    def add_page(self, page: Page) -> Page:
        self.session.add(page)
        self.session.commit()
        self.session.refresh(page)
        return page

    def add_chunk(self, chunk: Chunk) -> Chunk:
        self.session.add(chunk)
        self.session.commit()
        self.session.refresh(chunk)
        return chunk
