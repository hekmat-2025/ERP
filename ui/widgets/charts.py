from __future__ import annotations

from dataclasses import dataclass

import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget


@dataclass(frozen=True)
class ChartData:
    x: list
    y: list[float]


class LineChartCanvas(QWidget):
    """
    PyQtGraph-based line chart (more stable than matplotlib in mixed Qt environments).
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.plot = pg.PlotWidget()
        self.plot.setBackground(None)
        self.plot.showGrid(x=True, y=True, alpha=0.15)
        self.plot.getAxis("left").setTextPen("#e2e8f0")
        self.plot.getAxis("bottom").setTextPen("#e2e8f0")
        self.plot.getAxis("left").setPen(pg.mkPen("#94a3b8", width=1, style=pg.QtCore.Qt.PenStyle.SolidLine))
        self.plot.getAxis("bottom").setPen(pg.mkPen("#94a3b8", width=1, style=pg.QtCore.Qt.PenStyle.SolidLine))

        from PyQt5.QtWidgets import QVBoxLayout

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.plot, 1)

        self._curve = self.plot.plot(
            [],
            [],
            pen=pg.mkPen("#3b82f6", width=3),
            symbol="o",
            symbolSize=5,
            symbolBrush="#3b82f6",
        )
        self._bars: pg.BarGraphItem | None = None

    def plot_monthly(self, labels: list[str], values: list[float]) -> None:
        # line chart
        if self._bars is not None:
            self.plot.removeItem(self._bars)
            self._bars = None
        x = list(range(len(values)))
        self._curve.setData(x, values)
        ax = self.plot.getAxis("bottom")
        ax.setTicks([list(zip(x, labels))])
        self.plot.enableAutoRange(axis="y", enable=True)

    def plot_monthly_bars(self, labels: list[str], values: list[float]) -> None:
        # multicolor bar chart
        self._curve.setData([], [])
        if self._bars is not None:
            self.plot.removeItem(self._bars)
            self._bars = None

        x = list(range(len(values)))
        palette = ["#3b82f6", "#22c55e", "#f59e0b", "#a855f7", "#ef4444", "#06b6d4"]
        brushes = [pg.mkBrush(palette[i % len(palette)]) for i in range(len(values))]
        self._bars = pg.BarGraphItem(x=x, height=values, width=0.65, brushes=brushes)
        self.plot.addItem(self._bars)

        ax = self.plot.getAxis("bottom")
        ax.setTicks([list(zip(x, labels))])
        self.plot.enableAutoRange(axis="y", enable=True)

