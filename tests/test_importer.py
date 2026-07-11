from pathlib import Path

from app.dataset.importer import discover_pairs, import_pairs, strip_html

FIXTURES = Path(__file__).resolve().parent / "fixtures" / "pairs"


def test_strip_html_preserves_arabic():
    html = "<p dir='rtl'>مرحبا <strong>بالعالم</strong></p>"
    text = strip_html(html)
    assert "مرحبا" in text
    assert "بالعالم" in text
    assert "<" not in text


def test_discover_and_import_pairs(tmp_path: Path):
    pairs = discover_pairs(FIXTURES)
    assert len(pairs) == 1
    out = tmp_path / "pairs.jsonl"
    imported = import_pairs(FIXTURES, out)
    assert len(imported) == 1
    item = imported[0]
    assert item.requires_human_classification is True
    assert item.original_text
    assert item.corrected_text
    assert any(s.op in {"replace", "insert", "delete"} for s in item.diff_spans)
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1
    assert "requires_human_classification" in lines[0]
