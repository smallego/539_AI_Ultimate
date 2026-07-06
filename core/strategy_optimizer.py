import csv
import sqlite3
from pathlib import Path

from core.explainer import explain_prediction

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "history.db"
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


def risk_label(score):
    if score >= 70:
        return "Low"
    if score >= 45:
        return "Medium"
    return "High"


def risk_component(label):
    return {"Low": 88, "Medium": 58, "High": 28}.get(label, 50)


def connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def row_numbers(row):
    return [int(row[f"n{i}"]) for i in range(1, 6)]


def latest_predictions(limit=5):
    if not DB_PATH.exists():
        return []

    conn = connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT created_at
            FROM prediction_history
            ORDER BY id DESC
            LIMIT 1
            """
        )
        latest = cur.fetchone()
        if latest is None:
            return []

        created_at = latest["created_at"]
        if created_at:
            cur.execute(
                """
                SELECT *
                FROM prediction_history
                WHERE created_at = ?
                ORDER BY set_no ASC, id ASC
                """,
                (created_at,),
            )
        else:
            cur.execute(
                """
                SELECT *
                FROM prediction_history
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            )
        rows = cur.fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        conn.close()

    return [
        {
            "id": row["id"],
            "created_at": row["created_at"] or row["predict_date"] or "",
            "model_version": row["model_version"],
            "set_no": row["set_no"],
            "numbers": row_numbers(row),
            "final_score": row["final_score"],
            "ai_score": row["ai_score"],
        }
        for row in rows
    ]


def learning_rows(limit=20):
    if not DB_PATH.exists():
        return []

    conn = connection()
    cur = conn.cursor()
    try:
        cur.execute(
            """
            SELECT *
            FROM learning_history
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
    except sqlite3.Error:
        rows = []
    finally:
        conn.close()
    return rows


def backtest_rows(limit=80):
    if not BACKTEST_REPORT.exists():
        return []
    with BACKTEST_REPORT.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))[-limit:]


def explain_signals():
    reports = [explain_prediction(prediction) for prediction in latest_predictions()]
    return {
        "decision": average([report["decisionScore"] for report in reports], default=50),
        "explain": average([sum(abs(reason["score"]) for reason in report["reasons"]) for report in reports], default=35),
        "confidence": average([report["confidence"] for report in reports], default=50),
        "reports": reports,
    }


def backtest_metrics():
    rows = backtest_rows()
    if not rows:
        return {"roi": 0, "hit": 0, "risk": "Medium", "confidence": 45}

    roi = safe_float(rows[-1].get("cumulative_roi"))
    hit2 = average([1 if safe_float(row.get("best_match")) >= 2 else 0 for row in rows], default=0) * 100
    losses = sum(1 for row in rows[-20:] if safe_float(row.get("period_prize")) <= 0)
    risk = "High" if roi < -70 or losses >= 18 else "Medium" if roi < -35 or losses >= 12 else "Low"
    confidence = clamp(45 + len(rows) * 0.4 + hit2 * 0.2)
    return {"roi": round(roi, 2), "hit": round(hit2, 2), "risk": risk, "confidence": round(confidence, 2)}


def learning_metrics():
    rows = learning_rows()
    if not rows:
        return {"roi": 0, "hit": 0, "risk": "Medium", "confidence": 40}

    roi = average([row["roi"] for row in rows[:10]], default=0)
    hit = average([row["hit2"] for row in rows[:10]], default=0)
    risk = "High" if roi < -70 or hit < 18 else "Medium" if roi < -35 or hit < 32 else "Low"
    confidence = clamp(40 + len(rows) * 2 + hit * 0.2)
    return {"roi": round(roi, 2), "hit": round(hit, 2), "risk": risk, "confidence": round(confidence, 2)}


def prediction_metrics():
    predictions = latest_predictions()
    if not predictions:
        return {"roi": 0, "hit": 0, "risk": "Medium", "confidence": 40}

    ai = average([item["ai_score"] for item in predictions], default=50)
    final = average([safe_float(item["final_score"]) for item in predictions], default=0.5) * 100
    roi = clamp(((ai + final) / 2) - 100, -100, 100)
    hit = clamp(ai * 0.48)
    risk = "High" if ai < 45 else "Medium" if ai < 68 else "Low"
    confidence = clamp((ai + final) / 2)
    return {"roi": round(roi, 2), "hit": round(hit, 2), "risk": risk, "confidence": round(confidence, 2)}


def normalize_roi(roi):
    return clamp(roi + 100)


def strategy_score(item):
    return round(
        normalize_roi(item["roi"]) * 0.22
        + item["hitRate"] * 0.20
        + item["decisionScore"] * 0.18
        + item["explainScore"] * 0.14
        + risk_component(item["risk"]) * 0.13
        + item["confidence"] * 0.13,
        2,
    )


def strategy_reasons(item):
    reasons = [
        f"ROI normalized to {normalize_roi(item['roi']):.2f}",
        f"Hit rate contributes {item['hitRate']:.2f}",
        f"Decision score contributes {item['decisionScore']:.2f}",
        f"Explain score contributes {item['explainScore']:.2f}",
        f"Risk is {item['risk']}",
        f"Confidence is {item['confidence']:.2f}",
    ]
    return reasons


def evaluate_strategies():
    explain = explain_signals()
    backtest = backtest_metrics()
    learning = learning_metrics()
    prediction = prediction_metrics()

    base = [
        {
            "id": "backtest",
            "name": "Backtest Strategy",
            "roi": backtest["roi"],
            "hitRate": backtest["hit"],
            "risk": backtest["risk"],
            "confidence": backtest["confidence"],
            "decisionScore": clamp(explain["decision"] * 0.5 + normalize_roi(backtest["roi"]) * 0.5),
            "explainScore": clamp(explain["explain"]),
        },
        {
            "id": "learning",
            "name": "Learning Strategy",
            "roi": learning["roi"],
            "hitRate": learning["hit"],
            "risk": learning["risk"],
            "confidence": learning["confidence"],
            "decisionScore": clamp(explain["decision"] * 0.45 + normalize_roi(learning["roi"]) * 0.55),
            "explainScore": clamp(explain["explain"] * 0.8 + learning["hit"] * 0.2),
        },
        {
            "id": "prediction",
            "name": "Prediction Strategy",
            "roi": prediction["roi"],
            "hitRate": prediction["hit"],
            "risk": prediction["risk"],
            "confidence": prediction["confidence"],
            "decisionScore": clamp(explain["decision"]),
            "explainScore": clamp(explain["explain"]),
        },
    ]

    hybrid = {
        "id": "hybrid",
        "name": "Hybrid Strategy",
        "roi": round(average([item["roi"] for item in base], default=0), 2),
        "hitRate": round(average([item["hitRate"] for item in base], default=0), 2),
        "risk": "Medium",
        "confidence": round(average([item["confidence"] for item in base], default=50), 2),
        "decisionScore": round(average([item["decisionScore"] for item in base], default=50), 2),
        "explainScore": round(average([item["explainScore"] for item in base], default=50), 2),
    }
    hybrid["risk"] = risk_label(average([risk_component(item["risk"]) for item in base], default=50))

    strategies = base + [hybrid]
    for item in strategies:
        item["overallScore"] = strategy_score(item)
        item["reasons"] = strategy_reasons(item)
        item["radar"] = {
            "ROI": normalize_roi(item["roi"]),
            "Hit Rate": item["hitRate"],
            "Risk": risk_component(item["risk"]),
            "Decision": item["decisionScore"],
            "Confidence": item["confidence"],
            "Explain": item["explainScore"],
        }

    return strategies


def compare_strategies():
    strategies = evaluate_strategies()
    return {
        "labels": ["ROI", "Hit Rate", "Risk", "Decision", "Confidence", "Explain"],
        "strategies": strategies,
    }


def rank_strategies():
    return sorted(evaluate_strategies(), key=lambda item: item["overallScore"], reverse=True)


def recommend_best_strategy():
    ranking = rank_strategies()
    if not ranking:
        return {
            "strategy": "-",
            "overallScore": 0,
            "risk": "-",
            "confidence": 0,
            "reasons": ["No strategy data available."],
        }

    best = ranking[0]
    return {
        "strategy": best["name"],
        "overallScore": best["overallScore"],
        "risk": best["risk"],
        "confidence": best["confidence"],
        "reasons": best["reasons"],
    }
