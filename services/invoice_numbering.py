from __future__ import annotations

import datetime as dt

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.invoice import Invoice


def next_invoice_number(session: Session, *, today: dt.date | None = None) -> str:
    d = today or dt.date.today()
    prefix = f"INV-{d.year}-"

    # Expected format: INV-YYYY-0001
    # Find max numeric suffix within year.
    max_suffix = session.scalar(
        select(func.max(Invoice.invoice_no)).where(Invoice.invoice_no.like(f"{prefix}%"))
    )
    if not max_suffix:
        return f"{prefix}0001"

    try:
        last_num = int(str(max_suffix).split("-")[-1])
    except Exception:
        last_num = 0
    return f"{prefix}{last_num + 1:04d}"

