from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
import logging
from sqlalchemy.orm import Session

from app.db import get_db
from app.core.config import settings
from app.schemas.document import UploadResponse
from app.services.document_service import DocumentService

router = APIRouter(prefix="", tags=["documents"])


@router.post("/documents", response_model=UploadResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="A document file is required.")

    try:
        content = file.file.read(settings.max_file_size_mb * 1024 * 1024 + 1)
        service = DocumentService(db)
        document = service.create_document(file.filename, content, file.content_type)
        return UploadResponse(
            id=document.id,
            filename=document.filename,
            title=document.title,
            size=document.size,
            page_count=document.page_count,
            status=document.status,
            processing_error=document.processing_error,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except Exception as exc:  # pragma: no cover - safety guard
        logging.getLogger(__name__).exception("Document processing failed")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to process the document. Check the backend logs.") from exc


@router.get("/documents/{document_id}")
def get_document(document_id: int, db: Session = Depends(get_db)) -> dict[str, object]:
    service = DocumentService(db)
    document = service.get_document(document_id)
    if document is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document was not found.")

    return {
        "id": document.id,
        "filename": document.filename,
        "title": document.title,
        "size": document.size,
        "page_count": document.page_count,
        "status": document.status,
        "processing_error": document.processing_error,
    }


@router.get("/documents")
def list_documents(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    service = DocumentService(db)
    documents = service.list_documents()
    return [
        {
            "id": item.id,
            "filename": item.filename,
            "title": item.title,
            "size": item.size,
            "page_count": item.page_count,
            "status": item.status,
            "created_at": item.created_at.isoformat(),
        }
        for item in documents
    ]
