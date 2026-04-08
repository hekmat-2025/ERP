from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QPushButton


class Card(QFrame):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setProperty("variant", "card")
        self.setFrameShape(QFrame.NoFrame)


class PrimaryButton(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setProperty("variant", "primary")


class DangerButton(QPushButton):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(text, parent)
        self.setProperty("variant", "danger")


def h1(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("variant", "h1")
    return lbl


def h2(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("variant", "h2")
    return lbl


def muted(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("variant", "muted")
    lbl.setTextInteractionFlags(Qt.TextSelectableByMouse)
    return lbl

