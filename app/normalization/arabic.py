from dataclasses import dataclass

import regex as re

# Arabic diacritics / tashkeel
_DIACRITICS = re.compile(r"[\u0610-\u061A\u064B-\u065F\u0670\u06D6-\u06ED]")
_TATWEEL = re.compile(r"\u0640")
_WHITESPACE = re.compile(r"\s+")
_ALEF_VARIANTS = str.maketrans(
    {
        "أ": "ا",
        "إ": "ا",
        "آ": "ا",
        "ٱ": "ا",
    }
)
_DIGIT_MAP = str.maketrans("٠١٢٣٤٥٦٧٨٩۰۱۲۳۴۵۶۷۸۹", "01234567890123456789")
_PUNCT_NORMALIZE = str.maketrans(
    {
        "،": ",",
        "؛": ";",
        "؟": "?",
        "«": '"',
        "»": '"',
        "“": '"',
        "”": '"',
        "‘": "'",
        "’": "'",
    }
)


@dataclass(frozen=True)
class NormalizationConfig:
    remove_diacritics: bool = True
    remove_tatweel: bool = True
    normalize_alef: bool = True
    normalize_alef_maksura: bool = True
    normalize_whitespace: bool = True
    normalize_punctuation: bool = True
    normalize_digits: bool = True
    fuzzy_taa_marbuta: bool = False


DEFAULT_CONFIG = NormalizationConfig()


def normalize_arabic(text: str, config: NormalizationConfig | None = None) -> str:
    """Return a matching-only normalized form. Never mutate source text in place."""
    cfg = config or DEFAULT_CONFIG
    result = text

    if cfg.remove_diacritics:
        result = _DIACRITICS.sub("", result)
    if cfg.remove_tatweel:
        result = _TATWEEL.sub("", result)
    if cfg.normalize_alef:
        result = result.translate(_ALEF_VARIANTS)
    if cfg.normalize_alef_maksura:
        result = result.replace("ى", "ي")
    if cfg.normalize_digits:
        result = result.translate(_DIGIT_MAP)
    if cfg.normalize_punctuation:
        result = result.translate(_PUNCT_NORMALIZE)
    if cfg.fuzzy_taa_marbuta:
        result = result.replace("ة", "ه")
    if cfg.normalize_whitespace:
        result = _WHITESPACE.sub(" ", result).strip()

    return result
