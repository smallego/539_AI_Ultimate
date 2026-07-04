# core/logger.py

from pathlib import Path
from datetime import datetime
import traceback

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_DIR = BASE_DIR / "logs"


def get_log_path():
    LOG_DIR.mkdir(exist_ok=True)
    today = datetime.now().strftime("%Y-%m-%d")
    return LOG_DIR / f"{today}.log"


def log(message, level="INFO"):
    log_path = get_log_path()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    line = f"[{now}] {level:<5} {message}"

    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")

    print(line)


def log_error(message, error=None):
    log(message, level="ERROR")

    if error is not None:
        log_path = get_log_path()
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(str(error) + "\n")
            f.write(traceback.format_exc() + "\n")