"""Guards: public runner must never touch gold."""

from __future__ import annotations

import inspect
import json
from pathlib import Path

from app.cli import run_benchmark
from benchmark_v2.public import run_engine


def test_run_benchmark_refuses_private_paths():
    source = inspect.getsource(run_benchmark)
    assert "FORBIDDEN_CASE_KEYS" in source
    assert "_assert_public_cases_dir" in source
    assert "load_gold" not in source
    assert "expected_findings" in source  # only as forbidden key names to reject


def test_public_wrapper_delegates_without_gold_imports():
    source = inspect.getsource(run_engine)
    assert "private.gold" not in source
    assert "private.scorer" not in source
    assert "run_benchmark" in source


def test_public_cases_contain_only_inputs():
    cases_dir = Path(__file__).resolve().parents[1] / "benchmark_v2" / "public" / "cases"
    sample = next(cases_dir.glob("case-*.json"))
    raw = json.loads(sample.read_text(encoding="utf-8"))
    assert "case_id" in raw
    assert "expected_findings" not in raw
    assert "forbidden_findings" not in raw
