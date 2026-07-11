from __future__ import annotations

import argparse
from pathlib import Path

from app.config import ROOT_DIR
from app.dataset.importer import import_pairs


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Import BEFORE/AFTER Arabic article pairs")
    parser.add_argument(
        "--source",
        type=Path,
        default=ROOT_DIR / "data" / "pairs",
        help="Directory of pairs or pairs.zip",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT_DIR / "data" / "imported" / "pairs.jsonl",
        help="Output JSONL path",
    )
    args = parser.parse_args(argv)
    imported = import_pairs(args.source, args.output)
    print(f"Imported {len(imported)} pairs -> {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
