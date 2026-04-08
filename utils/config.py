from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Settings:
    company_name: str
    company_address: str
    company_phone: str
    logo_path: str
    currency_code: str
    currency_symbol: str
    tax_enabled: bool
    default_gst_rate: float
    db_filename: str
    ui_theme: str
    business_key: str


def _get(d: dict[str, Any], path: str, default: Any = None) -> Any:
    cur: Any = d
    for part in path.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return default
        cur = cur[part]
    return cur


def load_settings(settings_path: Path) -> Settings:
    raw = json.loads(settings_path.read_text(encoding="utf-8"))
    return Settings(
        company_name=str(_get(raw, "company.name", "Aftab Sahar Blue Cons.")),
        company_address=str(_get(raw, "company.address", "")),
        company_phone=str(_get(raw, "company.phone", "")),
        logo_path=str(_get(raw, "company.logo_path", "assets/logo.png")),
        currency_code=str(_get(raw, "currency.code", "PKR")),
        currency_symbol=str(_get(raw, "currency.symbol", "Rs")),
        tax_enabled=bool(_get(raw, "tax.enabled", True)),
        default_gst_rate=float(_get(raw, "tax.default_gst_rate", 18.0)),
        db_filename=str(_get(raw, "database.filename", "data/asb_erp.sqlite3")),
        ui_theme=str(_get(raw, "ui.theme", "dark")),
        business_key=str(_get(raw, "ui.business", "aftab_sahar")),
    )


def load_settings_raw(settings_path: Path) -> dict[str, Any]:
    return json.loads(settings_path.read_text(encoding="utf-8"))


def save_settings_raw(settings_path: Path, raw: dict[str, Any]) -> None:
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    settings_path.write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

