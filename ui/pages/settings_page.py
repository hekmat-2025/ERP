from __future__ import annotations

import logging
from pathlib import Path

from PyQt5.QtWidgets import (
    QCheckBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from utils.config import Settings
from utils.config import load_settings_raw, save_settings_raw
from utils.paths import app_root
from ui.widgets import Card, PrimaryButton, h1, muted
from ui.theme import build_qss, palette_for

logger = logging.getLogger(__name__)


class SettingsPage(QWidget):
    def __init__(self, *, settings: Settings) -> None:
        super().__init__()
        self._settings = settings
        self._settings_path = app_root() / "config" / "settings.json"

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(14)

        header = Card()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 16, 16, 16)
        header_layout.addWidget(h1("Settings"))
        header_layout.addStretch(1)
        header_layout.addWidget(muted("Company, tax and branding"))
        root.addWidget(header)

        content = Card()
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.setSpacing(12)

        self.company_name = QLineEdit(settings.company_name)
        self.company_address = QLineEdit(settings.company_address)
        self.company_phone = QLineEdit(settings.company_phone)
        self.logo_path = QLineEdit(settings.logo_path)
        self.browse_logo_btn = QPushButton("Browse…")
        self.browse_logo_btn.clicked.connect(self._browse_logo)

        logo_row = QHBoxLayout()
        logo_row.addWidget(self.logo_path, 1)
        logo_row.addWidget(self.browse_logo_btn)

        self.currency = QComboBox()
        self.currency.addItem("Afghani (AFN)", ("AFN", "AFN"))
        self.currency.addItem("US Dollar (USD)", ("USD", "$"))
        # set current
        current = (settings.currency_code or "AFN").upper()
        for i in range(self.currency.count()):
            code, _sym = self.currency.itemData(i)
            if code == current:
                self.currency.setCurrentIndex(i)
                break

        self.theme = QComboBox()
        self.theme.addItem("Dark (Luxury Blue + Gold)", "dark")
        self.theme.addItem("Light (Blue + White + Grey)", "light")
        self.theme.setCurrentIndex(0 if (settings.ui_theme or "dark").lower() != "light" else 1)

        self.tax_enabled = QCheckBox("Enable GST/Tax")
        self.tax_enabled.setChecked(bool(settings.tax_enabled))
        self.default_gst = QDoubleSpinBox()
        self.default_gst.setMaximum(1000)
        self.default_gst.setDecimals(2)
        self.default_gst.setValue(float(settings.default_gst_rate))

        form = QFormLayout()
        form.addRow("Company name*", self.company_name)
        form.addRow("Company address", self.company_address)
        form.addRow("Company phone", self.company_phone)
        form.addRow("Logo path", logo_row)
        form.addRow("Currency", self.currency)
        form.addRow("Theme", self.theme)
        form.addRow("", self.tax_enabled)
        form.addRow("Default GST %", self.default_gst)
        content_layout.addLayout(form)

        actions = QHBoxLayout()
        actions.addStretch(1)
        self.save_btn = PrimaryButton("Save Settings")
        actions.addWidget(self.save_btn)
        content_layout.addLayout(actions)

        root.addWidget(content, 1)
        self.save_btn.clicked.connect(self._on_save)
        self.theme.currentIndexChanged.connect(self._apply_theme_live)

    def _browse_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Select logo image",
            str((app_root() / "assets").resolve()),
            "Images (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)",
        )
        if not path:
            return
        # Store as relative if inside app root (better for packaging)
        p = Path(path)
        try:
            rel = p.resolve().relative_to(app_root().resolve())
            self.logo_path.setText(rel.as_posix())
        except Exception:
            self.logo_path.setText(str(p))

    def _on_save(self) -> None:
        try:
            raw = load_settings_raw(self._settings_path)
            raw.setdefault("company", {})
            raw.setdefault("currency", {})
            raw.setdefault("tax", {})
            raw.setdefault("ui", {})

            name = (self.company_name.text() or "").strip()
            if not name:
                raise ValueError("Company name is required.")

            raw["company"]["name"] = name
            raw["company"]["address"] = (self.company_address.text() or "").strip()
            raw["company"]["phone"] = (self.company_phone.text() or "").strip()
            raw["company"]["logo_path"] = (self.logo_path.text() or "").strip() or "assets/logo.png"

            code, sym = self.currency.currentData()
            raw["currency"]["code"] = code
            raw["currency"]["symbol"] = sym

            raw["ui"]["theme"] = str(self.theme.currentData() or "dark")

            raw["tax"]["enabled"] = bool(self.tax_enabled.isChecked())
            raw["tax"]["default_gst_rate"] = float(self.default_gst.value())

            save_settings_raw(self._settings_path, raw)
            QMessageBox.information(
                self,
                "Saved",
                "Settings saved successfully.\n\nTheme was applied immediately. Restart is recommended to reload all pages.",
            )
        except Exception as e:  # noqa: BLE001
            logger.exception("Settings save failed")
            QMessageBox.critical(self, "Save failed", str(e))

    def _apply_theme_live(self) -> None:
        try:
            theme = str(self.theme.currentData() or "dark")
            app = self.window().windowHandle()
            from PyQt5.QtWidgets import QApplication

            QApplication.instance().setStyleSheet(build_qss(palette_for(theme)))
        except Exception:
            # Don't block UI if styling fails
            logger.exception("Live theme apply failed")

