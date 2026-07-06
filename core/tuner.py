# core/tuner.py

import random
import csv
from pathlib import Path
import sqlite3
from collections import Counter
from itertools import combinations
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from core.ai_scorer import ai_score

DB_PATH = BASE_DIR / "database" / "history.db"
REPORT_PATH = BASE_DIR / "reports" / "tuning_result.csv"

START_TRAIN_SIZE = 300
SET_COUNT = 5
BET_COST_PER_SET = 50
CANDIDATE_COUNT = 300


TEST_CONFIGS = [
    {"weight": 0.60, "co": 0.15, "balance": 0.10, "ai": 0.15},
    {"weight": 0.50, "co": 0.20, "balance": 0.10, "ai": 0.20},
    {"weight": 0.45, "co": 0.20, "balance": 0.10, "ai": 0.25},
    {"weight": 0.40, "co": 0.20, "balance": 0.15, "ai": 0.25},
    {"weight": 0.35, "co": 0.25, "balance": 0.15, "ai": 0.25},
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_all_draws():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM draw_history ORDER BY draw_date ASC, draw_no ASC")
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
    counter = Counter()
    for row in draws:
        counter.update(get_numbers(row))

    freq_raw = {n: counter.get(n, 0) for n in range(1, 40)}

    miss_raw = {}
    for n in range(1, 40):
        miss = 0
        for row in reversed(draws):
            if n in get_numbers(row):
                break
            miss += 1
        miss_raw[n] = miss

    hot_counter = Counter()
    for row in draws[-20:]:
        hot_counter.update(get_numbers(row))

    hot_raw = {n: hot_counter.get(n, 0) for n in range(1, 40)}

    freq = normalize(freq_raw)
    miss = normalize(miss_raw)
    hot = normalize(hot_raw)

    return {
        n: freq[n] * 0.45 + miss[n] * 0.35 + hot[n] * 0.20
        for n in range(1, 40)
    }


def build_cooccurrence(draws):
    pair_count = {}

    for row in draws:
        nums = get_numbers(row)
        for a, b in combinations(sorted(nums), 2):
            pair_count[(a, b)] = pair_count.get((a, b), 0) + 1

    max_count = max(pair_count.values()) if pair_count else 1
    return {pair: count / max_count for pair, count in pair_count.items()}


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


def generate_candidates(weights):
    candidates = set()
    attempts = 0

    while len(candidates) < CANDIDATE_COUNT and attempts < CANDIDATE_COUNT * 10:
        candidates.add(tuple(weighted_sample(weights)))
        attempts += 1

    return list(candidates)


def co_score(nums, co_matrix):
    pairs = list(combinations(sorted(nums), 2))
    return sum(co_matrix.get(pair, 0) for pair in pairs) / len(pairs)


def balance_score(nums):
    odd = sum(1 for n in nums if n % 2 == 1)
    low = sum(1 for n in nums if n <= 19)
    total = sum(nums)

    odd_score = 1.0 if odd in [2, 3] else 0.7
    low_score = 1.0 if low in [2, 3] else 0.7
    sum_score = 1.0 if 80 <= total <= 130 else 0.75

    return odd_score * 0.4 + low_score * 0.4 + sum_score * 0.2


def score_set(nums, weights, co_matrix, cfg):
    weight_score = sum(weights[n] for n in nums) / 5
    pair_score = co_score(nums, co_matrix)
    bal_score = balance_score(nums)
    ai = ai_score(nums)["ai_score"] / 100

    return (
        weight_score * cfg["weight"] +
        pair_score * cfg["co"] +
        bal_score * cfg["balance"] +
        ai * cfg["ai"]
    )


def too_similar(new_set, selected_sets, max_overlap=2):
    for old in selected_sets:
        if len(set(new_set) & set(old)) > max_overlap:
            return True
    return False


def select_best_sets(scored):
    selected = []

    for nums, score in scored:
        if not too_similar(nums, selected):
            selected.append(nums)

        if len(selected) >= SET_COUNT:
            break

    return selected


def prize_by_match(match):
    if match == 5:
        return 8000000
    if match == 4:
        return 20000
    if match == 3:
        return 300
    if match == 2:
        return 50
    return 0


def backtest_config(draws, cfg):
    total_cost = 0
    total_prize = 0
    hit2 = hit3 = hit4 = 0

    for i in range(START_TRAIN_SIZE, len(draws)):
        train = draws[:i]
        target = set(get_numbers(draws[i]))

        weights = build_weights(train)
        co_matrix = build_cooccurrence(train)
        candidates = generate_candidates(weights)

        scored = []
        for nums in candidates:
            score = score_set(nums, weights, co_matrix, cfg)
            scored.append((list(nums), score))

        scored.sort(key=lambda x: x[1], reverse=True)
        best_sets = select_best_sets(scored)

        period_prize = 0
        best_match = 0

        for nums in best_sets:
            match = len(set(nums) & target)
            best_match = max(best_match, match)
            period_prize += prize_by_match(match)

        total_cost += SET_COUNT * BET_COST_PER_SET
        total_prize += period_prize

        if best_match >= 2:
            hit2 += 1
        if best_match >= 3:
            hit3 += 1
        if best_match >= 4:
            hit4 += 1

    test_count = len(draws) - START_TRAIN_SIZE
    roi = (total_prize - total_cost) / total_cost * 100

    return {
        "roi": round(roi, 2),
        "hit2": round(hit2 / test_count * 100, 2),
        "hit3": round(hit3 / test_count * 100, 2),
        "hit4": round(hit4 / test_count * 100, 2),
        "cost": total_cost,
        "prize": total_prize,
    }


def main():
    draws = get_all_draws()

    if len(draws) <= START_TRAIN_SIZE:
        print("資料不足，無法調參")
        return

    results = []

    print("===================================")
    print("V2.1 Auto Tuning Started")
    print("===================================")

    for idx, cfg in enumerate(TEST_CONFIGS, start=1):
        print(f"測試第 {idx} 組權重：{cfg}")

        result = backtest_config(draws, cfg)

        row = {**cfg, **result}
        results.append(row)

        print(f"ROI={result['roi']}%, 2碼={result['hit2']}%, 3碼={result['hit3']}%")

    results.sort(key=lambda x: x["roi"], reverse=True)

    REPORT_PATH.parent.mkdir(exist_ok=True)

    with open(REPORT_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("===================================")
    print("Auto Tuning 完成")
    print("最佳權重：")
    print(results[0])
    print(f"報表輸出：{REPORT_PATH}")
    print("===================================")


if __name__ == "__main__":
    main()