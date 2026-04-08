from __future__ import annotations

import datetime as dt

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from models.customer import Customer
from models.invoice import Invoice
from models.invoice_item import InvoiceItem
from models.product import Product


class ReportsService:
    def __init__(self, session: Session) -> None:
        self._session = session

    def invoice_history(self, *, start: dt.date | None = None, end: dt.date | None = None) -> pd.DataFrame:
        stmt = (
            select(
                Invoice.id.label("invoice_id"),
                Invoice.invoice_no.label("invoice_no"),
                Invoice.invoice_date.label("date"),
                Customer.name.label("customer"),
                Invoice.gross_amount.label("gross"),
                Invoice.tax_amount.label("tax"),
                Invoice.grand_total.label("grand_total"),
            )
            .join(Customer, Customer.id == Invoice.customer_id)
            .order_by(Invoice.invoice_date.desc(), Invoice.id.desc())
        )
        if start:
            stmt = stmt.where(Invoice.invoice_date >= start)
        if end:
            stmt = stmt.where(Invoice.invoice_date <= end)

        rows = self._session.execute(stmt).mappings().all()
        return pd.DataFrame(rows)

    def sales_by_day(self, *, start: dt.date | None = None, end: dt.date | None = None) -> pd.DataFrame:
        stmt = (
            select(
                Invoice.invoice_date.label("date"),
                func.sum(Invoice.gross_amount).label("gross"),
                func.sum(Invoice.tax_amount).label("tax"),
                func.sum(Invoice.grand_total).label("grand_total"),
                func.count(Invoice.id).label("invoice_count"),
            )
            .group_by(Invoice.invoice_date)
            .order_by(Invoice.invoice_date.desc())
        )
        if start:
            stmt = stmt.where(Invoice.invoice_date >= start)
        if end:
            stmt = stmt.where(Invoice.invoice_date <= end)
        rows = self._session.execute(stmt).mappings().all()
        return pd.DataFrame(rows)

    def product_sales(self, *, start: dt.date | None = None, end: dt.date | None = None) -> pd.DataFrame:
        stmt = (
            select(
                InvoiceItem.product_name.label("product"),
                func.sum(InvoiceItem.quantity).label("qty"),
                func.sum(InvoiceItem.amount).label("amount"),
                func.count(func.distinct(Invoice.id)).label("invoices"),
            )
            .join(Invoice, Invoice.id == InvoiceItem.invoice_id)
            .group_by(InvoiceItem.product_name)
            .order_by(func.sum(InvoiceItem.amount).desc())
        )
        if start:
            stmt = stmt.where(Invoice.invoice_date >= start)
        if end:
            stmt = stmt.where(Invoice.invoice_date <= end)
        rows = self._session.execute(stmt).mappings().all()
        return pd.DataFrame(rows)

    def kpis(self) -> dict[str, float]:
        total_sales = self._session.scalar(select(func.coalesce(func.sum(Invoice.grand_total), 0.0))) or 0.0
        invoice_count = self._session.scalar(select(func.count(Invoice.id))) or 0
        customer_count = self._session.scalar(select(func.count(Customer.id))) or 0
        # Revenue ~= total sales for this MVP
        revenue = float(total_sales)
        return {
            "total_sales": float(total_sales),
            "total_invoices": float(invoice_count),
            "customers": float(customer_count),
            "revenue": float(revenue),
        }

    def monthly_sales(self, *, months: int = 6) -> pd.DataFrame:
        """
        Returns last N months (including current) with summed grand_total.
        SQLite-compatible (uses strftime).
        """
        ym = func.strftime("%Y-%m", Invoice.invoice_date)
        stmt = (
            select(
                ym.label("month"),
                func.coalesce(func.sum(Invoice.grand_total), 0.0).label("grand_total"),
            )
            .group_by(ym)
            .order_by(ym.desc())
            .limit(months)
        )
        rows = list(self._session.execute(stmt).mappings().all())
        df = pd.DataFrame(rows)
        if not df.empty:
            df = df.sort_values("month")
        return df

