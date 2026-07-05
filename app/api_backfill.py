# app/api_backfill.py

from pathlib import Path
import sys
import requests
import urllib3
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.database import init_database, insert_draw, database_summary
from core.logger import log, log_error

API_URL = "https://api.taiwanlottery.com/TLCAPIWeB/Lottery/Daily539Result"

START_YEAR = 2024
START_MONTH = 1


def month_list(start_year, start_month):
    today = datetime.today()
    y = start_year
    m = start_month

    months = []

    while (y < today.year) or (y == today.year and m <= today.month):
        months.append(f"{y}-{m:02d}")

        m += 1
        if m > 12:
            y += 1
            m = 1

    return months


def fetch_month(month):
    urllib3.disable_warnings()

    params = {
        "period": "",
        "month": month,
        "endMonth": month,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.taiwanlottery.com/lotto/result/daily_cash",
    }

    log(f"Fetching Daily539 month: {month}")

    r = requests.get(
        API_URL,
        params=params,
        headers=headers,
        timeout=20,
        verify=False,
    )

    r.raise_for_status()
    data = r.json()

    if data.get("rtCode") != 0:
        raise ValueError(f"API error for {month}: {data}")

    return data["content"]["daily539Res"]


def backfill():
    try:
        init_database()

        before = database_summary()["draw_count"]

        months = month_list(START_YEAR, START_MONTH)

        total_api_rows = 0

        print("===================================")
        print("Daily539 API 歷史資料補齊開始")
        print(f"月份範圍：{months[0]} ~ {months[-1]}")
        print("===================================")

        for month in months:
            rows = fetch_month(month)
            total_api_rows += len(rows)

            for row in rows:
                period = str(row["period"])
                lottery_date = row["lotteryDate"][:10]
                numbers = row["drawNumberSize"]

                insert_draw(period, lottery_date, numbers)

            print(f"{month} 完成，API筆數：{len(rows)}")

        after = database_summary()["draw_count"]
        added = after - before

        log(f"Daily539 backfill completed. API rows={total_api_rows}, Added={added}, Total={after}")

        print("===================================")
        print("Daily539 API 歷史資料補齊完成")
        print(f"API 總筆數：{total_api_rows}")
        print(f"新增筆數：{added}")
        print(f"資料庫總筆數：{after}")
        print("===================================")

    except Exception as e:
        log_error("Daily539 API backfill failed", e)
        raise


if __name__ == "__main__":
    backfill()