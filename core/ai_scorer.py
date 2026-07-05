# core/ai_scorer.py

from features import analyze_set


def score_sum(total):
    if 80 <= total <= 130:
        return 100
    if 70 <= total < 80 or 130 < total <= 140:
        return 80
    if 60 <= total < 70 or 140 < total <= 150:
        return 60
    return 40


def score_span(span):
    if 20 <= span <= 36:
        return 100
    if 15 <= span < 20:
        return 80
    if 10 <= span < 15:
        return 60
    return 40


def score_odd_even(odd, even):
    if (odd, even) in [(2, 3), (3, 2)]:
        return 100
    if (odd, even) in [(1, 4), (4, 1)]:
        return 70
    return 50


def score_low_high(low, high):
    if (low, high) in [(2, 3), (3, 2)]:
        return 100
    if (low, high) in [(1, 4), (4, 1)]:
        return 70
    return 50


def score_consecutive(consecutive):
    if consecutive == 0:
        return 90
    if consecutive == 1:
        return 100
    if consecutive == 2:
        return 70
    return 40


def score_same_tail(same_tail):
    if same_tail == 0:
        return 100
    if same_tail == 1:
        return 85
    if same_tail == 2:
        return 60
    return 40


def score_ac(ac):
    if 5 <= ac <= 7:
        return 100
    if ac in [4, 8]:
        return 80
    if ac in [3, 9]:
        return 60
    return 40


def ai_score(nums):
    f = analyze_set(nums)

    scores = {
        "sum_score": score_sum(f["sum"]),
        "span_score": score_span(f["span"]),
        "odd_even_score": score_odd_even(f["odd"], f["even"]),
        "low_high_score": score_low_high(f["low"], f["high"]),
        "consecutive_score": score_consecutive(f["consecutive"]),
        "same_tail_score": score_same_tail(f["same_tail"]),
        "ac_score": score_ac(f["ac"]),
    }

    final_score = (
        scores["sum_score"] * 0.20 +
        scores["span_score"] * 0.15 +
        scores["odd_even_score"] * 0.15 +
        scores["low_high_score"] * 0.15 +
        scores["consecutive_score"] * 0.10 +
        scores["same_tail_score"] * 0.10 +
        scores["ac_score"] * 0.15
    )

    return {
        "numbers": f["numbers"],
        "features": f,
        "scores": scores,
        "ai_score": round(final_score, 2),
    }


def print_ai_score(nums):
    result = ai_score(nums)

    print("===================================")
    print("AI Set Scorer V2.0")
    print("===================================")
    print("號碼：", " ".join(f"{n:02d}" for n in result["numbers"]))
    print(f"AI Score：{result['ai_score']}")

    print("\n特徵：")
    for k, v in result["features"].items():
        if k != "numbers":
            print(f"{k}: {v}")

    print("\n分數：")
    for k, v in result["scores"].items():
        print(f"{k}: {v}")

    print("===================================")


if __name__ == "__main__":
    print_ai_score([2, 10, 15, 31, 37])