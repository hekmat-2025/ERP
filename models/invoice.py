from __future__ import annotations

import datetime as dt

from sqlalchemy import Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class Invoice(Base):
    __tablename__ = "invoices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_no: Mapped[str] = mapped_column(String(30), nullable=False, unique=True, index=True)
    invoice_date: Mapped[dt.date] = mapped_column(Date, nullable=False, default=dt.date.today)

    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False)
    customer = relationship("Customer")

    gross_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    tax_amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    grand_total: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    notes: Mapped[str] = mapped_column(String(500), nullable=False, default="")

    items = relationship(
        "InvoiceItem",
        back_populates="invoice",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:
        return f"Invoice(id={self.id!r}, invoice_no={self.invoice_no!r})"

