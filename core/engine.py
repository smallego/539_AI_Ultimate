# core/engine.py

from pathlib import Path
import sqlite3
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config import FREQ_WEIGHT, MISS_WEIGHT, HOT_WEIGHT
from models.frequency import frequency_model, frequency_model_window, get_numbers
from models.miss import miss_model
from models.hot import hot_model

DB_PATH = BASE_DIR / "database" / "history.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_draws():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        SELECT *
        FROM draw_history
        ORDER BY draw_date ASC, draw_no ASC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def normalize(scores):
    values = list(scores.values())
    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        return {k: 1.0 for k in scores}

    return {
        k: 0.5 + (v - min_v) / (max_v - min_v)
        for k, v in scores.items()
    }


def build_final_weights():
    draws = get_all_draws()

    if not draws:
        raise ValueError("資料庫沒有開獎資料，請先執行 update.py")

    freq_raw = frequency_model(draws)
    miss_raw = miss_model(draws)
    hot_raw = hot_model(draws, recent_n=20)

    freq = frequency_model_window(draws)
    miss = normalize(miss_raw)
    hot = normalize(hot_raw)

    final = {}

    for num in range(1, 40):
        final[num] = (
            freq[num] * FREQ_WEIGHT +
            miss[num] * MISS_WEIGHT +
            hot[num] * HOT_WEIGHT
        )

    return {
        "draw_count": len(draws),
        "frequency": freq_raw,
        "miss": miss_raw,
        "hot": hot_raw,
        "final_weights": final,
    }


def print_top10(title, data):
    print(f"\n{title}")
    for num, value in sorted(data.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{num:02d}：{value}")


def main():
    result = build_final_weights()

    print("===================================")
    print("539 AI Ultimate - Engine")
    print("Engine Refactor V1")
    print("===================================")
    print(f"歷史資料期數：{result['draw_count']}")

    print_top10("Frequency TOP10", result["frequency"])
    print_top10("Miss TOP10", result["miss"])
    print_top10("Hot TOP10", result["hot"])

    print("\nFinal Weight TOP10")
    for num, score in sorted(result["final_weights"].items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{num:02d}：{score:.4f}")

    print("===================================")


if __name__ == "__main__":
    main()