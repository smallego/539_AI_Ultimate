# app/gui.py

import subprocess
import os
from pathlib import Path
import tkinter as tk
from tkinter import messagebox

BASE_DIR = Path(__file__).resolve().parent.parent
DASHBOARD_V2 = BASE_DIR / "dashboard" / "Dashboard_V2.xlsx"


def run_command(command):
    try:
        subprocess.run(
            command,
            cwd=BASE_DIR,
            shell=True,
            check=True
        )
        messagebox.showinfo("完成", f"執行完成：{command}")
    except subprocess.CalledProcessError:
        messagebox.showerror("錯誤", f"執行失敗：{command}")


def update_api():
    run_command("python app\\api_update.py")


def run_ai_scorer():
    run_command("python core\\scorer.py")


def run_backtest():
    run_command("python core\\backtest.py")


def run_tuner():
    run_command("python core\\tuner.py")


def build_dashboard():
    run_command("python dashboard\\dashboard_v2.py")


def open_dashboard():
    if DASHBOARD_V2.exists():
        os.startfile(DASHBOARD_V2)
    else:
        messagebox.showwarning("找不到檔案", "請先建立 Dashboard V2")


def run_all():
    run_command("run_all.bat")


def main():
    root = tk.Tk()
    root.title("539 AI Ultimate Professional")
    root.geometry("420x430")
    root.resizable(False, False)

    title = tk.Label(
        root,
        text="539 AI Ultimate Professional",
        font=("Arial", 16, "bold")
    )
    title.pack(pady=20)

    buttons = [
        ("更新官方 API", update_api),
        ("AI 今日預測", run_ai_scorer),
        ("執行回測", run_backtest),
        ("Auto Tuning", run_tuner),
        ("建立 Dashboard V2", build_dashboard),
        ("開啟 Dashboard V2", open_dashboard),
        ("一鍵 Run All", run_all),
        ("離開", root.destroy),
    ]

    for text, command in buttons:
        btn = tk.Button(
            root,
            text=text,
            width=28,
            height=2,
            command=command
        )
        btn.pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()