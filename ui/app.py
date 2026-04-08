from __future__ import annotations

import logging
import shutil
import sys
from pathlib import Path

from PyQt5.QtGui import QFont
from PyQt5.QtCore import QLocale
from PyQt5.QtWidgets import QApplication

from database.migrations import create_all
from database.session import session_factory, sqlite_engine
from models import customer as _customer  # noqa: F401  (ensure model import)
from models import invoice as _invoice  # noqa: F401
from models import invoice_item as _invoice_item  # noqa: F401
from models import product as _product  # noqa: F401
from ui.business_select import BusinessSelectDialog
from ui.main_window import MainWindow
from ui.theme import build_qss, palette_for
from utils.config import load_settings, load_settings_raw, save_settings_raw
from utils.logging_config import setup_logging
from utils.paths import app_root, config_dir, data_dir, logs_dir

logger = logging.getLogger(__name__)


def run_app() -> int:
    # Ensure a writable settings file exists in user data.
    settings_path = config_dir() / "settings.json"
    if not settings_path.exists():
        default_settings = app_root() / "config" / "settings.json"
        if default_settings.exists():
            shutil.copy2(default_settings, settings_path)
    raw = load_settings_raw(settings_path)
    raw.setdefault("ui", {})
    raw.setdefault("company", {})
    raw.setdefault("database", {})
    theme = str(raw["ui"].get("theme", "dark"))

    setup_logging(logs_dir())
    logger.info("Starting ASB ERP")

    app = QApplication(sys.argv)
    app.setApplicationName("Aftab Sahar Blue Cons. ERP")
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    app.setFont(QFont("Segoe UI", 10))
    app.setStyleSheet(build_qss(palette_for(theme)))

    dlg = BusinessSelectDialog(logo_path=(app_root() / "assets" / "logo.png"))
    if dlg.exec() != dlg.Accepted or not dlg.choice:
        return 0

    business = dlg.choice
    # Persist selection + map business → company name + database file
    raw["ui"]["business"] = business
    if business == "mts":
        raw["company"]["name"] = "M.T.S"
        raw["company"]["logo_path"] = "assets/mts_logo.png"
        raw["database"]["filename"] = "data/mts.sqlite3"
    else:
        raw["company"]["name"] = "Aftab Sahar Blue Cons."
        raw["company"]["logo_path"] = "assets/logo.png"
        raw["database"]["filename"] = "data/aftab_sahar.sqlite3"
    save_settings_raw(settings_path, raw)

    settings = load_settings(settings_path)

    # Re-apply theme (in case settings changed elsewhere)
    app.setStyleSheet(build_qss(palette_for(settings.ui_theme)))

    # Store database under user data directory even in packaged builds.
    db_path = (data_dir() / Path(settings.db_filename).name).resolve()
    engine = sqlite_engine(db_path)
    create_all(engine)
    SessionFactory = session_factory(engine)

    window = MainWindow(
        settings=settings,
        session_factory=SessionFactory,
        db_path=db_path,
        assets_root=app_root() / "assets",
    )
    window.show()
    return app.exec()

