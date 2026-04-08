from __future__ import annotations

import logging

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session, sessionmaker

from services.customers_service import CustomersService
from services.validation import ValidationError
from ui.widgets import Card, DangerButton, PrimaryButton, h1, muted

logger = logging.getLogger(__name__)


class CustomerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Customer")
        self.setModal(True)
        self.resize(460, 240)

        self.name = QLineEdit()
        self.address = QLineEdit()
        self.phone = QLineEdit()

        form = QFormLayout()
        form.addRow("Name*", self.name)
        form.addRow("Address", self.address)
        form.addRow("Phone", self.phone)

        buttons = QHBoxLayout()
        self.save_btn = PrimaryButton("Save")
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        buttons.addStretch(1)
        buttons.addWidget(self.save_btn)
        buttons.addWidget(self.cancel_btn)

        root = QVBoxLayout(self)
        root.addLayout(form)
        root.addStretch(1)
        root.addLayout(buttons)


class CustomersPage(QWidget):
    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        super().__init__()
        self._session_factory = session_factory

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = Card()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.addWidget(h1("Customers"))
        header_layout.addStretch(1)
        header_layout.addWidget(muted("Customer master data"))
        root.addWidget(header)

        card = Card()
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 16, 16, 16)
        card_layout.setSpacing(10)

        actions = QHBoxLayout()
        self.add_btn = PrimaryButton("Add")
        self.edit_btn = QPushButton("Edit")
        self.del_btn = DangerButton("Delete")
        self.refresh_btn = QPushButton("Refresh")
        actions.addWidget(self.add_btn)
        actions.addWidget(self.edit_btn)
        actions.addWidget(self.del_btn)
        actions.addStretch(1)
        actions.addWidget(self.refresh_btn)
        card_layout.addLayout(actions)

        self.table = QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Address", "Phone"])
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        card_layout.addWidget(self.table, 1)

        root.addWidget(card, 1)

        self.add_btn.clicked.connect(self._on_add)
        self.edit_btn.clicked.connect(self._on_edit)
        self.del_btn.clicked.connect(self._on_delete)
        self.refresh_btn.clicked.connect(self.reload)

        self.reload()

    def _selected_id(self) -> int | None:
        rows = self.table.selectionModel().selectedRows()
        if not rows:
            return None
        row = rows[0].row()
        item = self.table.item(row, 0)
        if not item:
            return None
        try:
            return int(item.text())
        except Exception:
            return None

    def reload(self) -> None:
        with self._session_factory() as session:
            svc = CustomersService(session)
            customers = svc.list_customers()

        self.table.setRowCount(0)
        for c in customers:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(c.id)))
            self.table.setItem(r, 1, QTableWidgetItem(c.name))
            self.table.setItem(r, 2, QTableWidgetItem(c.address))
            self.table.setItem(r, 3, QTableWidgetItem(c.phone))

        self.table.resizeColumnsToContents()

    def _on_add(self) -> None:
        dlg = CustomerDialog(self)
        dlg.save_btn.clicked.connect(lambda: self._save_new(dlg))
        dlg.exec()

    def _save_new(self, dlg: CustomerDialog) -> None:
        try:
            with self._session_factory() as session:
                svc = CustomersService(session)
                svc.create_customer(
                    name=dlg.name.text(),
                    address=dlg.address.text(),
                    phone=dlg.phone.text(),
                )
            dlg.accept()
            self.reload()
        except ValidationError as e:
            QMessageBox.warning(self, "Validation", str(e))
        except Exception as e:  # noqa: BLE001
            logger.exception("Create customer failed")
            QMessageBox.critical(self, "Error", str(e))

    def _on_edit(self) -> None:
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "Select", "Select a customer row first.")
            return
        with self._session_factory() as session:
            c = session.get(__import__("models.customer", fromlist=["Customer"]).Customer, cid)
            if not c:
                QMessageBox.warning(self, "Not found", "Customer not found.")
                return
            dlg = CustomerDialog(self)
            dlg.name.setText(c.name)
            dlg.address.setText(c.address)
            dlg.phone.setText(c.phone)
            dlg.save_btn.clicked.connect(lambda: self._save_edit(dlg, cid))
        dlg.exec()

    def _save_edit(self, dlg: CustomerDialog, cid: int) -> None:
        try:
            with self._session_factory() as session:
                svc = CustomersService(session)
                svc.update_customer(
                    cid,
                    name=dlg.name.text(),
                    address=dlg.address.text(),
                    phone=dlg.phone.text(),
                )
            dlg.accept()
            self.reload()
        except ValidationError as e:
            QMessageBox.warning(self, "Validation", str(e))
        except Exception as e:  # noqa: BLE001
            logger.exception("Update customer failed")
            QMessageBox.critical(self, "Error", str(e))

    def _on_delete(self) -> None:
        cid = self._selected_id()
        if not cid:
            QMessageBox.information(self, "Select", "Select a customer row first.")
            return
        if QMessageBox.question(self, "Confirm", "Delete selected customer?") != QMessageBox.StandardButton.Yes:
            return
        try:
            with self._session_factory() as session:
                svc = CustomersService(session)
                svc.delete_customer(cid)
            self.reload()
        except Exception as e:  # noqa: BLE001
            logger.exception("Delete customer failed")
            QMessageBox.critical(self, "Error", str(e))

