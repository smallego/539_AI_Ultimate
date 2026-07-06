from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
WEB_DIR = BASE_DIR / "web"

DATABASE_DIR = BASE_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "history.db"

LOG_DIR = BASE_DIR / "logs"

MODEL_DIR = BASE_DIR / "models"
MODEL_FILE = MODEL_DIR / "weights.json"
VERSION_FILE = BASE_DIR / "VERSION"

DASHBOARD_DIR = BASE_DIR / "dashboard"
DASHBOARD_FILE = DASHBOARD_DIR / "Dashboard_V4.xlsx"

REPORT_DIR = BASE_DIR / "reports"
BACKTEST_REPORT = REPORT_DIR / "backtest_result.csv"

API_SCRIPTS = {
    "run_all": "app/main.py",
    "update": "app/api_update.py",
    "predict": "core/scorer.py",
    "backtest": "core/backtest.py",
    "dashboard": "dashboard/dashboard_v4.py",
}

BUILD_TIME = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def app_version():
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text(encoding="utf-8").strip()
    return "unknown"
