"""Download licensed public Arabic news corpora → JSONL (local and/or GCS).

Supported (verify licences before redistribution):
- SANAD (CC BY 4.0) — AlKhaleej / AlArabiya / Akhbarona — NOT Al Jazeera
- ANAD (CC BY 4.0) — 2021 multi-site news — excludes any Al Jazeera rows if present

External corpora are for silence/structure evaluation only.
They are NOT Al Jazeera house-style policy.

Al Jazeera live scraping is intentionally unsupported here.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Sources we never treat as AJ house style; also drop AJ if it appears in a public dump
_AJ_NAME_RE = re.compile(r"al[\s_-]?jazeera|الجزيرة", re.IGNORECASE)


def _is_aljazeera_source(value: str | None) -> bool:
    if not value:
        return False
    return bool(_AJ_NAME_RE.search(str(value)))


def _write_jsonl(path: Path, rows: list[dict]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    return len(rows)


def pull_sanad(*, out_dir: Path, max_records: int | None) -> Path:
    """Pull SANAD via Hugging Face datasets (arbml/SANAD)."""
    try:
        from datasets import load_dataset  # type: ignore
    except ImportError as exc:
        raise SystemExit(
            "Install datasets: pip install datasets pyarrow\n" + str(exc)
        ) from exc

    print("Loading arbml/SANAD from Hugging Face...", flush=True)
    ds = load_dataset("arbml/SANAD", split="train")
    rows: list[dict] = []
    skipped_aj = 0
    for i, item in enumerate(ds):
        if max_records is not None and len(rows) >= max_records:
            break
        # Common field names across SANAD mirrors
        text = (
            item.get("Article")
            or item.get("article")
            or item.get("text")
            or item.get("content")
            or item.get("body")
            or ""
        )
        title = item.get("title") or item.get("headline") or ""
        label = item.get("label") or item.get("category") or ""
        source = str(item.get("source") or item.get("newspaper") or "sanad")
        if isinstance(text, str):
            body = text.strip()
        else:
            body = str(text).strip()
        if not body:
            continue
        # SANAD often has no separate headline — use first sentence as soft headline
        if not title:
            first = body.split(".", 1)[0].strip()
            title = (first[:160] + "…") if len(first) > 160 else first
        if _is_aljazeera_source(source):
            skipped_aj += 1
            continue
        rows.append(
            {
                "record_id": f"SANAD-{i:06d}",
                "language": "ar",
                "source_type": "external_public",
                "headline": title if isinstance(title, str) else str(title),
                "body": body,
                "expected_findings": [],
                "reason": "acceptable_published_copy",
                "license": "CC-BY-4.0",
                "notes": (
                    "SANAD public corpus — not Al Jazeera house-style data. "
                    f"category={label}; origin_source={source}"
                ),
                "metadata": {
                    "corpus": "SANAD",
                    "category": label,
                    "origin_source": source,
                    "hf_dataset": "arbml/SANAD",
                },
            }
        )
        if (len(rows) % 10000) == 0 and rows:
            print(f"  ... {len(rows)} records", flush=True)

    out = out_dir / "sanad_clean_v1.jsonl"
    n = _write_jsonl(out, rows)
    print(f"Wrote {n} records -> {out} (skipped_aj={skipped_aj})", flush=True)
    return out


def _iter_anad_text_files(anad_root: Path | None, anad_zip: Path | None):
    """Yield (rel_path, text) from a directory tree or zip (Windows-safe)."""
    if anad_zip is not None:
        import zipfile

        with zipfile.ZipFile(anad_zip) as zf:
            for info in zf.infolist():
                if info.is_dir():
                    continue
                name = info.filename.replace("\\", "/")
                # skip AJ and non-text
                if _is_aljazeera_source(name):
                    continue
                lower = name.lower()
                if not (lower.endswith(".txt") or lower.endswith(".text") or lower.endswith(".md")):
                    continue
                try:
                    raw = zf.read(info)
                    text = raw.decode("utf-8", errors="replace").strip()
                except Exception:  # noqa: BLE001
                    continue
                yield name, text
        return

    assert anad_root is not None
    for path in sorted(anad_root.rglob("*")):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".txt", ".text", ".md", ""}:
            continue
        if path.name.startswith("."):
            continue
        rel = path.relative_to(anad_root).as_posix()
        if _is_aljazeera_source(rel):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            continue
        yield rel, text


def pull_anad(
    *,
    out_dir: Path,
    max_records: int | None,
    anad_root: Path | None,
    anad_zip: Path | None = None,
) -> Path:
    """
    Convert ANAD (directory or zip) to JSONL.

    On Windows, prefer --anad-zip: git clone fails on paths containing ':'.
    """
    if (anad_root is None or not anad_root.exists()) and (
        anad_zip is None or not anad_zip.exists()
    ):
        raise SystemExit(
            "ANAD requires --anad-root or --anad-zip.\n"
            "Windows example:\n"
            "  curl -L -o data/local/anad_main.zip "
            "https://github.com/alaybaa/ArabicArticlesDataset/archive/refs/heads/main.zip\n"
            "  python scripts/pull_public_corpora.py --corpus anad "
            "--anad-zip data/local/anad_main.zip"
        )

    rows: list[dict] = []
    skipped_aj = 0
    for rel, body in _iter_anad_text_files(anad_root, anad_zip):
        if max_records is not None and len(rows) >= max_records:
            break
        if _is_aljazeera_source(rel):
            skipped_aj += 1
            continue
        if len(body) < 40:
            continue
        lines = [ln.strip() for ln in body.splitlines() if ln.strip()]
        headline = lines[0][:180] if lines and len(lines[0]) < 180 else ""
        article_body = "\n".join(lines[1:] if headline else lines)
        parts = rel.replace("\\", "/").split("/")
        category = parts[-2] if len(parts) >= 2 else "unknown"
        site = parts[-3] if len(parts) >= 3 else "anad"
        # normalize illegal windows site folder names for metadata only
        site = site.replace(":", "_")
        if _is_aljazeera_source(site):
            skipped_aj += 1
            continue
        rows.append(
            {
                "record_id": f"ANAD-{len(rows):06d}",
                "language": "ar",
                "source_type": "external_public",
                "headline": headline,
                "body": article_body or body,
                "expected_findings": [],
                "reason": "acceptable_published_copy",
                "license": "CC-BY-4.0",
                "notes": (
                    "ANAD public corpus — not Al Jazeera house-style data. "
                    f"site={site}; category={category}"
                ),
                "metadata": {
                    "corpus": "ANAD",
                    "site": site,
                    "category": category,
                    "rel_path": rel.replace(":", "_"),
                },
            }
        )
        if (len(rows) % 10000) == 0 and rows:
            print(f"  ... {len(rows)} records", flush=True)

    out = out_dir / "anad_clean_v1.jsonl"
    n = _write_jsonl(out, rows)
    print(f"Wrote {n} records -> {out} (skipped_aj={skipped_aj})", flush=True)
    return out


def _upload_gcs(local: Path, dest_key: str, dataset_id: str) -> None:
    from app.cli.upload_dataset import main as upload_main

    code = upload_main(
        [
            "--source",
            str(local),
            "--destination",
            dest_key,
            "--dataset-id",
            dataset_id,
            "--source-type",
            "external_public",
            "--license",
            "CC-BY-4.0",
            "--notes",
            "Public licensed corpus — not Al Jazeera house-style data",
            "--backend",
            "gcs",
            "--yes",
            "--overwrite",
        ]
    )
    if code != 0:
        # Fallback: gcloud storage cp
        import subprocess

        bucket = "arabic-proofreading-data-ooredoo-499510"
        uri = f"gs://{bucket}/{dest_key}"
        print(f"Python GCS upload failed ({code}); trying gcloud storage cp → {uri}")
        subprocess.check_call(
            ["gcloud", "storage", "cp", str(local), uri, "--project=ooredoo-499510"]
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--corpus",
        choices=["sanad", "anad", "all"],
        default="sanad",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("data/local/public_corpora"),
    )
    parser.add_argument(
        "--max-records",
        type=int,
        default=None,
        help="Optional cap for smoke tests (omit for full pull)",
    )
    parser.add_argument("--anad-root", type=Path, default=None)
    parser.add_argument(
        "--anad-zip",
        type=Path,
        default=None,
        help="ANAD zip (Windows-safe; reads members without illegal ':' paths on disk)",
    )
    parser.add_argument(
        "--upload-gcs",
        action="store_true",
        help="Upload resulting JSONL to GCS public/clean/",
    )
    parser.add_argument(
        "--allow-aljazeera-scrape",
        action="store_true",
        help="Rejected on purpose — see docs/PUBLIC_CORPORA.md",
    )
    args = parser.parse_args(argv)

    if args.allow_aljazeera_scrape:
        print(
            "Refused: Al Jazeera scraping (especially with proxies) is not implemented.\n"
            "Use licensed public corpora, or obtain written AJ permission for an allowlisted pack.\n"
            "See docs/PUBLIC_CORPORA.md",
            file=sys.stderr,
        )
        return 2

    args.out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).isoformat()
    print(f"[{stamp}] corpus={args.corpus} max_records={args.max_records}")

    outputs: list[tuple[str, Path]] = []
    if args.corpus in {"sanad", "all"}:
        outputs.append(
            ("sanad_clean_v1", pull_sanad(out_dir=args.out_dir, max_records=args.max_records))
        )
    if args.corpus in {"anad", "all"}:
        outputs.append(
            (
                "anad_clean_v1",
                pull_anad(
                    out_dir=args.out_dir,
                    max_records=args.max_records,
                    anad_root=args.anad_root,
                    anad_zip=args.anad_zip,
                ),
            )
        )

    if args.upload_gcs:
        for dataset_id, path in outputs:
            dest = f"public/clean/{dataset_id}/{path.name}"
            print(f"Uploading {path} → {dest}")
            _upload_gcs(path, dest, dataset_id)

    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
