from pathlib import Path
import sqlite3
import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "history.db"


def trend_data(last_n=100):
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql(
        """
        SELECT draw_no, draw_date, n1, n2, n3, n4, n5
        FROM draw_history
        ORDER BY draw_date DESC, draw_no DESC
        LIMIT ?
        """,
        conn,
        params=(last_n,),
    )
    conn.close()

    rows = []
    for _, r in df.iloc[::-1].iterrows():
        nums = [int(r["n1"]), int(r["n2"]), int(r["n3"]), int(r["n4"]), int(r["n5"])]
        odd = sum(n % 2 for n in nums)
        low = sum(n <= 20 for n in nums)
        rows.append({
            "期別": str(r["draw_no"]),
            "日期": str(r["draw_date"]),
            "和值": sum(nums),
            "跨度": max(nums) - min(nums),
            "奇數": odd,
            "偶數": 5 - odd,
            "小號": low,
            "大號": 5 - low,
        })

    return pd.DataFrame(rows)
