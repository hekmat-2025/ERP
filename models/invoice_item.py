from __future__ import annotations

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.base import Base


class InvoiceItem(Base):
    __tablename__ = "invoice_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    invoice_id: Mapped[int] = mapped_column(
        ForeignKey("invoices.id", ondelete="CASCADE"), nullable=False, index=True
    )
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=True)

    product_name: Mapped[str] = mapped_column(String(200), nullable=False, default="")
    hsn_code: Mapped[str] = mapped_column(String(50), nullable=False, default="")
    gst_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    quantity: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    amount: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)

    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product")

    def __repr__(self) -> str:
        return f"InvoiceItem(id={self.id!r}, product_name={self.product_name!r})"

