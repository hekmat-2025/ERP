from __future__ import annotations

from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QGridLayout, QHBoxLayout, QLabel, QVBoxLayout, QWidget
from sqlalchemy.orm import Session, sessionmaker

from services.reports_service import ReportsService
from utils.config import Settings
from ui.widgets import Card, LineChartCanvas, h1, muted


class DashboardPage(QWidget):
    def __init__(self, *, settings: Settings, assets_root: Path, session_factory: sessionmaker[Session] | None = None) -> None:
        super().__init__()
        self._settings = settings
        self._assets_root = assets_root
        self._session_factory = session_factory

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = Card()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)

        logo = QLabel()
        logo.setFixedSize(56, 56)
        logo.setAlignment(Qt.AlignCenter)
        self._try_load_logo(logo)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title_box.addWidget(h1("Dashboard"))
        title_box.addWidget(muted(self._settings.company_name))

        header_layout.addWidget(logo)
        header_layout.addLayout(title_box)
        header_layout.addStretch(1)

        root.addWidget(header)

        # KPI cards
        kpi_grid = QGridLayout()
        kpi_grid.setHorizontalSpacing(14)
        kpi_grid.setVerticalSpacing(14)

        self.kpi_sales = self._kpi_card("Total Sales", "0.00")
        self.kpi_invoices = self._kpi_card("Total Invoices", "0")
        self.kpi_customers = self._kpi_card("Customers", "0")
        self.kpi_revenue = self._kpi_card("Revenue", "0.00")

        kpi_grid.addWidget(self.kpi_sales, 0, 0)
        kpi_grid.addWidget(self.kpi_invoices, 0, 1)
        kpi_grid.addWidget(self.kpi_customers, 0, 2)
        kpi_grid.addWidget(self.kpi_revenue, 0, 3)
        root.addLayout(kpi_grid)

        # Chart card
        chart_card = Card()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(16, 16, 16, 16)
        chart_layout.setSpacing(10)
        chart_layout.addWidget(QLabel("Monthly Sales (Last 6 Months)"))
        self.chart = LineChartCanvas()
        chart_layout.addWidget(self.chart, 1)
        root.addWidget(chart_card, 1)

        self.refresh()

    def _try_load_logo(self, target: QLabel) -> None:
        logo_path = (Path.cwd() / self._settings.logo_path).resolve()
        if logo_path.exists():
            pix = QPixmap(str(logo_path))
            if not pix.isNull():
                target.setPixmap(pix.scaled(48, 48, Qt.KeepAspectRatio, Qt.SmoothTransformation))
                return
        target.setText("LOGO")
        target.setStyleSheet("border: 1px dashed #999; color: #666;")

    def _kpi_card(self, title: str, value: str) -> Card:
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(6)
        t = muted(title)
        v = QLabel(value)
        v.setProperty("variant", "h1")
        layout.addWidget(t)
        layout.addWidget(v)
        layout.addStretch(1)
        card._value_label = v  # type: ignore[attr-defined]
        return card

    def refresh(self) -> None:
        if not self._session_factory:
            self.chart.plot_monthly(["-"], [0.0])
            return
        with self._session_factory() as session:
            svc = ReportsService(session)
            k = svc.kpis()
            df = svc.monthly_sales(months=6)

        self.kpi_sales._value_label.setText(f"{k['total_sales']:.2f}")  # type: ignore[attr-defined]
        self.kpi_invoices._value_label.setText(f"{int(k['total_invoices'])}")  # type: ignore[attr-defined]
        self.kpi_customers._value_label.setText(f"{int(k['customers'])}")  # type: ignore[attr-defined]
        self.kpi_revenue._value_label.setText(f"{k['revenue']:.2f}")  # type: ignore[attr-defined]

        if df.empty:
            self.chart.plot_monthly_bars(["-"], [0.0])
        else:
            labels = [str(x) for x in df["month"].tolist()]
            values = [float(x) for x in df["grand_total"].tolist()]
            self.chart.plot_monthly_bars(labels, values)

