from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentRead(BaseModel):
    id: int
    filename: str
    title: str
    size: int
    page_count: int
    status: str
    processing_error: str | None = None
    created_at: datetime


class DocumentListItem(BaseModel):
    id: int
    filename: str
    title: str
    page_count: int
    status: str
    size: int
    created_at: datetime


class PageRead(BaseModel):
    id: int
    page_number: int
    raw_text: str
    clean_text: str


class UploadResponse(BaseModel):
    id: int = Field(..., description="Document identifier")
    filename: str
    title: str
    size: int
    page_count: int
    status: str
    processing_error: str | None = None
