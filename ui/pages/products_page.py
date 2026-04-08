from __future__ import annotations

import logging
import shutil
import uuid
from pathlib import Path

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
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
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt
from sqlalchemy.orm import Session, sessionmaker

from services.products_service import ProductsService
from services.validation import ValidationError
from ui.widgets import Card, DangerButton, PrimaryButton, h1, muted
from utils.paths import app_root, data_dir

logger = logging.getLogger(__name__)


class ProductDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Product")
        self.setModal(True)
        self.resize(520, 320)

        self.name = QLineEdit()
        self.hsn = QLineEdit()
        self.rate = QDoubleSpinBox()
        self.rate.setMaximum(1_000_000_000)
        self.rate.setDecimals(2)
        self.gst = QDoubleSpinBox()
        self.gst.setMaximum(1000)
        self.gst.setDecimals(2)

        self.image_path = QLineEdit()
        self.image_path.setReadOnly(True)
        self.browse_image_btn = QPushButton("Browse…")
        self.preview = QLabel("No image")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedHeight(140)
        self.preview.setStyleSheet("border: 1px solid rgba(148,163,184,0.35); border-radius: 10px;")

        img_row = QHBoxLayout()
        img_row.addWidget(self.image_path, 1)
        img_row.addWidget(self.browse_image_btn)

        form = QFormLayout()
        form.addRow("Name*", self.name)
        form.addRow("HSN code", self.hsn)
        form.addRow("Rate", self.rate)
        form.addRow("GST rate %", self.gst)
        form.addRow("Image", img_row)
        form.addRow("", self.preview)

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

        self.browse_image_btn.clicked.connect(self._browse_image)

    def _browse_image(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select product image",
            str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
        )
        if not path:
            return

        src = Path(path)
        images_dir = data_dir() / "product_images"
        images_dir.mkdir(parents=True, exist_ok=True)
        dst = images_dir / f"{uuid.uuid4().hex}{src.suffix.lower()}"
        try:
            shutil.copy2(src, dst)
        except Exception as e:  # noqa: BLE001
            QMessageBox.critical(self, "Image copy failed", str(e))
            return

        rel = dst.resolve().relative_to(app_root().resolve()).as_posix()
        self.image_path.setText(rel)
        self._set_preview(dst)

    def _set_preview(self, p: Path) -> None:
        if not p.exists():
            self.preview.setText("No image")
            self.preview.setPixmap(QPixmap())
            return
        pix = QPixmap(str(p))
        if pix.isNull():
            self.preview.setText("Invalid image")
            self.preview.setPixmap(QPixmap())
            return
        self.preview.setPixmap(pix.scaledToHeight(120, Qt.SmoothTransformation))


class ProductsPage(QWidget):
    def __init__(self, *, session_factory: sessionmaker[Session]) -> None:
        super().__init__()
        self._session_factory = session_factory
        self._all_products = []

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = Card()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.addWidget(h1("Products"))
        header_layout.addStretch(1)
        header_layout.addWidget(muted("Materials and rate master"))
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
        self.search = QLineEdit()
        self.search.setPlaceholderText("Search by name or HSN…")
        self.search.setMinimumWidth(260)
        actions.addStretch(1)
        actions.addWidget(self.search)
        actions.addWidget(self.refresh_btn)
        card_layout.addLayout(actions)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Image", "Name", "HSN", "Rate", "GST %"])
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
        self.table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self.search.textChanged.connect(self._apply_filter)

        self.reload()

    def _on_cell_double_clicked(self, row: int, col: int) -> None:
        if col != 1:
            return
        path_item = self.table.item(row, 0)
        if not path_item:
            return
        pid = self._selected_id()
        if not pid:
            return
        with self._session_factory() as session:
            p = session.get(__import__("models.product", fromlist=["Product"]).Product, pid)
            if not p or not (p.image_path or "").strip():
                return
            img_path = (app_root() / p.image_path).resolve()
        if not img_path.exists():
            QMessageBox.warning(self, "Missing", "Image file not found on disk.")
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Product Image")
        dlg.resize(720, 520)
        v = QVBoxLayout(dlg)
        lbl = QLabel()
        lbl.setAlignment(Qt.AlignCenter)
        pix = QPixmap(str(img_path))
        lbl.setPixmap(pix.scaled(680, 480, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        v.addWidget(lbl, 1)
        dlg.exec()

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
            svc = ProductsService(session)
            self._all_products = svc.list_products()

        self._apply_filter()

    def _apply_filter(self) -> None:
        q = (self.search.text() or "").strip().lower()
        if not q:
            products = list(self._all_products)
        else:
            products = [
                p
                for p in self._all_products
                if q in (p.name or "").lower() or q in (p.hsn_code or "").lower()
            ]

        self.table.setRowCount(0)
        for p in products:
            r = self.table.rowCount()
            self.table.insertRow(r)
            self.table.setItem(r, 0, QTableWidgetItem(str(p.id)))
            # Image cell
            img_item = QTableWidgetItem("View" if (p.image_path or "").strip() else "")
            self.table.setItem(r, 1, img_item)
            self.table.setItem(r, 2, QTableWidgetItem(p.name))
            self.table.setItem(r, 3, QTableWidgetItem(p.hsn_code))
            self.table.setItem(r, 4, QTableWidgetItem(f"{p.rate:.2f}"))
            self.table.setItem(r, 5, QTableWidgetItem(f"{p.gst_rate:.2f}"))

        self.table.resizeColumnsToContents()
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)

    def _on_add(self) -> None:
        dlg = ProductDialog(self)
        dlg.save_btn.clicked.connect(lambda: self._save_new(dlg))
        dlg.exec()

    def _save_new(self, dlg: ProductDialog) -> None:
        try:
            with self._session_factory() as session:
                svc = ProductsService(session)
                svc.create_product(
                    name=dlg.name.text(),
                    hsn_code=dlg.hsn.text(),
                    rate=dlg.rate.value(),
                    gst_rate=dlg.gst.value(),
                    image_path=dlg.image_path.text(),
                )
            dlg.accept()
            self.reload()
        except ValidationError as e:
            QMessageBox.warning(self, "Validation", str(e))
        except Exception as e:  # noqa: BLE001
            logger.exception("Create product failed")
            QMessageBox.critical(self, "Error", str(e))

    def _on_edit(self) -> None:
        pid = self._selected_id()
        if not pid:
            QMessageBox.information(self, "Select", "Select a product row first.")
            return
        with self._session_factory() as session:
            p = session.get(__import__("models.product", fromlist=["Product"]).Product, pid)
            if not p:
                QMessageBox.warning(self, "Not found", "Product not found.")
                return
            dlg = ProductDialog(self)
            dlg.name.setText(p.name)
            dlg.hsn.setText(p.hsn_code)
            dlg.rate.setValue(float(p.rate))
            dlg.gst.setValue(float(p.gst_rate))
            dlg.image_path.setText((p.image_path or "").strip())
            if (p.image_path or "").strip():
                dlg._set_preview((app_root() / p.image_path).resolve())
            dlg.save_btn.clicked.connect(lambda: self._save_edit(dlg, pid))
        dlg.exec()

    def _save_edit(self, dlg: ProductDialog, pid: int) -> None:
        try:
            with self._session_factory() as session:
                svc = ProductsService(session)
                svc.update_product(
                    pid,
                    name=dlg.name.text(),
                    hsn_code=dlg.hsn.text(),
                    rate=dlg.rate.value(),
                    gst_rate=dlg.gst.value(),
                    image_path=dlg.image_path.text(),
                )
            dlg.accept()
            self.reload()
        except ValidationError as e:
            QMessageBox.warning(self, "Validation", str(e))
        except Exception as e:  # noqa: BLE001
            logger.exception("Update product failed")
            QMessageBox.critical(self, "Error", str(e))

    def _on_delete(self) -> None:
        pid = self._selected_id()
        if not pid:
            QMessageBox.information(self, "Select", "Select a product row first.")
            return
        if QMessageBox.question(self, "Confirm", "Delete selected product?") != QMessageBox.StandardButton.Yes:
            return
        try:
            with self._session_factory() as session:
                svc = ProductsService(session)
                svc.delete_product(pid)
            self.reload()
        except Exception as e:  # noqa: BLE001
            logger.exception("Delete product failed")
            QMessageBox.critical(self, "Error", str(e))

