"""Tests for editorial label validation / scoring helpers (no GCP)."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_validate_blank_is_unlabeled_not_error():
    mod = _load("validate_labels", ROOT / "scripts" / "validate_editorial_label_file.py")
    rows = [
        {
            "article_id": "A1",
            "segment_id": "S1",
            "finding_id": "F1",
            "category": "attribution",
            "decision": None,
            "drop_reason": None,
        }
    ]
    report = mod.validate_rows(rows)
    assert report["ok"] is True
    assert report["blank_decision"] == 1
    assert report["unlabeled_rows"] == 1


def test_validate_drop_requires_reason():
    mod = _load("validate_labels", ROOT / "scripts" / "validate_editorial_label_file.py")
    rows = [
        {
            "article_id": "A1",
            "segment_id": "S1",
            "finding_id": "F1",
            "category": "clarity",
            "decision": "drop",
            "drop_reason": None,
        }
    ]
    report = mod.validate_rows(rows)
    assert report["ok"] is False
    assert any(e["error"] == "drop_requires_drop_reason" for e in report["validation_errors"])


def test_score_precision_excludes_uncertain(tmp_path: Path):
    mod = _load("score_labels", ROOT / "scripts" / "score_editorial_labels.py")
    path = tmp_path / "labels.jsonl"
    rows = [
        {
            "article_id": "A",
            "finding_id": "1",
            "category": "attribution",
            "severity": "high",
            "decision": "keep",
            "drop_reason": None,
            "original_text": "x",
            "explanation_ar": "y",
        },
        {
            "article_id": "A",
            "finding_id": "2",
            "category": "attribution",
            "severity": "high",
            "decision": "drop",
            "drop_reason": "context_resolves_issue",
            "original_text": "x",
            "explanation_ar": "y",
        },
        {
            "article_id": "B",
            "finding_id": "3",
            "category": "clarity",
            "severity": "low",
            "decision": "uncertain",
            "drop_reason": None,
            "original_text": "x",
            "explanation_ar": "y",
        },
    ]
    path.write_text("\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n", encoding="utf-8")
    out = tmp_path / "out"
    rc = mod.main(["--input", str(path), "--out-dir", str(out)])
    assert rc == 0
    summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
    assert summary["keep_count"] == 1
    assert summary["drop_count"] == 1
    assert summary["uncertain_count"] == 1
    assert summary["precision_overall"] == 0.5
    assert (out / "category_precision.csv").exists()
    assert (out / "drop_reasons.csv").exists()
    assert (out / "labeled_findings.csv").exists()


def test_compare_requires_candidate(tmp_path: Path):
    mod = _load("compare_runs", ROOT / "scripts" / "compare_evaluation_runs.py")
    base = ROOT / "data" / "evaluation" / "runs" / "gemini_run3"
    missing = tmp_path / "missing_run"
    try:
        mod.main(
            [
                "--baseline",
                str(base),
                "--candidate",
                str(missing),
                "--output",
                str(tmp_path / "cmp"),
            ]
        )
        assert False, "expected SystemExit"
    except SystemExit as exc:
        assert "Missing candidate" in str(exc)
