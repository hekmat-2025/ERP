from __future__ import annotations

from dataclasses import dataclass

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QSizePolicy, QWidget


@dataclass(frozen=True)
class ProductLookupResult:
    hsn_code: str
    product_name: str


class ProductIdPicker(QWidget):
    """
    ERP-style product selection by ID (fast keyboard workflow).

    User types an integer ID; UI shows resolved product name.
    """

    changed = pyqtSignal(object)  # emits ProductLookupResult

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(32)
        self.setFocusPolicy(Qt.StrongFocus)

        self._hsn = QLineEdit()
        self._hsn.setPlaceholderText("HSN")
        self._hsn.setFixedWidth(160)
        self._hsn.setFont(QFont("Segoe UI", 13))
        self._hsn.setFixedHeight(30)
        self._hsn.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self._hsn)

        self._name = QLabel("—")
        self._name.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self._name.setFont(QFont("Segoe UI", 13))
        self._name.setStyleSheet("color: rgba(226, 232, 240, 0.90);")

        layout = QHBoxLayout(self)
        # Keep margins tiny so it fits inside table rows cleanly.
        layout.setContentsMargins(4, 0, 4, 0)
        layout.setSpacing(8)
        layout.addWidget(self._hsn)
        layout.addWidget(self._name, 1)

        # Do NOT auto-complete while typing; only trigger lookup on Enter or when leaving field.
        self._hsn.returnPressed.connect(self._emit)
        self._hsn.editingFinished.connect(self._emit)

    def set_name(self, name: str | None) -> None:
        self._name.setText((name or "—").strip() or "—")

    def set_hsn(self, hsn_code: str | None) -> None:
        self._hsn.setText((hsn_code or "").strip())

    def hsn_code(self) -> str:
        return (self._hsn.text() or "").strip()

    def focus_hsn(self) -> None:
        self._hsn.setFocus(Qt.MouseFocusReason)
        # don't auto-select; user may want to continue typing

    def product_name(self) -> str:
        return (self._name.text() or "").strip().replace("—", "").strip()

    def _emit(self) -> None:
        self.changed.emit(
            ProductLookupResult(
                hsn_code=self.hsn_code(),
                product_name=self.product_name(),
            )
        )

    def mousePressEvent(self, event) -> None:
        # Make the whole cell click focus the editable HSN field.
        self.focus_hsn()
        super().mousePressEvent(event)

