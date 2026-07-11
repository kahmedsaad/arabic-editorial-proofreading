from __future__ import annotations

from io import BytesIO
from pathlib import Path

from docx import Document as DocxDocument

from app.dataset.importer import strip_html


def extract_text_from_docx_bytes(data: bytes) -> str:
    document = DocxDocument(BytesIO(data))
    parts: list[str] = []
    for paragraph in document.paragraphs:
        text = paragraph.text.strip()
        if text:
            parts.append(text)
    return "\n\n".join(parts)


def extract_text_from_docx_path(path: Path) -> str:
    return extract_text_from_docx_bytes(path.read_bytes())


def extract_text_from_upload(filename: str, data: bytes) -> str:
    lower = filename.lower()
    if lower.endswith(".docx"):
        return extract_text_from_docx_bytes(data)
    text = data.decode("utf-8", errors="replace")
    if lower.endswith((".html", ".htm")) or "<" in text[:200]:
        return strip_html(text)
    return text.replace("\r\n", "\n")
