from __future__ import annotations

import re


def normalize_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\n +", "\n", text)
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def fix_hyphenated_line_breaks(text: str) -> str:
    text = re.sub(r"-\n\s*", "", text)
    text = re.sub(r"\s+-\s+", "-", text)
    return text


def clean_document_text(text: str) -> str:
    clean_text = fix_hyphenated_line_breaks(text)
    clean_text = normalize_whitespace(clean_text)
    return clean_text
