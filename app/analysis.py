# app/analysis.py

from collections import Counter
from database import init_database, get_all_draws, update_weight, get_weights


def get_numbers(row):
    return [row["n1"], row["n2"], row["n3"], row["n4"], row["n5"]]


def calculate_frequency(draws):
    counter = Counter()

    for row in draws:
        counter.update(get_numbers(row))

    return {num: counter.get(num, 0) for num in range(1, 40)}


def calculate_miss(draws):
    miss = {}

    for num in range(1, 40):
        miss_count = 0

        for row in reversed(draws):
            nums = get_numbers(row)

            if num in nums:
                break

            miss_count += 1

        miss[num] = miss_count

    return miss


def normalize_scores(raw_scores):
    values = list(raw_scores.values())

    min_value = min(values)
    max_value = max(values)

    if max_value == min_value:
        return {k: 1.0 for k in raw_scores}

    normalized = {}

    for k, v in raw_scores.items():
        normalized[k] = 0.5 + (v - min_value) / (max_value - min_value)

    return normalized


def calculate_final_scores(frequency, miss):
    frequency_score = normalize_scores(frequency)
    miss_score = normalize_scores(miss)

    final_scores = {}

    for num in range(1, 40):
        final_scores[num] = (
            frequency_score[num] * 0.60 +
            miss_score[num] * 0.40
        )

    return final_scores, frequency_score, miss_score


def update_database_weights(final_scores):
    for num, score in final_scores.items():
        update_weight(num, score)


def print_top_results(frequency, miss, final_scores):
    print("===================================")
    print("539 AI Ultimate - Analysis")
    print("B-Model V2：Frequency + Miss")
    print("===================================")

    print("\n熱門號碼 TOP10（歷史出現次數）")
    for num, count in sorted(frequency.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{num:02d}：{count} 次")

    print("\n冷號 TOP10（目前遺漏期數）")
    for num, count in sorted(miss.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{num:02d}：已遺漏 {count} 期")

    print("\n綜合權重 TOP10")
    for num, score in sorted(final_scores.items(), key=lambda x: x[1], reverse=True)[:10]:
        print(f"{num:02d}：{score:.4f}")

    print("===================================")


def main():
    init_database()

    draws = get_all_draws()

    if not draws:
        print("資料庫沒有開獎資料，請先執行 update.py")
        return

    frequency = calculate_frequency(draws)
    miss = calculate_miss(draws)
    final_scores, frequency_score, miss_score = calculate_final_scores(frequency, miss)

    update_database_weights(final_scores)
    print_top_results(frequency, miss, final_scores)

    print(f"\n分析完成，共分析 {len(draws)} 期資料。")
    print("model_weights.final_weight 已更新。")


if __name__ == "__main__":
    main()