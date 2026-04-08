from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class BackupResult:
    backup_path: Path


class BackupService:
    def __init__(self, db_path: Path, backups_dir: Path) -> None:
        self._db_path = db_path
        self._backups_dir = backups_dir
        self._backups_dir.mkdir(parents=True, exist_ok=True)

    def backup_now(self) -> BackupResult:
        if not self._db_path.exists():
            raise FileNotFoundError("Database file not found to backup.")
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst = self._backups_dir / f"asb_erp_backup_{ts}.sqlite3"
        shutil.copy2(self._db_path, dst)
        return BackupResult(backup_path=dst)

    def restore_from(self, backup_path: Path) -> None:
        if not backup_path.exists():
            raise FileNotFoundError("Backup file not found.")
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(backup_path, self._db_path)

