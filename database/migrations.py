from __future__ import annotations

import logging

from sqlalchemy.engine import Engine
from sqlalchemy import text

from database.base import Base

logger = logging.getLogger(__name__)


def create_all(engine: Engine) -> None:
    logger.info("Ensuring database schema exists.")
    Base.metadata.create_all(engine)
    _ensure_column(engine, table="products", column="image_path", ddl="ALTER TABLE products ADD COLUMN image_path VARCHAR(500) NOT NULL DEFAULT ''")


def _ensure_column(engine: Engine, *, table: str, column: str, ddl: str) -> None:
    try:
        with engine.begin() as conn:
            cols = conn.execute(text(f"PRAGMA table_info({table})")).fetchall()
            names = {row[1] for row in cols}  # row[1] = name
            if column not in names:
                logger.info("Applying migration: %s.%s", table, column)
                conn.execute(text(ddl))
    except Exception:  # noqa: BLE001
        logger.exception("Migration check failed for %s.%s", table, column)

