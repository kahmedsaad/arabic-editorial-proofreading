from __future__ import annotations

import json
import re
import zipfile
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path

from bs4 import BeautifulSoup

_BEFORE_SUFFIXES = ("_BEFORE.txt", "_BEFORE.html", "_before.txt", "_before.html")
_AFTER_SUFFIXES = ("_AFTER.txt", "_AFTER.html", "_after.txt", "_after.html")


@dataclass
class DiffSpan:
    op: str  # insert | delete | replace | unchanged
    original_text: str
    corrected_text: str
    original_start: int
    original_end: int
    corrected_start: int
    corrected_end: int


@dataclass
class ImportedPair:
    pair_id: str
    original_text: str
    corrected_text: str
    diff_spans: list[DiffSpan]
    source: str
    requires_human_classification: bool = True
    before_path: str = ""
    after_path: str = ""


def strip_html(text: str) -> str:
    if "<" not in text:
        return text.replace("\r\n", "\n")
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    # Prefer paragraph breaks
    for br in soup.find_all("br"):
        br.replace_with("\n")
    for p in soup.find_all("p"):
        p.append("\n")
    cleaned = soup.get_text("\n")
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.replace("\r\n", "\n").strip()


def read_article_file(path: Path) -> str:
    raw = path.read_text(encoding="utf-8", errors="replace")
    return strip_html(raw)


def _stem_key(name: str) -> str | None:
    for suffix in (*_BEFORE_SUFFIXES, *_AFTER_SUFFIXES):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return None


def _is_before(name: str) -> bool:
    return any(name.endswith(s) for s in _BEFORE_SUFFIXES)


def _is_after(name: str) -> bool:
    return any(name.endswith(s) for s in _AFTER_SUFFIXES)


def discover_pairs(directory: Path) -> list[tuple[str, Path, Path]]:
    """Return (pair_id, before_path, after_path) matched by filename stem."""
    files = [p for p in directory.iterdir() if p.is_file()]
    before: dict[str, Path] = {}
    after: dict[str, Path] = {}
    for path in files:
        key = _stem_key(path.name)
        if key is None:
            continue
        if _is_before(path.name):
            before[key] = path
        elif _is_after(path.name):
            after[key] = path

    pairs: list[tuple[str, Path, Path]] = []
    for key in sorted(set(before) & set(after)):
        pair_id = re.sub(r"[^\w\-]+", "_", key, flags=re.UNICODE).strip("_") or "pair"
        pairs.append((pair_id, before[key], after[key]))
    return pairs


def split_paragraphs(text: str) -> list[str]:
    parts = [p.strip() for p in re.split(r"\n\s*\n", text.replace("\r\n", "\n"))]
    return [p for p in parts if p]


def _para_span(paras: list[str], start_idx: int, end_idx: int) -> tuple[str, int, int]:
    """Return joined text and char offsets for paras[start_idx:end_idx]."""
    if start_idx >= end_idx or start_idx >= len(paras):
        full = "\n\n".join(paras)
        pos = len(full) if not paras else len("\n\n".join(paras[:start_idx]))
        if paras and start_idx > 0:
            pos = len("\n\n".join(paras[:start_idx])) + 2
        elif start_idx == 0:
            pos = 0
        else:
            pos = len(full)
        return "", pos, pos
    text = "\n\n".join(paras[start_idx:end_idx])
    prefix = "\n\n".join(paras[:start_idx])
    start = 0 if start_idx == 0 else len(prefix) + 2
    return text, start, start + len(text)


def align_paragraphs(original: str, corrected: str) -> list[DiffSpan]:
    """Conservative paragraph alignment using SequenceMatcher on paragraph lists."""
    left = split_paragraphs(original) or ([original] if original else [])
    right = split_paragraphs(corrected) or ([corrected] if corrected else [])
    matcher = SequenceMatcher(a=left, b=right, autojunk=False)
    spans: list[DiffSpan] = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                a_text, os, oe = _para_span(left, i1 + offset, i1 + offset + 1)
                b_text, cs, ce = _para_span(right, j1 + offset, j1 + offset + 1)
                spans.append(DiffSpan("unchanged", a_text, b_text, os, oe, cs, ce))
        elif tag == "replace":
            a_text, os, oe = _para_span(left, i1, i2)
            b_text, cs, ce = _para_span(right, j1, j2)
            spans.append(DiffSpan("replace", a_text, b_text, os, oe, cs, ce))
        elif tag == "delete":
            a_text, os, oe = _para_span(left, i1, i2)
            _, cs, _ = _para_span(right, j1, j1)
            spans.append(DiffSpan("delete", a_text, "", os, oe, cs, cs))
        elif tag == "insert":
            b_text, cs, ce = _para_span(right, j1, j2)
            _, os, _ = _para_span(left, i1, i1)
            spans.append(DiffSpan("insert", "", b_text, os, os, cs, ce))
    return spans


def import_pair(pair_id: str, before: Path, after: Path, source: str) -> ImportedPair:
    original = read_article_file(before)
    corrected = read_article_file(after)
    spans = align_paragraphs(original, corrected)
    return ImportedPair(
        pair_id=pair_id,
        original_text=original,
        corrected_text=corrected,
        diff_spans=spans,
        source=source,
        requires_human_classification=True,
        before_path=str(before),
        after_path=str(after),
    )


def ensure_pairs_dir(source: Path, work_dir: Path) -> Path:
    """Accept a directory of pairs or a zip; never modify originals."""
    if source.is_dir():
        return source
    if source.is_file() and source.suffix.lower() == ".zip":
        extract_to = work_dir / "pairs_extracted"
        extract_to.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(source, "r") as zf:
            zf.extractall(extract_to)
        # If zip contained a single top folder, use it
        children = [p for p in extract_to.iterdir()]
        if len(children) == 1 and children[0].is_dir():
            return children[0]
        return extract_to
    raise FileNotFoundError(f"Pairs source not found: {source}")


def import_pairs(
    source: Path,
    output_jsonl: Path,
    *,
    work_dir: Path | None = None,
) -> list[ImportedPair]:
    work = work_dir or output_jsonl.parent
    work.mkdir(parents=True, exist_ok=True)
    pairs_dir = ensure_pairs_dir(source, work)
    discovered = discover_pairs(pairs_dir)
    imported = [
        import_pair(pid, before, after, source=str(source))
        for pid, before, after in discovered
    ]
    output_jsonl.parent.mkdir(parents=True, exist_ok=True)
    with output_jsonl.open("w", encoding="utf-8") as fh:
        for item in imported:
            payload = {
                "pair_id": item.pair_id,
                "original_text": item.original_text,
                "corrected_text": item.corrected_text,
                "diff_spans": [asdict(s) for s in item.diff_spans],
                "source": item.source,
                "requires_human_classification": True,
                "before_path": item.before_path,
                "after_path": item.after_path,
            }
            fh.write(json.dumps(payload, ensure_ascii=False) + "\n")
    return imported
