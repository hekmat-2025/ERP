from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    background: str = "#0f172a"
    sidebar: str = "#1e293b"
    card: str = "#334155"
    primary: str = "#3b82f6"
    primary_hover: str = "#2563eb"
    text: str = "#e2e8f0"
    muted_text: str = "#94a3b8"
    border: str = "#475569"
    danger: str = "#ef4444"
    success: str = "#22c55e"


def palette_for(theme: str) -> Palette:
    t = (theme or "dark").strip().lower()
    if t == "light":
        # Light blue + white + grey
        return Palette(
            background="#f3f6fb",
            sidebar="#ffffff",
            card="#ffffff",
            primary="#2563eb",
            primary_hover="#1d4ed8",
            text="#0f172a",
            muted_text="#475569",
            border="#cbd5e1",
            danger="#dc2626",
            success="#16a34a",
        )

    # Dark mode: luxury blue + gold accents
    return Palette(
        background="#071225",
        sidebar="#0b1b34",
        card="#102a4a",
        primary="#d4af37",  # gold
        primary_hover="#b8921f",
        text="#e2e8f0",
        muted_text="#a3b4cc",
        border="#1f3b63",
        danger="#ef4444",
        success="#22c55e",
    )


def build_qss(p: Palette | None = None) -> str:
    p = p or Palette()
    # Keep this as one string so it is easy to tune later.
    return f"""
/* Global */
QWidget {{
  background: {p.background};
  color: {p.text};
  font-size: 10.5pt;
}}

QMainWindow::separator {{
  background: {p.border};
  width: 1px;
  height: 1px;
}}

/* Cards */
QFrame[variant="card"] {{
  background: {p.card};
  border: 1px solid {p.border};
  border-radius: 10px;
}}

QLabel[variant="muted"] {{
  color: {p.muted_text};
}}

QLabel[variant="h1"] {{
  font-size: 16pt;
  font-weight: 600;
}}

QLabel[variant="h2"] {{
  font-size: 12.5pt;
  font-weight: 600;
}}

/* Sidebar */
QFrame[variant="sidebar"] {{
  background: {p.sidebar};
  border-right: 1px solid {p.border};
}}

QToolButton[variant="nav"] {{
  background: transparent;
  border: 1px solid transparent;
  border-radius: 10px;
  padding: 10px 12px;
  text-align: left;
  font-weight: 500;
}}

QToolButton[variant="nav"]:hover {{
  background: rgba(59, 130, 246, 0.12);
  border-color: rgba(59, 130, 246, 0.20);
}}

QToolButton[variant="nav"][active="true"] {{
  background: rgba(59, 130, 246, 0.22);
  border-color: rgba(59, 130, 246, 0.35);
}}

/* Topbar */
QFrame[variant="topbar"] {{
  background: rgba(30, 41, 59, 0.35);
  border-bottom: 1px solid {p.border};
}}

/* Inputs */
QLineEdit, QComboBox, QDateEdit, QDoubleSpinBox {{
  background: rgba(15, 23, 42, 0.55);
  border: 1px solid {p.border};
  border-radius: 10px;
  padding: 8px 10px;
  selection-background-color: {p.primary};
}}

QLineEdit:focus, QComboBox:focus, QDateEdit:focus, QDoubleSpinBox:focus {{
  border: 1px solid {p.primary};
}}

QComboBox::drop-down {{
  border: 0px;
  width: 26px;
}}

/* Buttons */
QPushButton {{
  border-radius: 10px;
  padding: 9px 12px;
  border: 1px solid {p.border};
  background: rgba(30, 41, 59, 0.65);
}}

QPushButton:hover {{
  background: rgba(30, 41, 59, 0.85);
}}

QPushButton:pressed {{
  background: rgba(30, 41, 59, 0.95);
}}

QPushButton[variant="primary"] {{
  background: {p.primary};
  border: 1px solid rgba(255, 255, 255, 0.12);
}}

QPushButton[variant="primary"]:hover {{
  background: {p.primary_hover};
}}

QPushButton[variant="danger"] {{
  background: rgba(239, 68, 68, 0.18);
  border: 1px solid rgba(239, 68, 68, 0.35);
}}

QPushButton[variant="danger"]:hover {{
  background: rgba(239, 68, 68, 0.28);
}}

/* Tables */
QTableWidget {{
  background: rgba(15, 23, 42, 0.35);
  border: 1px solid {p.border};
  border-radius: 10px;
  gridline-color: rgba(71, 85, 105, 0.35);
  selection-background-color: rgba(59, 130, 246, 0.25);
  selection-color: {p.text};
}}

QHeaderView::section {{
  background: rgba(30, 41, 59, 0.85);
  color: {p.text};
  padding: 8px 10px;
  border: 0px;
  border-right: 1px solid rgba(71, 85, 105, 0.55);
  font-weight: 600;
}}

QTableWidget::item {{
  padding: 8px;
}}

QTableCornerButton::section {{
  background: rgba(30, 41, 59, 0.85);
  border: 0px;
}}

/* Tabs */
QTabWidget::pane {{
  border: 1px solid {p.border};
  border-radius: 10px;
  top: -1px;
}}

QTabBar::tab {{
  background: rgba(30, 41, 59, 0.65);
  border: 1px solid {p.border};
  padding: 8px 12px;
  border-top-left-radius: 10px;
  border-top-right-radius: 10px;
  margin-right: 6px;
}}

QTabBar::tab:selected {{
  background: rgba(59, 130, 246, 0.22);
  border-color: rgba(59, 130, 246, 0.35);
}}

/* Scrollbars */
QScrollBar:vertical {{
  background: transparent;
  width: 12px;
  margin: 0px;
}}
QScrollBar::handle:vertical {{
  background: rgba(148, 163, 184, 0.35);
  border-radius: 6px;
  min-height: 24px;
}}
QScrollBar::handle:vertical:hover {{
  background: rgba(148, 163, 184, 0.50);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
  height: 0px;
}}

QScrollBar:horizontal {{
  background: transparent;
  height: 12px;
  margin: 0px;
}}
QScrollBar::handle:horizontal {{
  background: rgba(148, 163, 184, 0.35);
  border-radius: 6px;
  min-width: 24px;
}}
QScrollBar::handle:horizontal:hover {{
  background: rgba(148, 163, 184, 0.50);
}}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
  width: 0px;
}}
"""

