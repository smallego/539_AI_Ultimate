from pathlib import Path
import sqlite3
import pandas as pd
from collections import Counter

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "history.db"


def load_history():
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql("""
        SELECT *
        FROM draw_history
        ORDER BY draw_date DESC
    """, conn)

    conn.close()

    return df


def basic_statistics(last_n=100):

    df = load_history().head(last_n)

    numbers = []

    sums = []
    spans = []

    odd = even = low = high = 0

    for _, r in df.iterrows():

        nums = [
            int(r["n1"]),
            int(r["n2"]),
            int(r["n3"]),
            int(r["n4"]),
            int(r["n5"])
        ]

        numbers.extend(nums)

        sums.append(sum(nums))
        spans.append(max(nums) - min(nums))

        odd += sum(n % 2 for n in nums)
        even += sum(n % 2 == 0 for n in nums)

        low += sum(n <= 20 for n in nums)
        high += sum(n > 20 for n in nums)

    counter = Counter(numbers)

    hot = counter.most_common(10)

    cold = sorted(counter.items(), key=lambda x: x[1])[:10]

    return {
        "draws": len(df),
        "avg_sum": round(sum(sums) / len(sums), 2),
        "avg_span": round(sum(spans) / len(spans), 2),
        "odd": odd,
        "even": even,
        "low": low,
        "high": high,
        "hot": hot,
        "cold": cold,
    }


if __name__ == "__main__":

    s = basic_statistics()

    print()

    print("===== Analytics =====")

    print(f"Draws      : {s['draws']}")
    print(f"Avg Sum    : {s['avg_sum']}")
    print(f"Avg Span   : {s['avg_span']}")

    print()

    print("Hot Number")

    for n, c in s["hot"]:
        print(n, c)

    print()

    print("Cold Number")

    for n, c in s["cold"]:
        print(n, c)