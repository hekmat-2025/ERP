from __future__ import annotations

from dataclasses import dataclass


_ONES = [
    "zero",
    "one",
    "two",
    "three",
    "four",
    "five",
    "six",
    "seven",
    "eight",
    "nine",
    "ten",
    "eleven",
    "twelve",
    "thirteen",
    "fourteen",
    "fifteen",
    "sixteen",
    "seventeen",
    "eighteen",
    "nineteen",
]

_TENS = [
    "",
    "",
    "twenty",
    "thirty",
    "forty",
    "fifty",
    "sixty",
    "seventy",
    "eighty",
    "ninety",
]


def _words_lt_100(n: int) -> str:
    if n < 20:
        return _ONES[n]
    tens, ones = divmod(n, 10)
    if ones == 0:
        return _TENS[tens]
    return f"{_TENS[tens]} {_ONES[ones]}"


def _words_lt_1000(n: int) -> str:
    hundreds, rest = divmod(n, 100)
    parts: list[str] = []
    if hundreds:
        parts.append(f"{_ONES[hundreds]} hundred")
    if rest:
        parts.append(_words_lt_100(rest))
    return " ".join(parts) if parts else _ONES[0]


def int_to_words(n: int) -> str:
    if n == 0:
        return _ONES[0]
    if n < 0:
        return "minus " + int_to_words(-n)

    parts: list[str] = []
    billions, rem = divmod(n, 1_000_000_000)
    millions, rem = divmod(rem, 1_000_000)
    thousands, rem = divmod(rem, 1000)

    if billions:
        parts.append(f"{_words_lt_1000(billions)} billion")
    if millions:
        parts.append(f"{_words_lt_1000(millions)} million")
    if thousands:
        parts.append(f"{_words_lt_1000(thousands)} thousand")
    if rem:
        parts.append(_words_lt_1000(rem))

    return " ".join(parts)


@dataclass(frozen=True)
class MoneyWords:
    major: str
    minor: str


def currency_units(currency_code: str) -> MoneyWords:
    code = (currency_code or "").strip().upper()
    if code == "AFN":
        return MoneyWords(major="afghani", minor="pul")
    if code == "USD":
        return MoneyWords(major="dollars", minor="cents")
    # Fallback
    return MoneyWords(major="units", minor="cents")


def amount_to_words(amount: float, *, major_unit: str = "rupees", minor_unit: str = "paisa") -> str:
    """
    Lightweight amount-in-words helper for invoices.
    Works well for positive amounts; rounds to 2 decimals.
    """
    a = round(float(amount), 2)
    major = int(a)
    minor = int(round((a - major) * 100))

    major_words = int_to_words(major)
    if minor:
        minor_words = int_to_words(minor)
        return f"{major_words} {major_unit} and {minor_words} {minor_unit} only"
    return f"{major_words} {major_unit} only"

