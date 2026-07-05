# core/scorer.py

import random
from itertools import combinations
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

from config import (
    CANDIDATE_COUNT,
    SET_COUNT,
    MAX_OVERLAP,
    SCORER_WEIGHT,
    COOCCURRENCE_WEIGHT,
    BALANCE_WEIGHT,
)

from engine import build_final_weights, get_all_draws, get_numbers
from ai_scorer import ai_score


AI_WEIGHT = 0.25


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
        weight_score * SCORER_WEIGHT +
        co_score * COOCCURRENCE_WEIGHT +
        bal_score * BALANCE_WEIGHT +
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


def main():
    engine_result = build_final_weights()
    draws = get_all_draws()

    weights = engine_result["final_weights"]
    co_matrix = build_cooccurrence(draws)

    candidates = generate_candidate_sets(weights)

    scored = []
    for nums in candidates:
        score = score_set(nums, weights, co_matrix)
        scored.append((list(nums), score))

    scored.sort(key=lambda x: x[1], reverse=True)

    best_sets = select_best_sets(scored)

    print("===================================")
    print("539 AI Ultimate - Candidate Scorer")
    print("B-Model V2.0 + AI Score")
    print("===================================")
    print(f"候選組合數：{len(candidates)}")
    print("最佳 5 組：")
    print("===================================")

    for i, nums in enumerate(best_sets, start=1):
        score = score_set(nums, weights, co_matrix)
        ai = ai_score(nums)

        print(
            f"第 {i} 組：{' '.join(f'{n:02d}' for n in nums)}  "
            f"Final Score：{score:.4f}  AI Score：{ai['ai_score']}"
        )

    print("===================================")


if __name__ == "__main__":
    main()