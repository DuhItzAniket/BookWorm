"""Optional bridge to the draft Glypharis Python API; no model dependency at import time."""
from __future__ import annotations

import math
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
from typing import Protocol

import pymupdf
from pydantic import BaseModel, ConfigDict, Field, ValidationError

from app.core.config import settings


class OCRUnavailable(RuntimeError):
    """A configured OCR backend cannot provide trustworthy structured output."""


class OCRLine(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    text: str = Field(max_length=20_000)
    confidence: float = Field(ge=0, le=1)
    bbox: tuple[float, float, float, float]
    polygon: list[tuple[float, float]] | None = None
    raw_confidence: float | None = Field(default=None, ge=0, le=1)


class OCRResult(BaseModel):
    model_config = ConfigDict(allow_inf_nan=False)
    text: str = Field(max_length=2_000_000)
    lines: list[OCRLine] = Field(max_length=10_000)
    processing_time_ms: float = Field(ge=0)
    model_version: str = Field(min_length=1, max_length=200)


class OCRProvider(Protocol):
    def predict(self, image_path: Path) -> dict: ...


class GlypharisProvider:
    def __init__(self):
        self._engine = None
        self._lock = Lock()

    def predict(self, image_path: Path) -> dict:
        # Keep loading and inference serialized on the shared CPU/GPU resource.
        with self._lock:
            if self._engine is None:
                if not settings.glypharis_model_path:
                    raise OCRUnavailable("Set GLYPHARIS_MODEL_PATH to a validated release before enabling OCR.")
                try:
                    from glypharis import GlypharisOCR
                    self._engine = GlypharisOCR.from_pretrained(settings.glypharis_model_path)
                except Exception as exc:
                    raise OCRUnavailable("Glypharis is not ready. Install its validated release and configure the model path.") from exc
            try:
                return self._engine.predict(str(image_path)).to_dict()
            except Exception as exc:
                raise OCRUnavailable("Glypharis could not read this page. Check the OCR service logs.") from exc


_provider = GlypharisProvider()


def enrich_pdf_pages(content: bytes, pages: list[dict], provider: OCRProvider | None = None):
    """OCR only image-bearing pages with little native text; retain PDF page identity.

    Return per-page provenance separately for atomic persistence. Never silently
    accept an image-only chapter just because other PDF pages contain text.
    """
    provenance = []
    with pymupdf.open(stream=content, filetype="pdf") as pdf:
        candidates = []
        for page, extracted in zip(pdf, pages, strict=True):
            # get_image_info includes inline images that get_images may omit.
            if len(str(extracted["clean_text"]).strip()) < settings.ocr_min_native_chars and page.get_image_info():
                candidates.append(page.number)
        if not candidates:
            return provenance
        if settings.ocr_provider == "disabled" and provider is None:
            numbers = ", ".join(str(i + 1) for i in candidates[:10])
            raise ValueError(f"PDF pages {numbers} need OCR. Glypharis integration is prepared but disabled until its model is ready.")
        if len(candidates) > settings.ocr_max_pages:
            raise ValueError(f"This PDF needs OCR on {len(candidates)} pages; the current limit is {settings.ocr_max_pages}. Split the PDF.")
        provider = provider or _provider
        with TemporaryDirectory(prefix="bookworm-ocr-") as directory:
            for index in candidates:
                page = pdf[index]
                scale = settings.ocr_render_dpi / 72
                width, height = math.ceil(page.rect.width * scale), math.ceil(page.rect.height * scale)
                if width * height > settings.ocr_max_pixels:
                    raise ValueError(f"PDF page {index + 1} exceeds the OCR render pixel limit. Reduce OCR_RENDER_DPI.")
                pixmap = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), colorspace=pymupdf.csRGB, alpha=False)
                path = Path(directory) / f"page-{index + 1}.png"
                pixmap.save(path)
                try:
                    result = OCRResult.model_validate(provider.predict(path))
                except (ValidationError, TypeError) as exc:
                    raise OCRUnavailable("Glypharis output does not match the agreed OCR contract.") from exc
                if not result.text.strip() or not result.lines:
                    raise ValueError(f"OCR found no readable text on PDF page {index + 1}.")
                for line in result.lines:
                    x0, y0, x1, y1 = line.bbox
                    if not (0 <= x0 < x1 <= pixmap.width and 0 <= y0 < y1 <= pixmap.height):
                        raise OCRUnavailable("Glypharis returned a box outside the rendered image.")
                pages[index]["raw_text"] = result.text
                pages[index]["clean_text"] = " ".join(result.text.split())
                provenance.append({"page_number": index + 1, "method": "glypharis",
                                   "model_version": result.model_version,
                                   "details": {**result.model_dump(), "render_dpi": settings.ocr_render_dpi,
                                               "image_width": pixmap.width, "image_height": pixmap.height,
                                               "confidence_semantics": "unverified; treat as raw",
                                               "review_required": True}})
                path.unlink()
    return provenance
