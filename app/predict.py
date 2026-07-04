# app/predict.py

import random
from database import init_database, get_all_draws, get_weights, insert_prediction

MODEL_VERSION = "B-Model V2.0"


def build_weights_from_database():
    rows = get_weights()
    weights = {}

    for row in rows:
        num = int(row["number"])
        weight = float(row["final_weight"])

        if weight <= 0:
            weight = 0.1

        weights[num] = weight

    return weights


def weighted_sample_without_replacement(weights, k=5):
    pool = list(weights.keys())
    result = []

    for _ in range(k):
        total_weight = sum(weights[n] for n in pool)
        r = random.uniform(0, total_weight)

        upto = 0
        chosen = None

        for n in pool:
            upto += weights[n]
            if upto >= r:
                chosen = n
                break

        result.append(chosen)
        pool.remove(chosen)

    return sorted(result)


def too_similar(new_set, existing_sets, max_overlap=2):
    new_set = set(new_set)

    for old_set in existing_sets:
        overlap = len(new_set & set(old_set))
        if overlap > max_overlap:
            return True

    return False


def generate_prediction_sets(weights, set_count=5):
    sets = []
    used_sets = set()
    attempts = 0

    while len(sets) < set_count and attempts < 3000:
        nums = weighted_sample_without_replacement(weights, 5)
        key = tuple(nums)

        if key not in used_sets and not too_similar(nums, sets, max_overlap=2):
            sets.append(nums)
            used_sets.add(key)

        attempts += 1

    while len(sets) < set_count:
        nums = sorted(random.sample(range(1, 40), 5))
        key = tuple(nums)

        if key not in used_sets:
            sets.append(nums)
            used_sets.add(key)

    return sets


def print_weight_top10(weights):
    print("目前 Final Weight TOP10：")
    for num, weight in sorted(weights.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{num:02d}：{weight:.4f}")


def main():
    init_database()

    draws = get_all_draws()

    if not draws:
        print("資料庫沒有開獎資料，請先執行 update.py")
        return

    weights = build_weights_from_database()
    prediction_sets = generate_prediction_sets(weights, 5)

    insert_prediction(MODEL_VERSION, prediction_sets)

    print("===================================")
    print("539 AI Ultimate - Prediction")
    print(f"模型版本：{MODEL_VERSION}")
    print(f"歷史資料期數：{len(draws)}")
    print("===================================")

    print_weight_top10(weights)

    print("\n下一期預測 5 組：")
    print("===================================")

    for idx, nums in enumerate(prediction_sets, start=1):
        print(f"第 {idx} 組：{' '.join(f'{n:02d}' for n in nums)}")

    print("===================================")
    print("預測已寫入 prediction_history")


if __name__ == "__main__":
    main()