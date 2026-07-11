"""CLI entrypoint: python benchmark_v2/private/scorer/scorer.py ..."""

from __future__ import annotations

import sys
from pathlib import Path

# Allow running as a script from repo root without install.
_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from benchmark_v2.private.scorer.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
