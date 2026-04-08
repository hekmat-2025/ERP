from __future__ import annotations


_ARABIC_INDIC = str.maketrans("٠١٢٣٤٥٦٧٨٩", "0123456789")
_EASTERN_ARABIC_INDIC = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")


def to_english_digits(text: str) -> str:
    if not text:
        return text
    return text.translate(_ARABIC_INDIC).translate(_EASTERN_ARABIC_INDIC)

