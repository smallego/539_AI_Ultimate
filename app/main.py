# app/main.py

from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))
sys.path.append(str(BASE_DIR / "app"))
sys.path.append(str(BASE_DIR / "core"))
sys.path.append(str(BASE_DIR / "dashboard"))

from app.api_update import update_from_api
from core.backtest import run_backtest
from core.scorer import main as run_scorer
from dashboard_v2 import build_dashboard_v2
from core.logger import log, log_error


def run_pipeline():
    try:
        log("V3.1 pipeline started")

        log("Step 1: API update")
        update_from_api()

        log("Step 2: AI scorer")
        run_scorer()

        log("Step 3: Backtest")
        run_backtest()

        log("Step 4: Dashboard V2")
        build_dashboard_v2()

        log("V3.1 pipeline finished")
        print("===================================")
        print("V3.1 Pipeline 全部完成")
        print("===================================")

    except Exception as e:
        log_error("V3.1 pipeline failed", e)
        raise


if __name__ == "__main__":
    run_pipeline()