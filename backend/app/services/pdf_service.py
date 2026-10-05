from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from html import unescape
from pathlib import Path, PurePosixPath
from uuid import uuid4
from xml.etree import ElementTree as ET

import fitz

from app.core.config import settings


TEXT_EXTENSIONS = {".txt", ".md", ".csv", ".html", ".htm"}
DOCUMENT_EXTENSIONS = {".docx", ".epub"}
SUPPORTED_EXTENSIONS = {".pdf"} | TEXT_EXTENSIONS | DOCUMENT_EXTENSIONS


@dataclass
class ValidatedDocument:
    file_name: str
    extension: str
    page_count: int
    is_valid: bool
    size_bytes: int
    content_type: str


def sanitize_filename(file_name: str) -> str:
    base_name = Path(file_name).name or "document.pdf"
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", base_name)
    cleaned = cleaned.strip("._")
    return cleaned or "document.pdf"


def _resolve_extension(file_name: str, content_type: str | None = None) -> str:
    lowered_name = file_name.lower()
    for extension in sorted(SUPPORTED_EXTENSIONS, key=len, reverse=True):
        if lowered_name.endswith(extension):
            return extension

    raise ValueError("Unsupported document format. Supported formats include PDF, TXT, MD, DOCX, EPUB, and HTML files.")


def _decode_text_bytes(content: bytes) -> str:
    for encoding in ("utf-8-sig", "cp1252"):
        try:
            return content.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError("Text must use UTF-8 or Windows-1252 encoding.")


def _strip_html(raw_html: str) -> str:
    cleaned = re.sub(r"<script.*?</script>", " ", raw_html, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<style.*?</style>", " ", cleaned, flags=re.IGNORECASE | re.DOTALL)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    cleaned = unescape(cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _check_archive(archive):
    entries = archive.infolist()
    if len(entries) > 5000 or sum(item.file_size for item in entries) > 40 * 1024 * 1024:
        raise ValueError("Archive expands beyond the 40 MB / 5000 entry limit.")
    if any(item.flag_bits & 1 for item in entries):
        raise ValueError("Encrypted archives are not supported.")


def _extract_docx_text(content: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        _check_archive(archive)
        if "word/document.xml" not in archive.namelist():
            raise ValueError("Invalid DOCX file: no document content was found.")

        root = ET.fromstring(archive.read("word/document.xml"))
        namespace = {"w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"}
        paragraphs: list[str] = []

        for paragraph in root.findall(".//w:p", namespace):
            texts = [node.text or "" for node in paragraph.findall(".//w:t", namespace)]
            text = "".join(texts).strip()
            if text:
                paragraphs.append(text)

        if not paragraphs:
            raise ValueError("Invalid DOCX file: document text could not be extracted.")

        return "\n".join(paragraphs)


def _extract_epub_text(content: bytes) -> str:
    with zipfile.ZipFile(io.BytesIO(content)) as archive:
        _check_archive(archive)
        container_path = "META-INF/container.xml"
        if container_path not in archive.namelist():
            raise ValueError("Invalid EPUB file: missing container metadata.")

        container_root = ET.fromstring(archive.read(container_path))
        container_namespace = {"c": "urn:oasis:names:tc:opendocument:xmlns:container"}
        root_files = container_root.findall(".//c:rootfile", container_namespace)
        if not root_files:
            raise ValueError("Invalid EPUB file: no root file was found.")

        opf_path = root_files[0].attrib.get("full-path", "")
        if not opf_path:
            raise ValueError("Invalid EPUB file: missing OPF path.")

        opf_root = ET.fromstring(archive.read(opf_path))
        namespace = {"opf": "http://www.idpf.org/2007/opf"}
        manifest_items = opf_root.findall(".//opf:item", namespace)
        manifest = {item.attrib.get("id"): item.attrib.get("href", "")
                    for item in manifest_items if "xhtml" in item.attrib.get("media-type", "")}
        spine = opf_root.findall(".//opf:spine/opf:itemref", namespace)
        chapter_paths = [manifest[item.attrib.get("idref")] for item in spine
                         if item.attrib.get("idref") in manifest]

        if not chapter_paths:
            raise ValueError("Invalid EPUB file: no readable chapter content was found.")

        sections: list[str] = []
        base_dir = str(PurePosixPath(opf_path).parent)
        for href in chapter_paths:
            full_path = str(PurePosixPath(base_dir) / href) if base_dir != "." else href
            try:
                raw_html = archive.read(full_path)
            except KeyError:
                continue
            sections.append(_strip_html(_decode_text_bytes(raw_html)))

        combined = "\n".join(section for section in sections if section)
        if not combined:
            raise ValueError("Invalid EPUB file: extracted text was empty.")
        return combined


def validate_document_file(file_name: str, content: bytes, content_type: str | None = None) -> ValidatedDocument:
    if not content:
        raise ValueError("Invalid document: empty file uploaded.")

    size_limit_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > size_limit_bytes:
        raise ValueError(
            f"File too large: {len(content) / (1024 * 1024):.2f} MB exceeds the {settings.max_file_size_mb} MB limit."
        )

    extension = _resolve_extension(file_name, content_type)

    if extension == ".pdf":
        if content_type and "pdf" not in content_type.lower() and not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF: file type is not a valid PDF.")
        if not content.startswith(b"%PDF-"):
            raise ValueError("Invalid PDF: file signature does not match a PDF file.")
        if not file_name.lower().endswith(".pdf"):
            raise ValueError("Invalid PDF: filename must end with .pdf.")

        try:
            pdf_document = fitz.open(stream=content, filetype="pdf")
            if pdf_document.needs_pass:
                pdf_document.close()
                raise ValueError("Encrypted PDFs are not supported.")
            page_count = pdf_document.page_count
            pdf_document.close()
        except Exception as exc:  # pragma: no cover - thin wrapper for invalid PDFs
            raise ValueError("Invalid PDF: could not be opened for extraction.") from exc

        if page_count == 0:
            raise ValueError("Invalid PDF: no pages were found in this document.")
        if page_count > settings.max_pages:
            raise ValueError(f"Invalid PDF: document exceeds the maximum allowed page count of {settings.max_pages}.")

        return ValidatedDocument(
            file_name=sanitize_filename(file_name),
            extension=extension,
            page_count=page_count,
            is_valid=True,
            size_bytes=len(content),
            content_type=content_type or "application/pdf",
        )

    if extension in TEXT_EXTENSIONS:
        if not file_name.lower().endswith(tuple(TEXT_EXTENSIONS)):
            raise ValueError("Unsupported document type for text extraction.")
        return ValidatedDocument(
            file_name=sanitize_filename(file_name),
            extension=extension,
            page_count=1,
            is_valid=True,
            size_bytes=len(content),
            content_type=content_type or "text/plain",
        )

    if extension == ".docx":
        try:
            _extract_docx_text(content)
        except Exception as exc:  # pragma: no cover - validation wrapper
            raise ValueError("Invalid DOCX file: could not extract readable content.") from exc
        return ValidatedDocument(
            file_name=sanitize_filename(file_name),
            extension=extension,
            page_count=1,
            is_valid=True,
            size_bytes=len(content),
            content_type=content_type or "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )

    if extension == ".epub":
        try:
            _extract_epub_text(content)
        except Exception as exc:  # pragma: no cover - validation wrapper
            raise ValueError("Invalid EPUB file: could not extract readable content.") from exc
        return ValidatedDocument(
            file_name=sanitize_filename(file_name),
            extension=extension,
            page_count=1,
            is_valid=True,
            size_bytes=len(content),
            content_type=content_type or "application/epub+zip",
        )

    raise ValueError("Unsupported document format. Supported formats include PDF, TXT, MD, DOCX, EPUB, and HTML files.")


def extract_pdf_pages(content: bytes) -> list[dict[str, str | int]]:
    document = fitz.open(stream=content, filetype="pdf")
    pages: list[dict[str, str | int]] = []
    try:
        for page_number in range(document.page_count):
            page = document[page_number]
            raw_text = page.get_text("text") or ""
            cleaned = " ".join(raw_text.split())
            pages.append({
                "page_number": page_number + 1,
                "raw_text": raw_text,
                "clean_text": cleaned,
            })
    finally:
        document.close()

    return pages


def extract_document_pages(file_name: str, content: bytes) -> list[dict[str, str | int]]:
    extension = _resolve_extension(file_name)

    if extension == ".pdf":
        return extract_pdf_pages(content)

    if extension in TEXT_EXTENSIONS:
        if b"\x00" in content:
            raise ValueError("Binary content is not supported as a text document.")
        text = _decode_text_bytes(content)
        if extension in {".html", ".htm"}:
            text = _strip_html(text)
        if not text.strip():
            raise ValueError("Document text is empty after extraction.")
        return [{
            "page_number": 1,
            "raw_text": text,
            "clean_text": " ".join(text.split()),
        }]

    if extension == ".docx":
        text = _extract_docx_text(content)
        return [{
            "page_number": 1,
            "raw_text": text,
            "clean_text": " ".join(text.split()),
        }]

    if extension == ".epub":
        text = _extract_epub_text(content)
        return [{
            "page_number": 1,
            "raw_text": text,
            "clean_text": " ".join(text.split()),
        }]

    raise ValueError("Unsupported document format for extraction.")


def save_document_to_storage(file_name: str, content: bytes) -> str:
    storage_dir = Path(settings.upload_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(file_name)
    target_path = storage_dir / f"{uuid4()}_{safe_name}"
    target_path.write_bytes(content)
    return str(target_path)


def validate_pdf_file(file_name: str, content: bytes, content_type: str | None = None) -> ValidatedDocument:
    if not content:
        raise ValueError("Invalid PDF: empty file uploaded.")

    detected_extension = _resolve_extension(file_name, content_type) if file_name.lower().endswith((".pdf", ".txt", ".md", ".csv", ".html", ".htm", ".docx", ".epub")) else ".pdf"
    if detected_extension != ".pdf":
        raise ValueError("Invalid PDF: file type is not a valid PDF.")

    if content_type and "pdf" not in content_type.lower() and not content.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF: file type is not a valid PDF.")

    if not content.startswith(b"%PDF-"):
        raise ValueError("Invalid PDF: file signature does not match a PDF file.")

    if not file_name.lower().endswith(".pdf"):
        raise ValueError("Invalid PDF: filename must end with .pdf.")

    size_limit_bytes = settings.max_file_size_mb * 1024 * 1024
    if len(content) > size_limit_bytes:
        raise ValueError(
            f"File too large: {len(content) / (1024 * 1024):.2f} MB exceeds the {settings.max_file_size_mb} MB limit."
        )

    try:
        pdf_document = fitz.open(stream=content, filetype="pdf")
        page_count = pdf_document.page_count
        pdf_document.close()
    except Exception as exc:  # pragma: no cover - thin wrapper for invalid PDFs
        raise ValueError("Invalid PDF: could not be opened for extraction.") from exc

    if page_count == 0:
        raise ValueError("Invalid PDF: no pages were found in this document.")

    if page_count > settings.max_pages:
        raise ValueError(f"Invalid PDF: document exceeds the maximum allowed page count of {settings.max_pages}.")

    return ValidatedDocument(
        file_name=sanitize_filename(file_name),
        extension=".pdf",
        page_count=page_count,
        is_valid=True,
        size_bytes=len(content),
        content_type=content_type or "application/pdf",
    )


def save_pdf_to_storage(file_name: str, content: bytes) -> str:
    return save_document_to_storage(file_name, content)
