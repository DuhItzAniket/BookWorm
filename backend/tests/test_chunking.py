from __future__ import annotations

from app.services.chunking_service import ChunkingService


def test_chunking_service_respects_token_budget() -> None:
    service = ChunkingService(max_context_tokens=32, chunk_overlap_tokens=8)
    paragraph = (
        "BookWorm is a retrieval based question answering system that reads PDFs and extracts "
        "the most relevant evidence before answering a user question with source-aware snippets. "
        "This paragraph is intentionally longer than a small token budget to ensure the chunker "
        "splits the document into multiple searchable units."
    )
    pages = [
        {"page_number": 1, "clean_text": " ".join([paragraph] * 3)},
        {"page_number": 2, "clean_text": " ".join([paragraph] * 2)},
    ]

    chunks = service.chunk_pages(pages)

    assert chunks
    for chunk in chunks:
        token_count = len(service.tokenizer.encode(chunk.text, add_special_tokens=False))
        assert token_count <= 32
        assert chunk.page_start >= 1
        assert chunk.page_end >= chunk.page_start


def test_chunking_service_tracks_page_boundaries() -> None:
    service = ChunkingService(max_context_tokens=64, chunk_overlap_tokens=10)
    page_one = "This is the first page of a short document that should remain in the first chunk."
    page_two = "This is the second page of the same document and should begin a new chunk segment."

    chunks = service.chunk_pages([
        {"page_number": 1, "clean_text": page_one},
        {"page_number": 2, "clean_text": page_two},
    ])

    assert chunks
    assert chunks[0].page_start == 1
    assert chunks[0].page_end >= 1
    assert any(chunk.page_start == 2 or chunk.page_end == 2 for chunk in chunks)
