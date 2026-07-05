import os
import sys
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.append(str(BASE_DIR / "app"))
sys.path.append(str(BASE_DIR / "core"))

DASHBOARD_V4 = BASE_DIR / "dashboard" / "Dashboard_V4.xlsx"


def safe_run(name, func):
    try:
        func()
        messagebox.showinfo("完成", f"{name} 完成")
    except Exception as e:
        messagebox.showerror("錯誤", f"{name} 失敗\n\n{e}")


def update_api():
    from app.api_update import update_from_api
    safe_run("更新官方 API", update_from_api)


def run_ai_scorer():
    from core.scorer import main
    safe_run("AI 今日預測", main)


def run_backtest():
    from core.backtest import run_backtest
    safe_run("執行回測", run_backtest)


def run_tuner():
    from core.tuner import main
    safe_run("Auto Tuning", main)


def build_dashboard():
    from dashboard.dashboard_v4 import build_dashboard_v4
    safe_run("建立 Dashboard V4", build_dashboard_v4)


def open_dashboard():
    if DASHBOARD_V4.exists():
        os.startfile(DASHBOARD_V4)
    else:
        messagebox.showwarning("找不到檔案", "請先建立 Dashboard V4")


def run_all():
    from app.main import run_pipeline
    safe_run("一鍵 Run All", run_pipeline)


def main():
    root = tk.Tk()
    root.title("539 AI Ultimate Professional")
    root.geometry("420x430")
    root.resizable(False, False)

    title = tk.Label(root, text="539 AI Ultimate Professional", font=("Arial", 16, "bold"))
    title.pack(pady=20)

    buttons = [
        ("更新官方 API", update_api),
        ("AI 今日預測", run_ai_scorer),
        ("執行回測", run_backtest),
        ("Auto Tuning", run_tuner),
        ("建立 Dashboard V4", build_dashboard),
        ("開啟 Dashboard V4", open_dashboard),
        ("一鍵 Run All", run_all),
        ("離開", root.destroy),
    ]

    for text, command in buttons:
        tk.Button(root, text=text, width=28, height=2, command=command).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
