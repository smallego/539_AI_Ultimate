from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.append(str(BASE_DIR / "app"))
sys.path.append(str(BASE_DIR / "core"))

from app.api_update import update_from_api
from core.backtest import run_backtest
from core.scorer import main as run_scorer
from dashboard.dashboard_v4 import build_dashboard_v4
from core.logger import log, log_error


def run_pipeline():

    steps = [
        ("API 更新", update_from_api),
        ("AI 預測", run_scorer),
        ("回測", run_backtest),
        ("Dashboard", build_dashboard_v4),
    ]

    for name, func in steps:

        print("=" * 60)
        print(f"開始：{name}")

        try:

            func()

            print(f"完成：{name}")

        except Exception as e:

            import traceback

            print()
            print(f"{name} 發生錯誤")
            traceback.print_exc()

            raise

    print("=" * 60)
    print("全部完成")

   


if __name__ == "__main__":
    run_pipeline()
