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


def test_expert_label_artifact_complete_when_present():
    """If the expert pass has been run, all 163 rows must be decided."""
    path = ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3" / "expert_labels.jsonl"
    if not path.exists():
        return
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) == 163
    allowed = {"keep", "drop", "uncertain"}
    assert all(str(r.get("decision") or "").strip().lower() in allowed for r in rows)
    assert all(r["decision"] != "drop" or r.get("drop_reason") for r in rows)
    assert all((r.get("rationale") or r.get("editor_notes")) for r in rows)


def test_calibration_packet_selection_is_deterministic():
    labels = ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3" / "expert_labels.jsonl"
    if not labels.exists():
        return
    mod = _load(
        "build_calibration",
        ROOT / "scripts" / "build_editorial_calibration_packet.py",
    )
    rows = mod.load_rows(labels)
    first = mod.select_rows(rows)
    second = mod.select_rows(rows)
    assert [row["source_index"] for row in first] == [row["source_index"] for row in second]
    assert len(first) == 30
    assert sum(row["decision"] == "keep" for row in first) == 10
    assert sum(row["decision"] == "drop" for row in first) == 15
    assert sum(row["decision"] == "uncertain" for row in first) == 5
    categories = {row["category"] for row in first}
    assert {
        "attribution",
        "clarity",
        "headline_body_mismatch",
        "numeric_contradiction",
        "loaded_framing",
        "spelling",
        "entity_name",
    } <= categories


def test_consistency_audit_artifacts_when_present():
    base = ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3"
    audit = base / "label_consistency_audit.md"
    corrections = base / "proposed_label_corrections.jsonl"
    if not audit.exists() or not corrections.exists():
        return
    text = audit.read_text(encoding="utf-8")
    assert "163" in text
    rows = [json.loads(line) for line in corrections.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert rows
    assert all(row.get("status") == "proposed_only_not_applied" for row in rows)


def test_correction_adjudication_is_derived_and_complete():
    base = ROOT / "data" / "evaluation" / "analysis" / "editorial_labels_run3"
    proposals = base / "proposed_label_corrections.jsonl"
    expert = base / "expert_labels.jsonl"
    scoring = base / "labeled_for_scoring.jsonl"
    if not all(path.exists() for path in (proposals, expert, scoring)):
        return
    mod = _load(
        "adjudicate_corrections",
        ROOT / "scripts" / "adjudicate_editorial_corrections.py",
    )
    records, final_expert, final_scoring = mod.adjudicate(
        mod._read_jsonl(proposals),
        mod._read_jsonl(expert),
        mod._read_jsonl(scoring),
    )
    assert len(records) == 17
    assert sum(row["adjudication"] == "accept" for row in records) == 13
    assert sum(row["adjudication"] == "uncertain" for row in records) == 4
    assert sum(row["adjudication"] == "reject" for row in records) == 0
    assert len(final_expert) == len(final_scoring) == 163
    decisions = {row["source_index"]: row["decision"] for row in final_expert}
    assert decisions[128] == decisions[129] == "drop"
    assert decisions[47] == decisions[49] == "uncertain"
    assert decisions[50] == "keep"  # uncertain adjudication retains original


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
