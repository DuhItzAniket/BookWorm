from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Sequence

from transformers import AutoTokenizer

from app.services.text_cleaning import clean_document_text


@dataclass
class ChunkInfo:
    chunk_index: int
    page_start: int
    page_end: int
    text: str


class ChunkingService:
    def __init__(
        self,
        tokenizer_name: str = "distilbert-base-uncased",
        max_context_tokens: int = 384,
        chunk_overlap_tokens: int = 50,
        max_question_tokens: int = 64,
    ) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(tokenizer_name, use_fast=True)
        self.max_context_tokens = max_context_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens
        self.max_question_tokens = max_question_tokens

    def _split_into_paragraphs(self, text: str) -> list[str]:
        normalized = clean_document_text(text)
        if not normalized:
            return []

        paragraphs = [segment.strip() for segment in re.split(r"\n\s*\n+", normalized) if segment.strip()]
        return paragraphs if paragraphs else [normalized]

    def _encode(self, text: str) -> list[int]:
        return self.tokenizer.encode(text, add_special_tokens=False)

    def _split_oversized_paragraph(self, paragraph: str) -> list[str]:
        words = paragraph.split()
        if not words:
            return []

        segments: list[str] = []
        current_segment: list[str] = []
        current_tokens: list[int] = []

        for word in words:
            word_tokens = self._encode(word)
            if current_tokens and len(current_tokens) + len(word_tokens) > self.max_context_tokens:
                segments.append(" ".join(current_segment))
                current_segment = [word]
                current_tokens = word_tokens[:]
            else:
                current_segment.append(word)
                current_tokens.extend(word_tokens)

        if current_segment:
            segments.append(" ".join(current_segment))

        return segments

    def _finalize_chunk(
        self,
        chunk_text: str,
        start_page: int,
        end_page: int,
        chunk_index: int,
    ) -> ChunkInfo:
        return ChunkInfo(
            chunk_index=chunk_index,
            page_start=start_page,
            page_end=end_page,
            text=clean_document_text(chunk_text),
        )

    def chunk_pages(self, pages: Sequence[dict[str, object]]) -> list[ChunkInfo]:
        if not pages:
            return []

        chunks: list[ChunkInfo] = []
        current_paragraphs: list[str] = []
        current_tokens: list[int] = []
        current_chunk_index = 0
        start_page = int(pages[0]["page_number"])
        end_page = start_page

        def flush_current_chunk() -> None:
            nonlocal current_chunk_index, start_page, end_page
            if not current_paragraphs:
                return

            chunk_text = " ".join(current_paragraphs)
            chunks.append(self._finalize_chunk(chunk_text, start_page, end_page, current_chunk_index))
            current_chunk_index += 1
            current_paragraphs.clear()
            current_tokens.clear()

        for page in pages:
            page_number = int(page["page_number"])
            page_text = str(page.get("clean_text", "")).strip()
            if not page_text:
                continue

            for paragraph in self._split_into_paragraphs(page_text):
                paragraph_parts = self._split_oversized_paragraph(paragraph)
                if not paragraph_parts:
                    continue

                for part in paragraph_parts:
                    part_tokens = self._encode(part)

                    if current_tokens and len(current_tokens) + len(part_tokens) > self.max_context_tokens:
                        flush_current_chunk()

                    if not current_paragraphs:
                        start_page = page_number

                    current_paragraphs.append(part)
                    current_tokens.extend(part_tokens)
                    end_page = page_number

                    if len(current_tokens) >= self.max_context_tokens:
                        flush_current_chunk()

        if current_paragraphs:
            flush_current_chunk()

        return chunks
