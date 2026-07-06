import csv
import json
import sqlite3
from collections import Counter
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "history.db"
MODEL_FILE = BASE_DIR / "models" / "weights.json"
BACKTEST_REPORT = BASE_DIR / "reports" / "backtest_result.csv"


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def average(values, default=0):
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return default
    return sum(clean) / len(clean)


def safe_float(value, default=0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def star_rating(score):
    filled = int(round(score / 20))
    filled = max(0, min(5, filled))
    return "*" * filled + "-" * (5 - filled)


def confidence_value(score, cold_overlap, trend_component):
    penalty = cold_overlap * 4
    if trend_component < 60:
        penalty += 8
    return round(clamp(score - penalty), 2)


def risk_label(score, cold_overlap, backtest_component):
    if score < 50 or cold_overlap >= 3 or backtest_component < 35:
        return "High"
    if score < 72 or cold_overlap >= 1 or backtest_component < 55:
        return "Medium"
    return "Low"


def number_fields():
    return ["n1", "n2", "n3", "n4", "n5"]


def row_numbers(row):
    return [int(row[field]) for field in number_fields()]


def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def recent_draws(limit=30):
    if not DB_PATH.exists():
        return []

    conn = connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT *
            FROM draw_history
            ORDER BY draw_date DESC, draw_no DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
    except sqlite3.Error:
        rows = []
    conn.close()
    return list(reversed(rows))


def latest_learning():
    if not DB_PATH.exists():
        return {}

    conn = connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT *
            FROM learning_history
            ORDER BY id DESC
            LIMIT 1
            """
        )
        row = cur.fetchone()
    except sqlite3.Error:
        row = None
    conn.close()

    if row is None:
        return {}

    try:
        weights = json.loads(row["weights_json"] or "{}")
    except json.JSONDecodeError:
        weights = {}

    return {
        "roi": row["roi"],
        "hit2": row["hit2"],
        "hit3": row["hit3"],
        "hit4": row["hit4"],
        "hit5": row["hit5"],
        "avg_match": row["avg_match"],
        "weights": weights,
        "created_at": row["created_at"],
        "model_version": row["model_version"],
    }


def current_weights():
    if not MODEL_FILE.exists():
        return {}
    try:
        return json.loads(MODEL_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return {}


def read_backtest_rows(limit=40):
    if not BACKTEST_REPORT.exists():
        return []

    with BACKTEST_REPORT.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    return rows[-limit:]


def backtest_signal():
    rows = read_backtest_rows()
    if not rows:
        return {
            "component": 50,
            "roi_delta": 0,
            "recent_roi": None,
            "hit2_rate": None,
            "improving": False,
        }

    midpoint = max(1, len(rows) // 2)
    first = rows[:midpoint]
    second = rows[midpoint:]
    first_roi = average([safe_float(row.get("period_roi")) for row in first], default=0)
    second_roi = average([safe_float(row.get("period_roi")) for row in second], default=0)
    roi_delta = second_roi - first_roi
    hit2_rate = average([1 if safe_float(row.get("best_match")) >= 2 else 0 for row in second], default=0) * 100
    recent_roi = safe_float(rows[-1].get("cumulative_roi"))

    component = clamp(50 + roi_delta * 0.35 + (hit2_rate - 35) * 0.35)
    return {
        "component": round(component, 2),
        "roi_delta": round(roi_delta, 2),
        "recent_roi": round(recent_roi, 2),
        "hit2_rate": round(hit2_rate, 2),
        "improving": roi_delta > 0,
    }


def hot_cold_signal(numbers, draws):
    counter = Counter()
    for row in draws:
        counter.update(row_numbers(row))

    counts = [{"number": number, "count": counter.get(number, 0)} for number in range(1, 40)]
    hot = sorted(counts, key=lambda item: (-item["count"], item["number"]))[:10]
    cold = sorted(counts, key=lambda item: (item["count"], item["number"]))[:10]
    hot_numbers = {item["number"] for item in hot}
    cold_numbers = {item["number"] for item in cold}
    hot_overlap = sorted(set(numbers) & hot_numbers)
    cold_overlap = sorted(set(numbers) & cold_numbers)
    component = clamp(55 + len(hot_overlap) * 8 - len(cold_overlap) * 7)
    return {
        "component": round(component, 2),
        "hot": hot,
        "cold": cold,
        "hot_overlap": hot_overlap,
        "cold_overlap": cold_overlap,
    }


def trend_signal(numbers, draws):
    if not draws:
        return {
            "component": 50,
            "sum_value": sum(numbers),
            "span_value": max(numbers) - min(numbers),
            "avg_sum": None,
            "avg_span": None,
            "sum_ok": False,
            "span_ok": False,
        }

    sums = [sum(row_numbers(row)) for row in draws]
    spans = [max(row_numbers(row)) - min(row_numbers(row)) for row in draws]
    sum_value = sum(numbers)
    span_value = max(numbers) - min(numbers)
    avg_sum = average(sums)
    avg_span = average(spans)
    sum_tolerance = 15
    span_tolerance = 6
    sum_ok = abs(sum_value - avg_sum) <= sum_tolerance
    span_ok = abs(span_value - avg_span) <= span_tolerance
    component = average([100 if sum_ok else 55, 100 if span_ok else 55], default=60)
    return {
        "component": round(component, 2),
        "sum_value": sum_value,
        "span_value": span_value,
        "avg_sum": round(avg_sum, 2),
        "avg_span": round(avg_span, 2),
        "sum_ok": sum_ok,
        "span_ok": span_ok,
    }


def learning_signal(learning, weights):
    roi = learning.get("roi")
    hit2 = learning.get("hit2")
    hit3 = learning.get("hit3")
    hit4 = learning.get("hit4")
    model_weights = learning.get("weights") or weights or {}

    roi_component = clamp((safe_float(roi, -70) + 100))
    hit_component = clamp(average([
        safe_float(hit2),
        safe_float(hit3) * 1.7,
        safe_float(hit4) * 3.0,
    ], default=35))
    component = average([roi_component, hit_component], default=50)
    strongest = None
    if model_weights:
        strongest = max(model_weights.items(), key=lambda item: safe_float(item[1]))

    return {
        "component": round(component, 2),
        "roi": roi,
        "hit2": hit2,
        "hit3": hit3,
        "hit4": hit4,
        "strongest_weight": strongest,
    }


def explain_prediction(prediction):
    numbers = sorted(int(number) for number in prediction.get("numbers", []))
    draws = recent_draws(limit=30)
    learning = latest_learning()
    weights = current_weights()
    backtest = backtest_signal()
    hot_cold = hot_cold_signal(numbers, draws)
    trend = trend_signal(numbers, draws)
    learning_info = learning_signal(learning, weights)

    ai_component = clamp(safe_float(prediction.get("ai_score"), 50))
    final_component = clamp(safe_float(prediction.get("final_score"), 0.5) * 100)
    decision_score = round(
        ai_component * 0.24
        + final_component * 0.18
        + learning_info["component"] * 0.18
        + backtest["component"] * 0.15
        + trend["component"] * 0.13
        + hot_cold["component"] * 0.12,
        2,
    )
    confidence = confidence_value(decision_score, len(hot_cold["cold_overlap"]), trend["component"])
    risk = risk_label(decision_score, len(hot_cold["cold_overlap"]), backtest["component"])

    reasons = []
    for number in hot_cold["hot_overlap"][:3]:
        count = next((item["count"] for item in hot_cold["hot"] if item["number"] == number), 0)
        reasons.append({
            "type": "Hot Number",
            "title": f"{number:02d} is hot in the last 30 draws ({count} hits)",
            "score": 8,
        })

    for number in hot_cold["cold_overlap"][:3]:
        count = next((item["count"] for item in hot_cold["cold"] if item["number"] == number), 0)
        reasons.append({
            "type": "Cold Number",
            "title": f"{number:02d} is cold in the last 30 draws ({count} hits)",
            "score": -7,
        })

    if learning_info["strongest_weight"]:
        key, value = learning_info["strongest_weight"]
        reasons.append({
            "type": "Learning",
            "title": f"{key} is the strongest current learning weight ({safe_float(value):.4f})",
            "score": 12 if learning_info["component"] >= 60 else 4,
        })
    else:
        reasons.append({
            "type": "Learning",
            "title": "No learning weights available yet",
            "score": 0,
        })

    reasons.append({
        "type": "Trend",
        "title": "Sum matches the recent average" if trend["sum_ok"] else "Sum is outside the recent average band",
        "score": 6 if trend["sum_ok"] else -4,
    })
    reasons.append({
        "type": "Trend",
        "title": "Span matches the recent average" if trend["span_ok"] else "Span is outside the recent average band",
        "score": 6 if trend["span_ok"] else -4,
    })
    reasons.append({
        "type": "Backtest",
        "title": "Recent ROI is improving" if backtest["improving"] else "Recent ROI is not improving",
        "score": 10 if backtest["improving"] else -4,
    })
    reasons.append({
        "type": "AI",
        "title": f"AI score contributes {ai_component:.2f}",
        "score": round((ai_component - 50) * 0.18, 2),
    })
    reasons.append({
        "type": "Final Score",
        "title": f"Final score normalizes to {final_component:.2f}",
        "score": round((final_component - 50) * 0.12, 2),
    })

    return {
        "predictionId": prediction.get("id"),
        "setNo": prediction.get("set_no"),
        "numbers": numbers,
        "modelVersion": prediction.get("model_version"),
        "createdAt": prediction.get("created_at"),
        "decisionScore": decision_score,
        "stars": star_rating(decision_score),
        "confidence": confidence,
        "risk": risk,
        "components": {
            "aiScore": round(ai_component, 2),
            "finalScore": round(final_component, 2),
            "learning": learning_info["component"],
            "backtest": backtest["component"],
            "trend": trend["component"],
            "hotCold": hot_cold["component"],
        },
        "reasons": reasons,
        "timeline": [
            {"step": "Prediction", "title": "Prediction set loaded from prediction_history"},
            {"step": "Decision", "title": "AI score and final score normalized"},
            {"step": "Learning", "title": "Latest learning result and weights evaluated"},
            {"step": "Backtest", "title": "Recent backtest ROI and hit rate evaluated"},
            {"step": "Explain", "title": "Reason scores combined into explainable report"},
        ],
        "context": {
            "trend": trend,
            "learning": learning_info,
            "backtest": backtest,
            "hotOverlap": hot_cold["hot_overlap"],
            "coldOverlap": hot_cold["cold_overlap"],
        },
    }
