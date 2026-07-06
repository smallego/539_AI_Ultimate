# core/scorer.py

import random
import sqlite3
from itertools import combinations
from pathlib import Path
import sys
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config import (
    MODEL_VERSION,
    CANDIDATE_COUNT,
    SET_COUNT,
    MAX_OVERLAP,
    SCORER_WEIGHT,
    COOCCURRENCE_WEIGHT,
    BALANCE_WEIGHT,
)

from core.engine import build_final_weights, get_all_draws, get_numbers
from core.ai_scorer import ai_score

from core.learning import load_weights

MODEL = load_weights()

AI_WEIGHT = MODEL["AI_WEIGHT"]
DB_PATH = BASE_DIR / "database" / "history.db"
LAST_CANDIDATE_COUNT = 0

# 隞乩??批捆?????


def build_cooccurrence(draws):
    pair_count = {}

    for row in draws:
        nums = get_numbers(row)
        for a, b in combinations(sorted(nums), 2):
            pair_count[(a, b)] = pair_count.get((a, b), 0) + 1

    max_count = max(pair_count.values()) if pair_count else 1

    return {
        pair: count / max_count
        for pair, count in pair_count.items()
    }


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


def cooccurrence_score(nums, co_matrix):
    pairs = list(combinations(sorted(nums), 2))

    if not pairs:
        return 0

    total = 0
    for a, b in pairs:
        total += co_matrix.get((a, b), 0)

    return total / len(pairs)


def balance_score(nums):
    odd = sum(1 for n in nums if n % 2 == 1)
    low = sum(1 for n in nums if n <= 19)
    total_sum = sum(nums)

    odd_score = 1.0 if odd in [2, 3] else 0.7
    low_score = 1.0 if low in [2, 3] else 0.7
    sum_score = 1.0 if 80 <= total_sum <= 130 else 0.75

    return odd_score * 0.4 + low_score * 0.4 + sum_score * 0.2


def score_set(nums, weights, co_matrix):
    weight_score = sum(weights[n] for n in nums) / 5
    co_score = cooccurrence_score(nums, co_matrix)
    bal_score = balance_score(nums)

    ai_result = ai_score(nums)
    ai_score_normalized = ai_result["ai_score"] / 100

    final_score = (
        weight_score * MODEL["SCORER_WEIGHT"] +
        co_score * MODEL["COOCCURRENCE_WEIGHT"] +
        bal_score * MODEL["BALANCE_WEIGHT"] +
        ai_score_normalized * AI_WEIGHT
    )

    return final_score


def too_similar(new_set, selected_sets, max_overlap=MAX_OVERLAP):
    new_set = set(new_set)

    for old in selected_sets:
        if len(new_set & set(old)) > max_overlap:
            return True

    return False


def generate_candidate_sets(weights, count=CANDIDATE_COUNT):
    candidates = set()
    attempts = 0

    while len(candidates) < count and attempts < count * 10:
        nums = tuple(weighted_sample(weights, 5))
        candidates.add(nums)
        attempts += 1

    return list(candidates)


def select_best_sets(scored_sets):
    selected = []

    for nums, score in scored_sets:
        if not too_similar(nums, selected):
            selected.append(nums)

        if len(selected) >= SET_COUNT:
            break

    return selected


def ensure_prediction_history_schema():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        predict_date TEXT,
        created_at TEXT,
        model_version TEXT NOT NULL,
        set_no INTEGER NOT NULL,
        n1 INTEGER NOT NULL,
        n2 INTEGER NOT NULL,
        n3 INTEGER NOT NULL,
        n4 INTEGER NOT NULL,
        n5 INTEGER NOT NULL,
        final_score REAL,
        ai_score REAL
    )
    """)

    cur.execute("PRAGMA table_info(prediction_history)")
    columns = {row[1] for row in cur.fetchall()}

    if "created_at" not in columns:
        cur.execute("ALTER TABLE prediction_history ADD COLUMN created_at TEXT")
    if "predict_date" not in columns:
        cur.execute("ALTER TABLE prediction_history ADD COLUMN predict_date TEXT")
    if "final_score" not in columns:
        cur.execute("ALTER TABLE prediction_history ADD COLUMN final_score REAL")
    if "ai_score" not in columns:
        cur.execute("ALTER TABLE prediction_history ADD COLUMN ai_score REAL")

    conn.commit()
    conn.close()


def save_prediction_history(predictions):
    ensure_prediction_history_schema()

    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    predict_date = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    for item in predictions:
        nums = sorted([int(n) for n in item["numbers"]])
        cur.execute("""
        INSERT INTO prediction_history
        (
            predict_date,
            created_at,
            model_version,
            set_no,
            n1, n2, n3, n4, n5,
            final_score,
            ai_score
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            predict_date,
            created_at,
            MODEL_VERSION,
            item["set_no"],
            nums[0], nums[1], nums[2], nums[3], nums[4],
            item["final_score"],
            item["ai_score"],
        ))

    conn.commit()
    conn.close()


def run_prediction(save=True):
    global LAST_CANDIDATE_COUNT

    engine_result = build_final_weights()
    draws = get_all_draws()

    weights = engine_result["final_weights"]
    co_matrix = build_cooccurrence(draws)

    candidates = generate_candidate_sets(weights)
    LAST_CANDIDATE_COUNT = len(candidates)

    scored = []
    for nums in candidates:
        score = score_set(nums, weights, co_matrix)
        scored.append((list(nums), score))

    scored.sort(key=lambda x: x[1], reverse=True)

    best_sets = select_best_sets(scored)

    predictions = []
    for i, nums in enumerate(best_sets, start=1):
        score = score_set(nums, weights, co_matrix)
        ai = ai_score(nums)
        predictions.append({
            "set_no": i,
            "numbers": nums,
            "final_score": round(score, 4),
            "ai_score": float(ai["ai_score"]),
        })

    if save:
        save_prediction_history(predictions)

    return predictions


def main():
    predictions = run_prediction(save=True)

    print("===================================")
    print("539 AI Ultimate - Candidate Scorer")
    print("B-Model V2.0 + AI Score")
    print("===================================")
    print(f"Candidates: {LAST_CANDIDATE_COUNT}")
    print("Top 5 Sets")
    print("===================================")

    for item in predictions:
        print(
            f"Set {item['set_no']} {' '.join(f'{n:02d}' for n in item['numbers'])}  "
            f"Final Score: {item['final_score']:.4f}  AI Score: {item['ai_score']}"
        )

    print("===================================")

if __name__ == "__main__":
    main()
