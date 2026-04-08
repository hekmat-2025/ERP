from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QScrollArea, QWidget


class PageScrollArea(QScrollArea):
    """
    Wraps a page widget so content can scroll on small windows.
    """

    def __init__(self, page: QWidget, parent=None) -> None:
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setFrameShape(QScrollArea.NoFrame)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setWidget(page)
        # Let the app stylesheet show through.
        self.viewport().setAutoFillBackground(False)
        self.setAutoFillBackground(False)

