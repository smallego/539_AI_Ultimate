# app/update.py

import pandas as pd
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from app.database import init_database, insert_draw, database_summary
from core.logger import log, log_error

DATA_DIR = BASE_DIR / "data"


def import_csv_files():
    try:
        init_database()

        csv_files = sorted(DATA_DIR.glob("*.csv"))

        if not csv_files:
            log("No CSV files found in data folder", "WARNING")
            print("data 資料夾內找不到 CSV 檔案")
            return

        before = database_summary()["draw_count"]
        processed = 0

        log(f"CSV import started. Found {len(csv_files)} file(s).")

        for csv_file in csv_files:
            log(f"Reading CSV: {csv_file.name}")
            print(f"讀取：{csv_file.name}")

            df = pd.read_csv(csv_file)

            required_cols = ["開獎日期", "獎號1", "獎號2", "獎號3", "獎號4", "獎號5"]
            for col in required_cols:
                if col not in df.columns:
                    raise ValueError(f"{csv_file.name} 缺少欄位：{col}")

            for index, row in df.iterrows():
                draw_date = str(row["開獎日期"])
                numbers = [
                    int(row["獎號1"]),
                    int(row["獎號2"]),
                    int(row["獎號3"]),
                    int(row["獎號4"]),
                    int(row["獎號5"]),
                ]

                draw_no = draw_date.replace("/", "") + f"_{index + 1}"

                insert_draw(draw_no, draw_date, numbers)
                processed += 1

        after = database_summary()["draw_count"]
        added = after - before

        log(f"CSV import completed. Processed={processed}, Added={added}, Total={after}")

        print("===================================")
        print("CSV 匯入完成")
        print(f"處理筆數：{processed}")
        print(f"新增筆數：{added}")
        print(f"資料庫開獎總筆數：{after}")
        print("===================================")

    except Exception as e:
        log_error("CSV import failed", e)
        raise


if __name__ == "__main__":
    import_csv_files()