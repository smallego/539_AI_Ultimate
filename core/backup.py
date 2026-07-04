# core/backup.py

from pathlib import Path
from datetime import datetime
import shutil
from logger import log, log_error

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "history.db"
BACKUP_DIR = BASE_DIR / "database" / "backup"


def backup_database():
    try:
        if not DB_PATH.exists():
            log("Database backup skipped: history.db not found", "WARNING")
            return False

        BACKUP_DIR.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = BACKUP_DIR / f"history_{timestamp}.db"

        shutil.copy2(DB_PATH, backup_path)

        log(f"Database backup completed: {backup_path}")
        return True

    except Exception as e:
        log_error("Database backup failed", e)
        raise


if __name__ == "__main__":
    backup_database()