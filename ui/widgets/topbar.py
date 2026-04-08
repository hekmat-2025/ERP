from __future__ import annotations

import datetime as dt

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from utils.text import to_english_digits


class Topbar(QFrame):
    def __init__(self, *, app_title: str, user_text: str = "Offline ERP", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setProperty("variant", "topbar")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 10, 18, 10)
        layout.setSpacing(12)

        self.title = QLabel(app_title)
        self.title.setProperty("variant", "h2")

        self.datetime = QLabel("")
        self.datetime.setProperty("variant", "muted")

        self.user = QLabel(user_text)
        self.user.setProperty("variant", "muted")

        layout.addWidget(self.title)
        layout.addStretch(1)
        layout.addWidget(self.user)
        layout.addWidget(self.datetime)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)
        self._tick()

    def _tick(self) -> None:
        txt = dt.datetime.now().strftime("%a, %d %b %Y  %I:%M:%S %p")
        self.datetime.setText(to_english_digits(txt))

