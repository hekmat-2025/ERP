from __future__ import annotations

from PyQt5.QtWidgets import QGridLayout, QSizePolicy, QWidget


class ResponsiveTwoPane(QWidget):
    """
    Switches between horizontal (two columns) and vertical (stacked) based on width.
    """

    def __init__(self, left: QWidget, right: QWidget, *, breakpoint_px: int = 980, parent=None) -> None:
        super().__init__(parent)
        self._breakpoint_px = int(breakpoint_px)
        self._left = left
        self._right = right

        self._grid = QGridLayout(self)
        self._grid.setContentsMargins(0, 0, 0, 0)
        self._grid.setHorizontalSpacing(14)
        self._grid.setVerticalSpacing(14)
        self._grid.setColumnStretch(0, 3)
        self._grid.setColumnStretch(1, 2)

        self._mode: str | None = None
        self._apply_mode("h")

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def resizeEvent(self, event) -> None:  # noqa: D401
        super().resizeEvent(event)
        self._update_mode()

    def _update_mode(self) -> None:
        mode = "v" if self.width() < self._breakpoint_px else "h"
        if mode != self._mode:
            self._apply_mode(mode)

    def _apply_mode(self, mode: str) -> None:
        self._mode = mode
        # Move widgets within a single layout (safe for Qt).
        self._grid.removeWidget(self._left)
        self._grid.removeWidget(self._right)
        if mode == "h":
            self._grid.addWidget(self._left, 0, 0)
            self._grid.addWidget(self._right, 0, 1)
        else:
            self._grid.addWidget(self._left, 0, 0, 1, 2)
            self._grid.addWidget(self._right, 1, 0, 1, 2)

