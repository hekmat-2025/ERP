from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

import pandas as pd
from PyQt5.QtCore import QDate, QLocale
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDateEdit,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QTabWidget,
    QTableWidget,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session, sessionmaker

from services.reports_service import ReportsService
from ui.widgets.dataframe_table import fill_table_from_dataframe
from ui.widgets import Card, PrimaryButton, h1, muted

logger = logging.getLogger(__name__)


class ReportsPage(QWidget):
    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._active_df: pd.DataFrame | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = Card()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.addWidget(h1("Reports"))
        header_layout.addStretch(1)
        header_layout.addWidget(muted("Sales analysis and exports"))
        root.addWidget(header)

        filters_card = Card()
        filters_layout = QHBoxLayout(filters_card)
        filters_layout.setContentsMargins(16, 16, 16, 16)
        filters_layout.setSpacing(10)

        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.start_date.setDisplayFormat("ddd, dd MMM yyyy")
        self.start_date.setDate(QDate.currentDate().addMonths(-1))
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.end_date.setDisplayFormat("ddd, dd MMM yyyy")
        self.end_date.setDate(QDate.currentDate())
        self.refresh_btn = PrimaryButton("Refresh")
        self.export_btn = QPushButton("Export Excel")

        filters_layout.addWidget(QLabel("From"))
        filters_layout.addWidget(self.start_date)
        filters_layout.addWidget(QLabel("To"))
        filters_layout.addWidget(self.end_date)
        filters_layout.addStretch(1)
        filters_layout.addWidget(self.export_btn)
        filters_layout.addWidget(self.refresh_btn)
        root.addWidget(filters_card)

        content_card = Card()
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(10)

        self.tabs = QTabWidget()
        content_layout.addWidget(self.tabs, 1)
        root.addWidget(content_card, 1)

        self.invoice_table = self._make_table()
        self.daily_table = self._make_table()
        self.product_table = self._make_table()

        self.tabs.addTab(self.invoice_table, "Invoice History")
        self.tabs.addTab(self.daily_table, "Sales (Daily)")
        self.tabs.addTab(self.product_table, "Product Sales")

        self.refresh_btn.clicked.connect(self.refresh)
        self.export_btn.clicked.connect(self.export_excel)

        self.refresh()

    def _make_table(self) -> QTableWidget:
        t = QTableWidget()
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setEditTriggers(QAbstractItemView.NoEditTriggers)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setSortingEnabled(True)
        return t

    def _date_range(self) -> tuple[dt.date, dt.date]:
        return (self.start_date.date().toPyDate(), self.end_date.date().toPyDate())

    def refresh(self) -> None:
        start, end = self._date_range()
        try:
            with self._session_factory() as session:
                svc = ReportsService(session)
                inv_df = svc.invoice_history(start=start, end=end)
                day_df = svc.sales_by_day(start=start, end=end)
                prod_df = svc.product_sales(start=start, end=end)

            fill_table_from_dataframe(self.invoice_table, inv_df)
            fill_table_from_dataframe(self.daily_table, day_df)
            fill_table_from_dataframe(self.product_table, prod_df)

            # Default export target: current tab dataframe
            idx = self.tabs.currentIndex()
            self._active_df = [inv_df, day_df, prod_df][idx]
        except Exception as e:  # noqa: BLE001
            logger.exception("Report refresh failed")
            QMessageBox.critical(self, "Reports error", str(e))

    def export_excel(self) -> None:
        idx = self.tabs.currentIndex()
        label = self.tabs.tabText(idx).replace(" ", "_").lower()
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export to Excel",
            f"{label}.xlsx",
            "Excel Files (*.xlsx)",
        )
        if not out_path:
            return

        start, end = self._date_range()
        try:
            with self._session_factory() as session:
                svc = ReportsService(session)
                inv_df = svc.invoice_history(start=start, end=end)
                day_df = svc.sales_by_day(start=start, end=end)
                prod_df = svc.product_sales(start=start, end=end)

            with pd.ExcelWriter(out_path) as writer:
                inv_df.to_excel(writer, sheet_name="invoice_history", index=False)
                day_df.to_excel(writer, sheet_name="sales_daily", index=False)
                prod_df.to_excel(writer, sheet_name="product_sales", index=False)

            QMessageBox.information(self, "Exported", f"Saved:\n{out_path}")
        except Exception as e:  # noqa: BLE001
            logger.exception("Export failed")
            QMessageBox.critical(self, "Export failed", str(e))

