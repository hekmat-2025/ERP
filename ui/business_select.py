from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from ui.widgets import Card, PrimaryButton, h1, muted


@dataclass(frozen=True)
class BusinessChoice:
    key: str
    label: str


class BusinessSelectDialog(QDialog):
    def __init__(self, *, logo_path: Path, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setModal(True)
        self.setWindowTitle("Select Business")
        self.setMinimumWidth(520)

        self.choice: str | None = None

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = Card()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.setSpacing(12)

        logo = QLabel()
        logo.setFixedSize(56, 56)
        logo.setAlignment(Qt.AlignCenter)
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                logo.setPixmap(pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        else:
            logo.setText("LOGO")
            logo.setProperty("variant", "muted")

        header_layout.addWidget(logo)
        header_layout.addWidget(h1("Select Business"))
        header_layout.addStretch(1)
        root.addWidget(header)

        root.addWidget(muted("Choose which business you want to work with. Data is stored separately per business."))

        options = Card()
        options_layout = QHBoxLayout(options)
        options_layout.setContentsMargins(16, 16, 16, 16)
        options_layout.setSpacing(14)

        btn1 = PrimaryButton("1) Aftab Sahar")
        btn1.setMinimumHeight(44)
        btn1.clicked.connect(lambda: self._pick("aftab_sahar"))

        btn2 = PrimaryButton("2) M.T.S")
        btn2.setMinimumHeight(44)
        btn2.clicked.connect(lambda: self._pick("mts"))

        options_layout.addWidget(btn1, 1)
        options_layout.addWidget(btn2, 1)
        root.addWidget(options)

    def _pick(self, key: str) -> None:
        self.choice = key
        self.accept()

