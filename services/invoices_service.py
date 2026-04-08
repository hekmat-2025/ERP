from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from sqlalchemy.orm import Session

from models.customer import Customer
from models.invoice import Invoice
from models.invoice_item import InvoiceItem
from models.product import Product
from services.validation import ValidationError, require_non_empty, require_non_negative_number, require_positive_number

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class InvoiceItemDraft:
    product_id: int | None
    product_name: str
    hsn_code: str
    gst_rate: float
    rate: float
    quantity: float


@dataclass(frozen=True)
class CreateInvoiceRequest:
    invoice_no: str
    invoice_date: dt.date
    customer_id: int
    tax_enabled: bool
    items: list[InvoiceItemDraft]
    notes: str = ""


@dataclass(frozen=True)
class CreateInvoiceResult:
    invoice_id: int
    invoice_no: str
    gross_amount: float
    tax_amount: float
    grand_total: float


class InvoicesService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def get_invoice(self, invoice_id: int) -> Invoice | None:
        stmt = (
            select(Invoice)
            .where(Invoice.id == invoice_id)
            .options(selectinload(Invoice.items), selectinload(Invoice.customer))
        )
        return self._session.scalar(stmt)

    def create_invoice(self, req: CreateInvoiceRequest) -> CreateInvoiceResult:
        invoice_no = require_non_empty(req.invoice_no, "Invoice number")
        if not isinstance(req.invoice_date, dt.date):
            raise ValidationError("Invoice date is required.")

        customer = self._session.get(Customer, req.customer_id)
        if not customer:
            raise ValidationError("Customer is required.")

        clean_items: list[InvoiceItem] = []
        gross = 0.0
        tax = 0.0

        if not req.items:
            raise ValidationError("At least one invoice item is required.")

        for idx, d in enumerate(req.items, start=1):
            name = (d.product_name or "").strip()
            if not name:
                raise ValidationError(f"Row {idx}: Product is required.")

            qty = require_positive_number(d.quantity, f"Row {idx}: Quantity")
            rate = require_non_negative_number(d.rate, f"Row {idx}: Rate")
            gst_rate = require_non_negative_number(d.gst_rate, f"Row {idx}: GST rate")

            amount = qty * rate
            gross += amount
            if req.tax_enabled:
                tax += amount * (gst_rate / 100.0)

            clean_items.append(
                InvoiceItem(
                    product_id=d.product_id,
                    product_name=name,
                    hsn_code=(d.hsn_code or "").strip(),
                    gst_rate=gst_rate,
                    rate=rate,
                    quantity=qty,
                    amount=amount,
                )
            )

        grand = gross + tax

        inv = Invoice(
            invoice_no=invoice_no,
            invoice_date=req.invoice_date,
            customer_id=customer.id,
            gross_amount=gross,
            tax_amount=tax,
            grand_total=grand,
            notes=(req.notes or "").strip(),
            items=clean_items,
        )

        self._session.add(inv)
        self._session.commit()
        logger.info("Created invoice id=%s invoice_no=%s items=%s", inv.id, inv.invoice_no, len(clean_items))

        return CreateInvoiceResult(
            invoice_id=inv.id,
            invoice_no=inv.invoice_no,
            gross_amount=gross,
            tax_amount=tax,
            grand_total=grand,
        )

    def product_by_id(self, product_id: int) -> Product | None:
        return self._session.get(Product, product_id)

