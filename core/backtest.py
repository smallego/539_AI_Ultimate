# core/backtest.py

import random
import csv
from collections import Counter
from pathlib import Path
import sqlite3
import sys
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config import (
    MODEL_VERSION,
    START_TRAIN_SIZE,
    SET_COUNT,
    BET_COST_PER_SET,
)

DB_PATH = BASE_DIR / "database" / "history.db"
REPORT_DIR = BASE_DIR / "reports"
REPORT_PATH = REPORT_DIR / "backtest_result.csv"


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


def get_numbers(row):
    return [row["n1"], row["n2"], row["n3"], row["n4"], row["n5"]]


def normalize(scores):
    values = list(scores.values())
    min_v = min(values)
    max_v = max(values)

    if max_v == min_v:
        return {k: 1.0 for k in scores}

    return {k: 0.5 + (v - min_v) / (max_v - min_v) for k, v in scores.items()}


def build_weights(draws):
    freq_counter = Counter()
    for row in draws:
        freq_counter.update(get_numbers(row))

    freq_raw = {num: freq_counter.get(num, 0) for num in range(1, 40)}

    miss_raw = {}
    for num in range(1, 40):
        miss = 0
        for row in reversed(draws):
            if num in get_numbers(row):
                break
            miss += 1
        miss_raw[num] = miss

    hot_counter = Counter()
    for row in draws[-20:]:
        hot_counter.update(get_numbers(row))

    hot_raw = {num: hot_counter.get(num, 0) for num in range(1, 40)}

    freq = normalize(freq_raw)
    miss = normalize(miss_raw)
    hot = normalize(hot_raw)

    final = {}
    for num in range(1, 40):
        final[num] = freq[num] * 0.45 + miss[num] * 0.35 + hot[num] * 0.20

    return final


def weighted_sample(weights, k=5):
    pool = list(weights.keys())
    result = []

    for _ in range(k):
        total = sum(weights[n] for n in pool)
        r = random.uniform(0, total)
        upto = 0

        for n in pool:
            upto += weights[n]
            if upto >= r:
                result.append(n)
                pool.remove(n)
                break

    return sorted(result)


def too_similar(new_set, existing_sets, max_overlap=2):
    new_set = set(new_set)
    for old in existing_sets:
        if len(new_set & set(old)) > max_overlap:
            return True
    return False


def generate_sets(weights):
    sets = []
    attempts = 0

    while len(sets) < SET_COUNT and attempts < 3000:
        nums = weighted_sample(weights, 5)
        if not too_similar(nums, sets):
            sets.append(nums)
        attempts += 1

    while len(sets) < SET_COUNT:
        sets.append(sorted(random.sample(range(1, 40), 5)))

    return sets


def prize_by_match(match_count):
    if match_count == 5:
        return 8000000
    if match_count == 4:
        return 20000
    if match_count == 3:
        return 300
    if match_count == 2:
        return 50
    return 0


def save_results(rows):
    REPORT_DIR.mkdir(exist_ok=True)

    headers = [
        "model_version",
        "draw_no",
        "draw_date",
        "winning_numbers",
        "prediction_sets",
        "best_match",
        "period_cost",
        "period_prize",
        "period_roi",
        "cumulative_cost",
        "cumulative_prize",
        "cumulative_roi",
    ]

    with open(REPORT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)


def run_backtest():
    draws = get_all_draws()

    if len(draws) <= START_TRAIN_SIZE:
        print("資料不足，至少需要超過 300 期")
        return

    total_cost = 0
    total_prize = 0
    hit_2 = hit_3 = hit_4 = hit_5 = 0
    max_match_list = []
    losing_streak = 0
    max_losing_streak = 0
    result_rows = []

    for i in range(START_TRAIN_SIZE, len(draws)):
        train_draws = draws[:i]
        target_draw = draws[i]
        winning = set(get_numbers(target_draw))

        weights = build_weights(train_draws)
        prediction_sets = generate_sets(weights)

        best_match = 0
        period_prize = 0

        for nums in prediction_sets:
            match = len(set(nums) & winning)
            best_match = max(best_match, match)
            period_prize += prize_by_match(match)

        period_cost = SET_COUNT * BET_COST_PER_SET
        period_roi = (period_prize - period_cost) / period_cost * 100

        total_cost += period_cost
        total_prize += period_prize
        cumulative_roi = (total_prize - total_cost) / total_cost * 100

        max_match_list.append(best_match)

        if best_match >= 2:
            hit_2 += 1
        if best_match >= 3:
            hit_3 += 1
        if best_match >= 4:
            hit_4 += 1
        if best_match >= 5:
            hit_5 += 1

        if period_prize == 0:
            losing_streak += 1
            max_losing_streak = max(max_losing_streak, losing_streak)
        else:
            losing_streak = 0

        result_rows.append({
            "model_version": MODEL_VERSION,
            "draw_no": target_draw["draw_no"],
            "draw_date": target_draw["draw_date"],
            "winning_numbers": " ".join(f"{n:02d}" for n in sorted(winning)),
            "prediction_sets": " | ".join(
                " ".join(f"{n:02d}" for n in nums) for nums in prediction_sets
            ),
            "best_match": best_match,
            "period_cost": period_cost,
            "period_prize": period_prize,
            "period_roi": round(period_roi, 2),
            "cumulative_cost": total_cost,
            "cumulative_prize": total_prize,
            "cumulative_roi": round(cumulative_roi, 2),
        })

    save_results(result_rows)

    test_count = len(result_rows)
    roi = (total_prize - total_cost) / total_cost * 100
    avg_match = sum(max_match_list) / len(max_match_list)

    hit2_rate = hit_2 / test_count * 100
    hit3_rate = hit_3 / test_count * 100
    hit4_rate = hit_4 / test_count * 100
    hit5_rate = hit_5 / test_count * 100

    from core.learning import learn, save_learning_result
    new_weights = learn(roi)
    save_learning_result(
        MODEL_VERSION,
        roi,
        hit2_rate,
        hit3_rate,
        hit4_rate,
        hit5_rate,
        avg_match,
        new_weights,
    )

    print("AI Learning 更新完成")
    print(new_weights)
    print("===================================")
    print("539 AI Ultimate - Rolling Backtest")
    print(MODEL_VERSION)
    print("===================================")
    print(f"實際回測期數：{test_count}")
    print(f"總投注成本：{total_cost:,} 元")
    print(f"總模擬回收：{total_prize:,} 元")
    print(f"ROI：{roi:.2f}%")
    print("===================================")
    print(f"2碼以上命中率：{hit_2 / test_count * 100:.2f}%")
    print(f"3碼以上命中率：{hit_3 / test_count * 100:.2f}%")
    print(f"4碼以上命中率：{hit_4 / test_count * 100:.2f}%")
    print(f"5碼命中率：{hit_5 / test_count * 100:.4f}%")
    print(f"平均最佳命中數：{avg_match:.2f}")
    print(f"最大連敗期數：{max_losing_streak}")
    print("===================================")
    print(f"CSV 已輸出：{REPORT_PATH}")
    print("===================================")


if __name__ == "__main__":
    run_backtest()
