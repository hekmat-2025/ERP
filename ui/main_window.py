from __future__ import annotations

import logging
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMessageBox,
    QStackedWidget,
    QStatusBar,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
)
from sqlalchemy.orm import Session, sessionmaker

from services.backup_service import BackupService
from ui.pages.customers_page import CustomersPage
from ui.pages.dashboard_page import DashboardPage
from ui.pages.invoice_page import InvoicePage
from ui.pages.products_page import ProductsPage
from ui.pages.reports_page import ReportsPage
from ui.pages.settings_page import SettingsPage
from utils.config import Settings
from utils.paths import app_root
from ui.widgets.sidebar import NavItem, Sidebar
from ui.widgets.topbar import Topbar
from ui.widgets.page_scroll import PageScrollArea
from ui.business_select import BusinessSelectDialog
from utils.config import load_settings, load_settings_raw, save_settings_raw
from database.migrations import create_all
from database.session import session_factory as build_session_factory, sqlite_engine
from utils.paths import config_dir, data_dir

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    def __init__(
        self,
        *,
        settings: Settings,
        session_factory: sessionmaker[Session],
        db_path: Path,
        assets_root: Path,
    ) -> None:
        super().__init__()
        self._settings = settings
        self._session_factory = session_factory
        self._db_path = db_path
        self._assets_root = assets_root

        self.setWindowTitle("Aftab Sahar Blue Cons. ERP")
        self.resize(1200, 720)

        icon_path = assets_root / "app.ico"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Shell layout (MANDATORY): Topbar + (Sidebar | Content)
        root = QWidget(self)
        self.setCentralWidget(root)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        topbar = Topbar(app_title="Aftab Sahar Blue Cons. ERP", user_text="Construction ERP")
        root_layout.addWidget(topbar)

        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(0, 0, 0, 0)
        body_layout.setSpacing(0)
        root_layout.addWidget(body, 1)

        logo = (app_root() / self._settings.logo_path).resolve()
        items = [
            NavItem("dashboard", "Dashboard", (app_root() / "assets" / "icons" / "dashboard.svg")),
            NavItem("invoices", "Invoices", (app_root() / "assets" / "icons" / "invoice.svg")),
            NavItem("customers", "Customers", (app_root() / "assets" / "icons" / "customers.svg")),
            NavItem("products", "Products", (app_root() / "assets" / "icons" / "products.svg")),
            NavItem("reports", "Reports", (app_root() / "assets" / "icons" / "reports.svg")),
            NavItem("settings", "Settings", (app_root() / "assets" / "icons" / "settings.svg")),
        ]
        switch_icon = (app_root() / "assets" / "icons" / "switch.svg").resolve()
        self._sidebar = Sidebar(
            logo_path=logo,
            title="ASB Construction",
            items=items,
            switch_icon_path=switch_icon if switch_icon.exists() else None,
        )
        self._sidebar.nav_changed.connect(self._on_nav)
        self._sidebar.switch_business.connect(self._on_switch_business)
        body_layout.addWidget(self._sidebar)

        self._stack = QStackedWidget()
        body_layout.addWidget(self._stack, 1)

        self._pages: dict[str, QWidget] = {}
        self._page_wrappers: dict[str, PageScrollArea] = {}
        self._rebuild_pages(settings=settings, session_factory=session_factory)

        self.setStatusBar(QStatusBar(self))
        self.statusBar().showMessage("Ready")

        self._on_nav("dashboard")
        self._update_scroll_policies()

    def _on_switch_business(self) -> None:
        settings_path = config_dir() / "settings.json"
        raw = load_settings_raw(settings_path)
        raw.setdefault("ui", {})
        raw.setdefault("company", {})
        raw.setdefault("database", {})

        dlg = BusinessSelectDialog(logo_path=(app_root() / "assets" / "logo.png"))
        if dlg.exec() != dlg.Accepted or not dlg.choice:
            return

        business = dlg.choice
        raw["ui"]["business"] = business
        if business == "mts":
            raw["company"]["name"] = "M.T.S"
            raw["company"]["logo_path"] = "assets/mts_logo.png"
            raw["database"]["filename"] = "mts.sqlite3"
        else:
            raw["company"]["name"] = "Aftab Sahar Blue Cons."
            raw["company"]["logo_path"] = "assets/logo.png"
            raw["database"]["filename"] = "aftab_sahar.sqlite3"
        save_settings_raw(settings_path, raw)
        # Hot-switch: reload settings, re-init DB, rebuild pages, update sidebar header.
        self._settings = load_settings(settings_path)
        self._db_path = (data_dir() / Path(self._settings.db_filename).name).resolve()
        engine = sqlite_engine(self._db_path)
        create_all(engine)
        self._session_factory = build_session_factory(engine)

        self._rebuild_pages(settings=self._settings, session_factory=self._session_factory)
        logo = (app_root() / self._settings.logo_path).resolve()
        self._sidebar.set_header(logo_path=logo, title=self._settings.company_name)
        self.statusBar().showMessage(f"Switched business to {self._settings.company_name}", 4000)
        self._on_nav("dashboard")

    def _register_page(self, key: str, widget: QWidget) -> None:
        self._pages[key] = widget
        wrapper = PageScrollArea(widget)
        self._page_wrappers[key] = wrapper
        self._stack.addWidget(wrapper)

    def _rebuild_pages(self, *, settings: Settings, session_factory: sessionmaker[Session]) -> None:
        # Remove previous pages from stack
        while self._stack.count():
            w = self._stack.widget(0)
            self._stack.removeWidget(w)
            w.deleteLater()

        self._pages.clear()
        self._page_wrappers.clear()

        self._register_page(
            "dashboard",
            DashboardPage(settings=settings, assets_root=self._assets_root, session_factory=session_factory),
        )
        self._register_page("invoices", InvoicePage(settings=settings, session_factory=session_factory))
        self._register_page("products", ProductsPage(session_factory=session_factory))
        self._register_page("customers", CustomersPage(session_factory=session_factory))
        self._register_page("reports", ReportsPage(session_factory=session_factory))
        self._register_page("settings", SettingsPage(settings=settings))

    def _on_nav(self, key: str) -> None:
        if key not in self._pages:
            return
        self._sidebar.set_active(key)
        self._stack.setCurrentWidget(self._page_wrappers[key])

    def resizeEvent(self, event) -> None:  # noqa: D401
        super().resizeEvent(event)
        self._update_scroll_policies()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        self._update_scroll_policies()

    def _update_scroll_policies(self) -> None:
        """
        - In fullscreen/maximized: hide scrollbars (still scroll via wheel/touchpad).
        - In smaller windows: enable vertical scrollbars as-needed.
        """
        state = self.windowState()
        fullscreen_or_max = bool(state & Qt.WindowFullScreen) or bool(state & Qt.WindowMaximized)
        for w in self._page_wrappers.values():
            if fullscreen_or_max:
                w.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            else:
                w.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)

    def _backup_service(self) -> BackupService:
        backups_dir = self._db_path.parent / "backups"
        return BackupService(self._db_path, backups_dir)

    def _on_backup(self) -> None:
        try:
            result = self._backup_service().backup_now()
            QMessageBox.information(self, "Backup created", f"Backup saved:\n{result.backup_path}")
        except Exception as e:  # noqa: BLE001
            logger.exception("Backup failed")
            QMessageBox.critical(self, "Backup failed", str(e))

    def _on_restore(self) -> None:
        backup_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select backup file to restore",
            str((self._db_path.parent / "backups").resolve()),
            "SQLite DB (*.sqlite3 *.db);;All Files (*)",
        )
        if not backup_path:
            return

        if (
            QMessageBox.question(
                self,
                "Confirm Restore",
                "This will replace the current database with the selected backup.\n\n"
                "A safety backup of the current DB will be created first.\n\nProceed?",
            )
            != QMessageBox.StandardButton.Yes
        ):
            return

        try:
            svc = self._backup_service()
            safety = svc.backup_now()
            svc.restore_from(Path(backup_path))
            QMessageBox.information(
                self,
                "Restored",
                "Database restored successfully.\n\n"
                "For safety and to reload all data, the application will now close.\n\n"
                f"Safety backup saved:\n{safety.backup_path}",
            )
            QApplication.quit()
        except Exception as e:  # noqa: BLE001
            logger.exception("Restore failed")
            QMessageBox.critical(self, "Restore failed", str(e))

