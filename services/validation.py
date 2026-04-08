from __future__ import annotations


class ValidationError(ValueError):
    pass


def require_non_empty(value: str, field_name: str) -> str:
    v = (value or "").strip()
    if not v:
        raise ValidationError(f"{field_name} is required.")
    return v


def require_positive_number(value: float, field_name: str) -> float:
    try:
        v = float(value)
    except Exception as e:  # noqa: BLE001
        raise ValidationError(f"{field_name} must be a number.") from e
    if v <= 0:
        raise ValidationError(f"{field_name} must be > 0.")
    return v


def require_non_negative_number(value: float, field_name: str) -> float:
    try:
        v = float(value)
    except Exception as e:  # noqa: BLE001
        raise ValidationError(f"{field_name} must be a number.") from e
    if v < 0:
        raise ValidationError(f"{field_name} must be >= 0.")
    return v

