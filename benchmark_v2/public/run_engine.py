"""Public-only thin wrapper around app.cli.run_benchmark (no private/ imports)."""

from __future__ import annotations

import sys
from pathlib import Path

from app.cli.run_benchmark import main as run_main


def main(argv: list[str] | None = None) -> int:
    # Translate legacy flags used by benchmark_v2 docs.
    args = list(argv) if argv is not None else sys.argv[1:]
    translated: list[str] = []
    i = 0
    while i < len(args):
        if args[i] == "--out" and i + 1 < len(args):
            translated.extend(["--output", args[i + 1]])
            i += 2
            continue
        if args[i] == "--run-id":
            # run_id is recorded in meta via generated_at; skip unknown flag value
            i += 2
            continue
        if args[i] == "--cases-dir" and i + 1 < len(args):
            translated.extend(["--cases", args[i + 1]])
            i += 2
            continue
        translated.append(args[i])
        i += 1

    if "--cases" not in translated:
        default_cases = Path(__file__).resolve().parents[1] / "public" / "cases"
        translated.extend(["--cases", str(default_cases)])
    if "--output" not in translated and "--out" not in args:
        default_out = Path(__file__).resolve().parents[1] / "results" / "engine_outputs.json"
        translated.extend(["--output", str(default_out)])
    return run_main(translated)


if __name__ == "__main__":
    raise SystemExit(main())
