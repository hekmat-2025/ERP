from __future__ import annotations

import datetime as dt
import logging
from pathlib import Path

from PyQt5.QtCore import QDate, QLocale, Qt
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QCompleter,
    QComboBox,
    QDateEdit,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QFileDialog,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session, sessionmaker

from models.product import Product
from services.invoice_numbering import next_invoice_number
from services.invoices_service import CreateInvoiceRequest, InvoiceItemDraft, InvoicesService
from services.products_service import ProductsService
from services.validation import ValidationError
from utils.config import Settings
from utils.money_words import amount_to_words, currency_units
from services.print_service import PrintService
from ui.widgets import Card, DangerButton, PrimaryButton, h1, muted
from ui.widgets import ResponsiveTwoPane
from ui.widgets.product_id_picker import ProductIdPicker

logger = logging.getLogger(__name__)


class InvoicePage(QWidget):
    """
    Phase 1: invoice draft UI + calculations (save/pdf next).
    """

    COL_PRODUCT = 0
    COL_HSN = 1
    COL_GST = 2
    COL_RATE = 3
    COL_QTY = 4
    COL_AMOUNT = 5

    def __init__(self, *, settings: Settings, session_factory: sessionmaker[Session]) -> None:
        super().__init__()
        self._settings = settings
        self._session_factory = session_factory
        self._products: list[Product] = []
        self._products_by_hsn: dict[str, Product] = {}
        self._products_by_hsn_norm: dict[str, Product] = {}
        self._recalc_guard = False
        self._last_saved_invoice_id: int | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header_card = Card()
        header_layout = QHBoxLayout(header_card)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(14)
        header_layout.addWidget(h1("Invoices"))
        header_layout.addStretch(1)
        header_layout.addWidget(muted("Create and print professional invoices"))
        root.addWidget(header_card)

        grid = QVBoxLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(14)
        root.addLayout(grid, 1)

        # Customer / Invoice meta
        meta_card = Card()
        meta_layout = QVBoxLayout(meta_card)
        meta_layout.setContentsMargins(16, 16, 16, 16)
        meta_layout.setSpacing(10)

        meta_layout.addWidget(QLabel("Customer & Invoice Info"))

        self.invoice_no = QLineEdit()
        self.invoice_no.setReadOnly(True)
        self.invoice_date = QDateEdit()
        self.invoice_date.setCalendarPopup(True)
        self.invoice_date.setLocale(QLocale(QLocale.English, QLocale.UnitedStates))
        self.invoice_date.setDisplayFormat("ddd, dd MMM yyyy")
        self.invoice_date.setDate(dt.date.today())
        self.customer = QComboBox()
        self.customer.setMinimumWidth(260)
        self.customer.setEditable(True)
        self.customer.setInsertPolicy(QComboBox.NoInsert)
        self.customer.setMaxVisibleItems(12)

        meta_form = QFormLayout()
        meta_form.setLabelAlignment(Qt.AlignLeft)
        meta_form.addRow("Invoice No.", self.invoice_no)
        meta_form.addRow("Date", self.invoice_date)
        meta_form.addRow("Customer", self.customer)
        meta_layout.addLayout(meta_form)
        meta_layout.addStretch(1)

        # Items table
        items_card = Card()
        items_layout = QVBoxLayout(items_card)
        items_layout.setContentsMargins(16, 16, 16, 16)
        items_layout.setSpacing(10)

        items_header = QHBoxLayout()
        items_header.addWidget(QLabel("Items"))
        items_header.addStretch(1)
        self.add_row_btn = QPushButton("Add Item")
        self.del_row_btn = DangerButton("Remove")
        items_header.addWidget(self.add_row_btn)
        items_header.addWidget(self.del_row_btn)
        items_layout.addLayout(items_header)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["Product (HSN)", "HSN", "GST %", "Rate", "Qty", "Amount"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setAlternatingRowColors(True)
        # Readable, ERP-like table sizing
        self.table.setFont(QFont("Segoe UI", 12))
        self.table.horizontalHeader().setMinimumHeight(38)
        self.table.verticalHeader().setDefaultSectionSize(46)
        self.table.setWordWrap(False)
        self.table.setHorizontalScrollMode(self.table.ScrollPerPixel)

        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(self.COL_PRODUCT, QHeaderView.Stretch)
        for col in (self.COL_HSN, self.COL_GST, self.COL_RATE, self.COL_QTY, self.COL_AMOUNT):
            header.setSectionResizeMode(col, QHeaderView.ResizeToContents)
        items_layout.addWidget(self.table, 1)

        # Summary + actions
        summary_card = Card()
        summary_layout = QVBoxLayout(summary_card)
        summary_layout.setContentsMargins(16, 16, 16, 16)
        summary_layout.setSpacing(10)

        summary_layout.addWidget(QLabel("Summary"))
        self.gross_lbl = QLabel("0.00")
        self.tax_lbl = QLabel("0.00")
        self.grand_lbl = QLabel("0.00")
        self.grand_lbl.setProperty("variant", "h1")
        self.words_lbl = muted("Amount in words: -")

        sum_form = QFormLayout()
        sum_form.addRow("Gross Amount", self.gross_lbl)
        sum_form.addRow("Tax", self.tax_lbl)
        sum_form.addRow("Grand Total", self.grand_lbl)
        summary_layout.addLayout(sum_form)
        summary_layout.addWidget(self.words_lbl)
        summary_layout.addStretch(1)

        actions = QHBoxLayout()
        self.cancel_btn = QPushButton("New Invoice")
        self.save_btn = PrimaryButton("Save")
        self.print_btn = QPushButton("Print / PDF")
        self.print_btn.setEnabled(False)
        actions.addWidget(self.cancel_btn)
        actions.addStretch(1)
        actions.addWidget(self.print_btn)
        actions.addWidget(self.save_btn)
        summary_layout.addLayout(actions)

        top_row = ResponsiveTwoPane(meta_card, summary_card, breakpoint_px=980)
        grid.addWidget(top_row)
        grid.addWidget(items_card, 1)

        self.add_row_btn.clicked.connect(self.add_row)
        self.del_row_btn.clicked.connect(self.remove_selected_row)
        self.save_btn.clicked.connect(self._on_save)
        self.print_btn.clicked.connect(self._on_print_pdf)
        self.cancel_btn.clicked.connect(self._reset_for_next_invoice)
        self.table.itemChanged.connect(self.recalculate)
        self.table.cellClicked.connect(self._on_table_cell_clicked)

        self._reload_header()
        self.add_row()

    def _on_table_cell_clicked(self, row: int, col: int) -> None:
        if col != self.COL_PRODUCT:
            return
        picker = self._product_picker(row)
        if picker:
            picker.focus_hsn()

    def _reload_header(self) -> None:
        with self._session_factory() as session:
            self.invoice_no.setText(next_invoice_number(session))

            self.customer.clear()
            from sqlalchemy import select

            from models.customer import Customer

            for c in session.scalars(select(Customer).order_by(Customer.name.asc())):
                self.customer.addItem(c.name, c.id)

            self._products = ProductsService(session).list_products()
            self._products_by_hsn = {
                str(p.hsn_code).strip().lower(): p
                for p in self._products
                if str(p.hsn_code or "").strip()
            }
            self._products_by_hsn_norm = {
                self._norm_hsn(str(p.hsn_code)): p
                for p in self._products
                if str(p.hsn_code or "").strip()
            }

        # Searchable customer dropdown (type to filter)
        completer = QCompleter([self.customer.itemText(i) for i in range(self.customer.count())], self.customer)
        completer.setCaseSensitivity(Qt.CaseInsensitive)
        completer.setFilterMode(Qt.MatchContains)
        completer.setCompletionMode(QCompleter.PopupCompletion)
        self.customer.setCompleter(completer)

        self._last_saved_invoice_id = None
        self.print_btn.setEnabled(False)

    def add_row(self) -> None:
        r = self.table.rowCount()
        self.table.insertRow(r)

        picker = ProductIdPicker()
        picker.changed.connect(lambda _res, row=r: self._on_product_id_changed(row))
        self.table.setCellWidget(r, self.COL_PRODUCT, picker)

        self.table.setItem(r, self.COL_HSN, QTableWidgetItem(""))
        self.table.setItem(r, self.COL_GST, QTableWidgetItem("0.00"))
        self.table.setItem(r, self.COL_RATE, QTableWidgetItem("0.00"))
        self.table.setItem(r, self.COL_QTY, QTableWidgetItem("1"))
        amt = QTableWidgetItem("0.00")
        amt.setFlags(amt.flags() & ~Qt.ItemIsEditable)
        self.table.setItem(r, self.COL_AMOUNT, amt)

        self.recalculate()

    def _product_picker(self, row: int) -> ProductIdPicker | None:
        w = self.table.cellWidget(row, self.COL_PRODUCT)
        return w if isinstance(w, ProductIdPicker) else None

    def _on_product_id_changed(self, row: int) -> None:
        picker = self._product_picker(row)
        if not picker:
            return
        raw_hsn = picker.hsn_code().strip()
        hsn = raw_hsn.lower()
        hsn_norm = self._norm_hsn(raw_hsn)

        selected: Product | None = None
        if hsn:
            selected = self._products_by_hsn.get(hsn) or self._products_by_hsn_norm.get(hsn_norm)
            if not selected and hsn_norm:
                # partial match: first startswith
                for key, p in self._products_by_hsn_norm.items():
                    if key.startswith(hsn_norm):
                        selected = p
                        break

        if not selected:
            picker.set_name("Not found" if hsn else "—")
            return

        # Do not overwrite what the user typed (no auto-complete)
        picker.set_name(selected.name)

        self._recalc_guard = True
        try:
            hsn = self.table.item(row, self.COL_HSN)
            gst = self.table.item(row, self.COL_GST)
            rate = self.table.item(row, self.COL_RATE)
            if hsn:
                hsn.setText(selected.hsn_code or "")
            if gst:
                gst.setText(f"{float(selected.gst_rate):.2f}")
            if rate:
                rate.setText(f"{float(selected.rate):.2f}")
        finally:
            self._recalc_guard = False
        self.recalculate()

    @staticmethod
    def _norm_hsn(value: str) -> str:
        v = (value or "").strip().lower()
        for ch in (" ", "-", "_", "/"):
            v = v.replace(ch, "")
        return v

    def remove_selected_row(self) -> None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return
        self.table.removeRow(rows[0].row())
        self.recalculate()

    def _num(self, r: int, c: int) -> float:
        item = self.table.item(r, c)
        if not item:
            return 0.0
        try:
            return float(item.text() or 0)
        except Exception:
            return 0.0

    def recalculate(self) -> None:
        if self._recalc_guard:
            return
        gross = 0.0
        tax = 0.0
        for r in range(self.table.rowCount()):
            qty = self._num(r, self.COL_QTY)
            rate = self._num(r, self.COL_RATE)
            gst_rate = self._num(r, self.COL_GST)
            amount = max(0.0, qty) * max(0.0, rate)
            gross += amount
            if self._settings.tax_enabled:
                tax += amount * (max(0.0, gst_rate) / 100.0)
            amt_item = self.table.item(r, self.COL_AMOUNT)
            if amt_item:
                amt_item.setText(f"{amount:.2f}")
        grand = gross + tax
        self.gross_lbl.setText(f"{gross:.2f}")
        self.tax_lbl.setText(f"{tax:.2f}")
        self.grand_lbl.setText(f"{grand:.2f}")
        units = currency_units(self._settings.currency_code)
        self.words_lbl.setText(f"Amount in words: {amount_to_words(grand, major_unit=units.major, minor_unit=units.minor)}")

    def _on_save(self) -> None:
        try:
            customer_id = self.customer.currentData()
            if not customer_id:
                raise ValidationError("Customer is required.")

            items: list[InvoiceItemDraft] = []
            for r in range(self.table.rowCount()):
                picker = self._product_picker(r)
                if not picker:
                    continue
                raw_hsn = picker.hsn_code().strip()
                hsn_norm = self._norm_hsn(raw_hsn)
                selected = self._products_by_hsn_norm.get(hsn_norm) if hsn_norm else None
                if not selected:
                    # allow empty rows at bottom
                    continue
                name = picker.product_name().strip() if picker else ""
                items.append(
                    InvoiceItemDraft(
                        product_id=int(selected.id),
                        product_name=name,
                        hsn_code=(self.table.item(r, self.COL_HSN).text() if self.table.item(r, self.COL_HSN) else ""),
                        gst_rate=self._num(r, self.COL_GST),
                        rate=self._num(r, self.COL_RATE),
                        quantity=self._num(r, self.COL_QTY),
                    )
                )

            if not items:
                raise ValidationError("Add at least one item row with a product.")

            with self._session_factory() as session:
                svc = InvoicesService(session)
                req = CreateInvoiceRequest(
                    invoice_no=self.invoice_no.text().strip(),
                    invoice_date=self.invoice_date.date().toPyDate(),
                    customer_id=int(customer_id),
                    tax_enabled=bool(self._settings.tax_enabled),
                    items=items,
                )
                res = svc.create_invoice(req)

            self._last_saved_invoice_id = res.invoice_id
            self.print_btn.setEnabled(True)
            self.save_btn.setEnabled(False)
            QMessageBox.information(
                self,
                "Saved",
                f"Invoice saved successfully.\nInvoice No: {res.invoice_no}\nGrand Total: {res.grand_total:.2f}",
            )
        except ValidationError as e:
            QMessageBox.warning(self, "Validation", str(e))
        except Exception as e:  # noqa: BLE001
            logger.exception("Invoice save failed")
            QMessageBox.critical(self, "Error", str(e))

    def _reset_for_next_invoice(self) -> None:
        self.table.setRowCount(0)
        self._reload_header()
        self.add_row()
        self.save_btn.setEnabled(True)
        self.print_btn.setEnabled(False)

    def _on_print_pdf(self) -> None:
        if not self._last_saved_invoice_id:
            QMessageBox.information(self, "Print / PDF", "Save the invoice first.")
            return

        default_name = f"{self._last_saved_invoice_id}.pdf"
        out_path, _ = QFileDialog.getSaveFileName(
            self,
            "Save Invoice PDF",
            default_name,
            "PDF Files (*.pdf)",
        )
        if not out_path:
            return

        try:
            with self._session_factory() as session:
                PrintService(session, settings=self._settings).invoice_to_pdf(
                    invoice_id=int(self._last_saved_invoice_id),
                    output_pdf=Path(out_path),
                )
            QMessageBox.information(self, "PDF Created", f"Saved:\n{out_path}")
        except Exception as e:  # noqa: BLE001
            logger.exception("PDF generation failed")
            QMessageBox.critical(self, "PDF failed", str(e))

