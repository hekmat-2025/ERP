from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PyQt5.QtCore import QSize, Qt, pyqtSignal
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import QFrame, QLabel, QToolButton, QVBoxLayout, QWidget


@dataclass(frozen=True)
class NavItem:
    key: str
    label: str
    icon_path: Path | None = None


class NavButton(QToolButton):
    def __init__(self, item: NavItem, parent=None) -> None:
        super().__init__(parent)
        self.item = item
        self.setProperty("variant", "nav")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.setIconSize(QSize(18, 18))
        self.setText(item.label)
        if item.icon_path and item.icon_path.exists():
            self.setIcon(QIcon(str(item.icon_path)))

    def set_active(self, active: bool) -> None:
        self.setProperty("active", "true" if active else "false")
        self.style().unpolish(self)
        self.style().polish(self)


class Sidebar(QFrame):
    nav_changed = pyqtSignal(str)
    switch_business = pyqtSignal()

    def __init__(
        self,
        *,
        logo_path: Path,
        title: str,
        items: list[NavItem],
        switch_icon_path: Path | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setProperty("variant", "sidebar")
        self.setFixedWidth(220)

        self._buttons: dict[str, NavButton] = {}
        self._logo_path = logo_path
        self._title = title

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        # Header
        header = QFrame()
        header.setProperty("variant", "card")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(12, 12, 12, 12)
        header_layout.setSpacing(6)

        self._logo_label = QLabel()
        self._logo_label.setFixedSize(52, 52)
        self._logo_label.setAlignment(Qt.AlignCenter)

        self._title_label = QLabel(title)
        self._title_label.setProperty("variant", "h2")
        self._title_label.setWordWrap(True)

        header_layout.addWidget(self._logo_label)
        header_layout.addWidget(self._title_label)
        layout.addWidget(header)
        self.set_header(logo_path=logo_path, title=title)

        # Nav buttons
        for item in items:
            btn = NavButton(item)
            btn.clicked.connect(lambda _=False, k=item.key: self.nav_changed.emit(k))
            layout.addWidget(btn)
            self._buttons[item.key] = btn

        layout.addStretch(1)

        switch_btn = NavButton(NavItem("__switch__", "Switch Business", switch_icon_path))
        # Allow icon if present via assets/icons/switch.svg (caller can override if needed)
        switch_btn.clicked.connect(lambda _=False: self.switch_business.emit())
        layout.addWidget(switch_btn)

    def set_active(self, key: str) -> None:
        for k, btn in self._buttons.items():
            btn.set_active(k == key)

    def set_header(self, *, logo_path: Path, title: str) -> None:
        self._logo_path = logo_path
        self._title = title
        self._title_label.setText(title)

        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                self._logo_label.setPixmap(pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                self._logo_label.setText("")
                return

        self._logo_label.setPixmap(QPixmap())
        self._logo_label.setText("LOGO")
        self._logo_label.setProperty("variant", "muted")
        self._logo_label.style().unpolish(self._logo_label)
        self._logo_label.style().polish(self._logo_label)

