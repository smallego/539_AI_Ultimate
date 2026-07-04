# app/downloader.py

import webbrowser
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from core.logger import log

OFFICIAL_DOWNLOAD_PAGE = "https://www.taiwanlottery.com/lotto/history/result_download/"


def open_official_download_page():
    log("Opening Taiwan Lottery official history download page")
    webbrowser.open(OFFICIAL_DOWNLOAD_PAGE)
    print("已開啟台彩官方歷史資料下載頁")
    print("請下載今彩539年度 CSV 後，放入 data 資料夾。")


if __name__ == "__main__":
    open_official_download_page()