from __future__ import annotations

from datetime import datetime

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    page_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(30), nullable=False, default="UPLOADED")
    storage_location: Mapped[str] = mapped_column(String(500), nullable=False)
    processing_error: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(default=datetime.utcnow, onupdate=datetime.utcnow)

    pages: Mapped[list["Page"]] = relationship(back_populates="document", cascade="all, delete-orphan")
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")


class Page(Base):
    __tablename__ = "pages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    page_number: Mapped[int] = mapped_column(Integer, nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    clean_text: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped[Document] = relationship(back_populates="pages")


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    document_id: Mapped[int] = mapped_column(ForeignKey("documents.id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    page_start: Mapped[int] = mapped_column(Integer, nullable=False)
    page_end: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)

    document: Mapped[Document] = relationship(back_populates="chunks")
