from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import Sequence


@lru_cache(maxsize=1)
def get_tokenizer():
    from transformers import AutoTokenizer
    from app.core.config import settings
    return AutoTokenizer.from_pretrained(settings.qa_model_name, use_fast=True)


@dataclass
class ChunkInfo:
    chunk_index: int
    page_start: int
    page_end: int
    text: str


class ChunkingService:
    """Overlapping token windows sliced from original text, preserving evidence."""

    def __init__(self, tokenizer_name=None, max_context_tokens=320,
                 chunk_overlap_tokens=64, max_question_tokens=64, tokenizer=None):
        if not 0 <= chunk_overlap_tokens < max_context_tokens:
            raise ValueError("Overlap must be smaller than the context budget.")
        self.tokenizer = tokenizer or get_tokenizer()
        self.max_context_tokens = max_context_tokens
        self.chunk_overlap_tokens = chunk_overlap_tokens

    def chunk_pages(self, pages: Sequence[dict[str, object]]) -> list[ChunkInfo]:
        chunks = []
        for page in pages:
            text = str(page.get("clean_text", "")).strip()
            if not text:
                continue
            offsets = self.tokenizer(text, add_special_tokens=False,
                                     return_offsets_mapping=True, truncation=False)["offset_mapping"]
            step = self.max_context_tokens - self.chunk_overlap_tokens
            for start in range(0, len(offsets), step):
                end = min(start + self.max_context_tokens, len(offsets))
                passage = text[offsets[start][0]:offsets[end - 1][1]]
                chunks.append(ChunkInfo(len(chunks), int(page["page_number"]),
                                        int(page["page_number"]), passage))
                if end == len(offsets):
                    break
        return chunks
