from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

FOLDERS = [
    "data",
    "database",
    "dashboard",
    "reports",
    "logs",
    "config",
]


def init_project():
    for folder in FOLDERS:
        (BASE_DIR / folder).mkdir(exist_ok=True)


def main():
    init_project()

    print("===================================")
    print(" 539 AI Ultimate V8")
    print(" 系統啟動成功")
    print("===================================")
    print(f"專案位置：{BASE_DIR}")
    print(f"啟動時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("===================================")


if __name__ == "__main__":
    main()