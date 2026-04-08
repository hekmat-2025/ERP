from __future__ import annotations

import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

logger = logging.getLogger(__name__)


def sqlite_engine(db_path: Path) -> Engine:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    url = f"sqlite+pysqlite:///{db_path.as_posix()}"
    engine = create_engine(
        url,
        echo=False,
        future=True,
        connect_args={"check_same_thread": False},
    )
    return engine


def session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

