#!/usr/bin/env python3
"""Sprint 2: stratified silence subsample from SANAD/ANAD clean corpora.

Public corpora = expected silence (or near-silence). Subsample for daily FP
benchmarks; keep full dumps in GCS / data/local.

Streams JSONL and keeps a bounded reservoir per stratum (no full-corpus RAM load).

Usage:
  python scripts/sample_silence_set.py --n 300
  python scripts/sample_silence_set.py --n 300 --sources sanad --seed 42
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_ATTR_RE = re.compile(
    r"قال|قالت|أكد|أكدت|أعلن|أعلنت|بحسب|وفقاً|وفقا|نقلاً|نقلا|صرح|صرحت|أفاد|أفادت"
)
_QUOTE_RE = re.compile(r"[«»\"“”‘’']")
_MASADIR_RE = re.compile(r"مصادر(?:\s+\S+){0,3}")
_DEFAULT_SOURCES = {
    "sanad": ROOT / "data" / "local" / "public_corpora" / "sanad_clean_v1.jsonl",
    "anad": ROOT / "data" / "local" / "public_corpora" / "anad_clean_v1.jsonl",
}


def length_bucket(n: int) -> str:
    if n < 400:
        return "short"
    if n < 1200:
        return "medium"
    return "long"


def risk_tags(headline: str, body: str) -> list[str]:
    text = f"{headline}\n{body}"
    tags: list[str] = []
    if _QUOTE_RE.search(text):
        tags.append("has_quote")
    if _ATTR_RE.search(text):
        tags.append("has_attribution")
    if _MASADIR_RE.search(text):
        tags.append("has_masadir")
    if headline and _ATTR_RE.search(headline):
        tags.append("headline_attribution")
    if not tags:
        tags.append("plain")
    return tags


def _iter_jsonl(path: Path):
    with path.open("r", encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _normalize_row(raw: dict, corpus: str) -> dict | None:
    body = (raw.get("body") or "").strip()
    if len(body) < 80:
        return None
    headline = (raw.get("headline") or "").strip()
    record_id = raw.get("record_id") or f"{corpus.upper()}-UNKNOWN"
    tags = risk_tags(headline, body)
    return {
        "record_id": record_id,
        "language": raw.get("language", "ar"),
        "source_type": "external_public",
        "headline": headline,
        "body": body,
        "expected_findings": [],
        "expected_issues": [],
        "reason": "acceptable_published_copy",
        "license": raw.get("license") or "CC-BY-4.0",
        "notes": raw.get("notes")
        or "Public corpus silence sample — not Al Jazeera house-style data",
        "metadata": {
            **(raw.get("metadata") or {}),
            "corpus": corpus,
            "length_bucket": length_bucket(len(body)),
            "risk_tags": tags,
            "sprint": "sprint2_silence",
        },
    }


def stratum_key(row: dict) -> tuple[str, str, str]:
    meta = row["metadata"]
    return (meta["corpus"], meta["length_bucket"], meta["risk_tags"][0])


def reservoir_fill(
    paths: dict[str, Path],
    *,
    per_stratum: int,
    seed: int,
    max_scan: int | None,
) -> dict[tuple[str, str, str], list[dict]]:
    """One-pass reservoir sample per stratum."""
    rng = random.Random(seed)
    reservoirs: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    seen_counts: dict[tuple[str, str, str], int] = defaultdict(int)

    for corpus, path in paths.items():
        if not path.exists():
            print(f"skip missing corpus={corpus} path={path}", flush=True)
            continue
        scanned = 0
        kept = 0
        for raw in _iter_jsonl(path):
            scanned += 1
            if max_scan is not None and scanned > max_scan:
                break
            row = _normalize_row(raw, corpus)
            if row is None:
                continue
            key = stratum_key(row)
            seen_counts[key] += 1
            count = seen_counts[key]
            bucket = reservoirs[key]
            if len(bucket) < per_stratum:
                bucket.append(row)
                kept += 1
            else:
                j = rng.randrange(count)
                if j < per_stratum:
                    bucket[j] = row
                    kept += 1
            if scanned % 50000 == 0:
                print(f"  {corpus}: scanned={scanned}", flush=True)
        print(
            f"loaded corpus={corpus} scanned={scanned} strata={len(reservoirs)}",
            flush=True,
        )
    return reservoirs


def stratified_pick(
    reservoirs: dict[tuple[str, str, str], list[dict]],
    *,
    n: int,
    seed: int,
) -> list[dict]:
    rng = random.Random(seed + 1)
    keys = sorted(reservoirs.keys())
    pools = {k: list(v) for k, v in reservoirs.items()}
    for bucket in pools.values():
        rng.shuffle(bucket)

    picked: list[dict] = []
    seen: set[str] = set()
    while len(picked) < n:
        progressed = False
        for key in keys:
            bucket = pools[key]
            while bucket:
                row = bucket.pop()
                rid = row["record_id"]
                if rid in seen:
                    continue
                seen.add(rid)
                picked.append(row)
                progressed = True
                break
            if len(picked) >= n:
                break
        if not progressed:
            break
    picked.sort(key=lambda r: r["record_id"])
    return picked[:n]


def stratified_sample(rows: list[dict], *, n: int, seed: int) -> list[dict]:
    """In-memory helper for unit tests."""
    reservoirs: dict[tuple[str, str, str], list[dict]] = defaultdict(list)
    for row in rows:
        reservoirs[stratum_key(row)].append(row)
    return stratified_pick(reservoirs, n=n, seed=seed)


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for row in rows:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sample silence set for Sprint 2")
    parser.add_argument("--n", type=int, default=300, help="Target sample size (200–500)")
    parser.add_argument("--seed", type=int, default=20260714)
    parser.add_argument(
        "--sources",
        nargs="+",
        default=["sanad", "anad"],
        choices=sorted(_DEFAULT_SOURCES.keys()),
    )
    parser.add_argument(
        "--max-scan-per-corpus",
        type=int,
        default=None,
        help="Optional cap while scanning each corpus (smoke tests)",
    )
    parser.add_argument(
        "--per-stratum",
        type=int,
        default=40,
        help="Reservoir size per stratum before final pick",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "local" / "sprint2" / "silence_v1.jsonl",
    )
    parser.add_argument(
        "--seed-out",
        type=Path,
        default=ROOT / "data" / "evaluation" / "sprint2" / "silence_seed.jsonl",
        help="Tiny git-tracked slice for smoke tests",
    )
    parser.add_argument("--seed-n", type=int, default=20)
    args = parser.parse_args(argv)

    if not 50 <= args.n <= 2000:
        raise SystemExit("--n should be between 50 and 2000 (Sprint 2 target: 200–500)")

    paths = {name: _DEFAULT_SOURCES[name] for name in args.sources}
    reservoirs = reservoir_fill(
        paths,
        per_stratum=args.per_stratum,
        seed=args.seed,
        max_scan=args.max_scan_per_corpus,
    )
    sample = stratified_pick(reservoirs, n=args.n, seed=args.seed)
    write_jsonl(args.out, sample)

    seed_slice = sample[: min(args.seed_n, len(sample))]
    write_jsonl(args.seed_out, seed_slice)

    by_corpus: dict[str, int] = defaultdict(int)
    by_tag: dict[str, int] = defaultdict(int)
    for row in sample:
        by_corpus[row["metadata"]["corpus"]] += 1
        for tag in row["metadata"]["risk_tags"]:
            by_tag[tag] += 1

    print(
        json.dumps(
            {
                "wrote": str(args.out),
                "seed_slice": str(args.seed_out),
                "n": len(sample),
                "strata": len(reservoirs),
                "by_corpus": dict(by_corpus),
                "by_risk_tag": dict(by_tag),
                "seed": args.seed,
            },
            ensure_ascii=False,
            indent=2,
        ),
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
