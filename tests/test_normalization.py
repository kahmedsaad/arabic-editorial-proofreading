from app.normalization.arabic import NormalizationConfig, normalize_arabic


def test_preserves_source_semantics_via_copy():
    original = "إِنَّ الْيَوْمَ — اختبارٌ"
    normalized = normalize_arabic(original)
    assert original.startswith("إ")
    assert "ا" in normalized
    assert "َ" not in normalized


def test_alef_and_alef_maksura():
    assert normalize_arabic("أحمد على") == normalize_arabic("احمد علي")


def test_digits_and_tatweel():
    text = "عام ٢٠٢٤ــــ"
    assert normalize_arabic(text) == "عام 2024"


def test_fuzzy_taa_optional():
    base = normalize_arabic("مدرسة")
    fuzzy = normalize_arabic("مدرسة", NormalizationConfig(fuzzy_taa_marbuta=True))
    assert base.endswith("ة")
    assert fuzzy.endswith("ه")
