# app/parser.py

from pathlib import Path
import sys
import re
import requests
import urllib3
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from core.logger import log, log_error

LATEST_URL = "https://www.taiwanlottery.com/lotto/result/daily_cash/"
CACHE_DIR = BASE_DIR / "data" / "cache"
CACHE_PATH = CACHE_DIR / "latest_result.html"


def download_latest_html():
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

        log("Downloading Taiwan Lottery latest result page")

        urllib3.disable_warnings()

        headers = {"User-Agent": "Mozilla/5.0"}

        response = requests.get(
            LATEST_URL,
            headers=headers,
            timeout=20,
            verify=False
        )
        response.raise_for_status()

        CACHE_PATH.write_text(response.text, encoding="utf-8")
        log(f"Latest result HTML saved: {CACHE_PATH}")

        return response.text

    except Exception as e:
        log_error("Download latest result page failed", e)
        raise


def parse_539_latest(html):
    soup = BeautifulSoup(html, "lxml")

    section = soup.find(id="m539")

    if section is None:
        debug_path = CACHE_DIR / "m539_debug.html"
        debug_path.write_text(html, encoding="utf-8")
        raise ValueError(f"找不到 id=m539，已輸出：{debug_path}")

    text = section.get_text(" ", strip=True)

    date_match = re.search(r"\d{4}/\d{1,2}/\d{1,2}", text)
    draw_date = date_match.group(0) if date_match else None

    draw_no_match = re.search(r"\d{8,12}", text)
    draw_no = draw_no_match.group(0) if draw_no_match else None

    nums = re.findall(r"\b([1-3]?\d)\b", text)

    numbers = []
    for n in nums:
        value = int(n)
        if 1 <= value <= 39 and value not in numbers:
            numbers.append(value)

    winning_numbers = numbers[:5]

    if len(winning_numbers) < 5:
        debug_path = CACHE_DIR / "m539_text_debug.txt"
        debug_path.write_text(text, encoding="utf-8")
        raise ValueError(f"解析號碼不足5個，已輸出：{debug_path}")

    return {
        "game": "今彩539",
        "draw_no": draw_no,
        "draw_date": draw_date,
        "numbers": winning_numbers,
    }


def main():
    html = download_latest_html()

    print("===================================")
    print("HTML 下載完成，先不解析")
    print(f"檔案位置：{CACHE_PATH}")
    print(f"HTML 長度：{len(html)}")
    print("===================================")


if __name__ == "__main__":
    main()