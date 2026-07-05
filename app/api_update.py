# app/api_update.py

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


def get_month_range():
    today = datetime.today()
    roc_year = today.year - 1911
    month = today.month

    month_str = f"{today.year}-{month:02d}"

    return month_str, month_str


def fetch_daily539():
    urllib3.disable_warnings()

    start_month, end_month = get_month_range()

    params = {
        "period": "",
        "month": start_month,
        "endMonth": end_month,
    }

    headers = {
        "User-Agent": "Mozilla/5.0",
        "Referer": "https://www.taiwanlottery.com/lotto/result/daily_cash",
    }

    log(f"Fetching Daily539 API: {params}")

    r = requests.get(
        API_URL,
        params=params,
        headers=headers,
        timeout=20,
        verify=False,
    )

    r.raise_for_status()
    return r.json()


def update_from_api():
    try:
        init_database()

        before = database_summary()["draw_count"]

        data = fetch_daily539()

        if data.get("rtCode") != 0:
            raise ValueError(f"API error: {data}")

        rows = data["content"]["daily539Res"]

        added_count = 0

        for row in rows:
            period = str(row["period"])
            lottery_date = row["lotteryDate"][:10]
            numbers = row["drawNumberSize"]

            insert_draw(period, lottery_date, numbers)
            added_count += 1

        after = database_summary()["draw_count"]
        actual_added = after - before

        log(f"Daily539 API update completed. API rows={len(rows)}, Added={actual_added}, Total={after}")

        print("===================================")
        print("Daily539 API 更新完成")
        print(f"API 筆數：{len(rows)}")
        print(f"新增筆數：{actual_added}")
        print(f"資料庫總筆數：{after}")
        print("===================================")

    except Exception as e:
        log_error("Daily539 API update failed", e)
        raise


if __name__ == "__main__":
    update_from_api()