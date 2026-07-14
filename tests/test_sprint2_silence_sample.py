"""Sprint 2 — silence sample + contrastive scaffold tests."""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPRINT2 = ROOT / "data" / "evaluation" / "sprint2"


def _load_sampler():
    path = ROOT / "scripts" / "sample_silence_set.py"
    spec = importlib.util.spec_from_file_location("sample_silence_set", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_risk_tags_and_length_bucket():
    mod = _load_sampler()
    tags = mod.risk_tags("الجيش يعلن السيطرة", 'قال المتحدث: «تم الأمر» بحسب مصادر.')
    assert "has_quote" in tags
    assert "has_attribution" in tags
    assert "has_masadir" in tags
    assert mod.length_bucket(100) == "short"
    assert mod.length_bucket(800) == "medium"
    assert mod.length_bucket(2000) == "long"


def test_stratified_sample_respects_n_and_seed():
    mod = _load_sampler()
    rows = []
    for i in range(40):
        corpus = "sanad" if i % 2 == 0 else "anad"
        body = ("نص تجريبي. " * (5 + (i % 30))).strip()
        rows.append(
            {
                "record_id": f"{corpus.upper()}-{i:04d}",
                "headline": "عنوان",
                "body": body,
                "metadata": {
                    "corpus": corpus,
                    "length_bucket": mod.length_bucket(len(body)),
                    "risk_tags": mod.risk_tags("عنوان", body) or ["plain"],
                },
            }
        )
    a = mod.stratified_sample(rows, n=12, seed=7)
    b = mod.stratified_sample(rows, n=12, seed=7)
    assert len(a) == 12
    assert [r["record_id"] for r in a] == [r["record_id"] for r in b]
    assert len({r["record_id"] for r in a}) == 12


def test_contrastives_pairs_balanced():
    path = SPRINT2 / "contrastives_v1.jsonl"
    assert path.exists()
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(rows) >= 8
    by_pair: dict[str, list] = {}
    for row in rows:
        by_pair.setdefault(row["pair_id"], []).append(row)
    for pair_id, pair_rows in by_pair.items():
        actions = {r["expected_action"] for r in pair_rows}
        assert actions == {"show", "silence"}, pair_id
        fires = {r["should_fire"] for r in pair_rows}
        assert fires == {True, False}, pair_id


def test_fp_label_template_has_annotator_fields():
    path = SPRINT2 / "fp_labels_template.jsonl"
    row = json.loads(path.read_text(encoding="utf-8").splitlines()[0])
    assert row["annotator_decision"] in {"keep", "drop", "modify"}
    assert "drop_reason" in row
