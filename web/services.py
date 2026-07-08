import sqlite3
import json
import subprocess
import csv
from collections import Counter
from datetime import datetime

from core.ai_signal import calculate_ai_signal
from core.auto_model_loop import apply_if_improved as run_auto_model_loop
from core.auto_model_loop import status as auto_model_loop_status
from core.explainer import explain_prediction
from core.strategy_optimizer import compare_strategies, rank_strategies, recommend_best_strategy
from web.cache import cache_stats, performance_stats

from web.config import (
    API_SCRIPTS,
    BACKTEST_REPORT,
    BASE_DIR,
    BUILD_TIME,
    DASHBOARD_FILE,
    DATABASE_PATH,
    MODEL_FILE,
    app_version,
)

try:
    from config import MODEL_VERSION
except Exception:
    MODEL_VERSION = "unknown"

LATEST_DRAW_SQL = """
SELECT *
FROM draw_history
ORDER BY date(draw_date) DESC, draw_no DESC
LIMIT 1
"""


def number_fields():
    return ["n1", "n2", "n3", "n4", "n5"]


def row_numbers(row):
    return [int(row[field]) for field in number_fields()]


def parse_draw_date(value):
    if not value:
        return datetime.min

    text = str(value).strip()
    if not text:
        return datetime.min

    text = text.split("T", 1)[0].split(" ", 1)[0]
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return datetime.min


def draw_sort_key(row):
    return (parse_draw_date(row["draw_date"]), str(row["draw_no"]))


def choose_latest_draw(sql_latest, rows):
    parsed_rows = [row for row in rows if parse_draw_date(row["draw_date"]) != datetime.min]
    if not parsed_rows:
        return sql_latest

    parsed_latest = max(parsed_rows, key=draw_sort_key)
    if sql_latest is None:
        return parsed_latest
    return max([sql_latest, parsed_latest], key=draw_sort_key)


def get_connection():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_prediction_history_schema():
    if not DATABASE_PATH.exists():
        return

    conn = get_connection()
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


def ensure_learning_history_schema():
    if not DATABASE_PATH.exists():
        return

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS learning_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        model_version TEXT,
        roi REAL,
        hit2 REAL,
        hit3 REAL,
        hit4 REAL,
        hit5 REAL,
        avg_match REAL,
        weights_json TEXT
    )
    """)
    conn.commit()
    conn.close()


def format_draw(row):
    if row is None:
        return {}

    numbers = row_numbers(row)
    return {
        "drawNo": row["draw_no"],
        "drawDate": row["draw_date"],
        "numbers": numbers,
        "sum": sum(numbers),
        "span": max(numbers) - min(numbers),
        "odd": sum(1 for number in numbers if number % 2 == 1),
        "even": sum(1 for number in numbers if number % 2 == 0),
        "low": sum(1 for number in numbers if number <= 19),
        "high": sum(1 for number in numbers if number >= 20),
    }


def format_prediction(row):
    created_at = row["created_at"] or row["predict_date"] or ""
    return {
        "id": row["id"],
        "created_at": created_at,
        "model_version": row["model_version"],
        "set_no": row["set_no"],
        "numbers": row_numbers(row),
        "final_score": row["final_score"],
        "ai_score": row["ai_score"],
    }


def parse_weights(value):
    if not value:
        return {}
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return {}


def current_weights():
    if not MODEL_FILE.exists():
        return {}
    with MODEL_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def format_learning(row):
    return {
        "id": row["id"],
        "created_at": row["created_at"],
        "model_version": row["model_version"],
        "roi": row["roi"],
        "hit2": row["hit2"],
        "hit3": row["hit3"],
        "hit4": row["hit4"],
        "hit5": row["hit5"],
        "avg_match": row["avg_match"],
        "weights": parse_weights(row["weights_json"]),
    }


def latest_learning():
    if not DATABASE_PATH.exists():
        return {}

    ensure_learning_history_schema()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT *
    FROM learning_history
    ORDER BY id DESC
    LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    return format_learning(row) if row else {}


def learning_history(limit=50):
    if not DATABASE_PATH.exists():
        return []

    ensure_learning_history_schema()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT *
    FROM learning_history
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [format_learning(row) for row in rows]


def learning_weights(limit=20):
    rows = list(reversed(learning_history(limit=limit)))
    return {
        "current": current_weights(),
        "history": rows,
    }


def latest_predictions():
    if not DATABASE_PATH.exists():
        return []

    ensure_prediction_history_schema()
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT created_at
    FROM prediction_history
    ORDER BY id DESC
    LIMIT 1
    """)
    latest = cur.fetchone()
    if latest is None:
        conn.close()
        return []

    created_at = latest["created_at"]
    if created_at:
        cur.execute("""
        SELECT *
        FROM prediction_history
        WHERE created_at = ?
        ORDER BY set_no ASC, id ASC
        """, (created_at,))
    else:
        cur.execute("""
        SELECT *
        FROM prediction_history
        ORDER BY id DESC
        LIMIT 5
        """)

    rows = cur.fetchall()
    conn.close()
    return [format_prediction(row) for row in rows]


def prediction_history(limit=50):
    if not DATABASE_PATH.exists():
        return []

    ensure_prediction_history_schema()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
    SELECT *
    FROM prediction_history
    ORDER BY id DESC
    LIMIT ?
    """, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [format_prediction(row) for row in rows]


def prediction_by_id(prediction_id):
    if not DATABASE_PATH.exists():
        return None

    ensure_prediction_history_schema()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT *
        FROM prediction_history
        WHERE id = ?
        LIMIT 1
        """,
        (prediction_id,),
    )
    row = cur.fetchone()
    conn.close()
    return format_prediction(row) if row else None


def explain_latest_predictions():
    return [explain_prediction(prediction) for prediction in latest_predictions()]


def explain_prediction_by_id(prediction_id):
    prediction = prediction_by_id(prediction_id)
    if prediction is None:
        return None
    return explain_prediction(prediction)


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


def prize_level_by_match(match_count):
    if match_count == 5:
        return "jackpot"
    if match_count == 4:
        return "fourth_prize"
    if match_count == 3:
        return "third_prize"
    if match_count == 2:
        return "second_prize"
    return "none"


def prediction_status(match_count, has_draw):
    if not has_draw:
        return "waiting_draw"
    if match_count == 5:
        return "jackpot"
    if match_count >= 2:
        return "winner"
    return "no_prize"


def analysis_badge_tone(match_count, status):
    if status == "waiting_draw":
        return "secondary"
    if match_count == 5:
        return "warning"
    if match_count >= 3:
        return "warning"
    if match_count >= 2:
        return "success"
    return "secondary"


def result_card_tone(match_count, status):
    if status == "waiting_draw":
        return "waiting"
    if match_count == 5:
        return "jackpot"
    if match_count >= 3:
        return "gold"
    if match_count >= 2:
        return "success"
    return "neutral"


def prediction_analysis_has_draw(latest_draw, predictions):
    if not latest_draw or not latest_draw.get("numbers") or not predictions:
        return False

    latest_draw_date = parse_draw_date(latest_draw.get("drawDate"))
    latest_prediction_date = max(
        (
            parse_draw_date(item.get("created_at") or item.get("predict_date"))
            for item in predictions
        ),
        default=datetime.min,
    )
    if latest_prediction_date == datetime.min:
        return True
    return latest_draw_date.date() >= latest_prediction_date.date()


def prediction_result_analysis():
    data = dashboard_data()
    latest_draw = data.get("latestDraw") or {}
    predictions = latest_predictions()
    winning_numbers = latest_draw.get("numbers") or []
    winning_set = set(winning_numbers)
    has_draw = prediction_analysis_has_draw(latest_draw, predictions)

    rows = []
    total_prize = 0
    best_match = 0
    total_hits = 0
    highest_hit_rate = 0
    analysis_period = predictions[0].get("created_at") if predictions else None

    for prediction in predictions[:5]:
        numbers = prediction.get("numbers") or []
        matched_numbers = sorted(set(numbers) & winning_set) if has_draw else []
        hits = len(matched_numbers) if has_draw else None
        prize = prize_by_match(hits or 0) if has_draw else None
        hit_rate = round((hits or 0) / 5 * 100, 2) if has_draw else None
        level = prize_level_by_match(hits or 0) if has_draw else "waiting"
        status = prediction_status(hits or 0, has_draw)
        total_prize += prize or 0
        best_match = max(best_match, hits or 0)
        total_hits += hits or 0
        highest_hit_rate = max(highest_hit_rate, hit_rate or 0)
        rows.append({
            "id": prediction.get("id"),
            "set_no": prediction.get("set_no"),
            "numbers": numbers,
            "draw_no": latest_draw.get("drawNo"),
            "draw_date": latest_draw.get("drawDate"),
            "draw_numbers": winning_numbers if has_draw else [],
            "final_score": prediction.get("final_score"),
            "ai_score": prediction.get("ai_score"),
            "hits": hits,
            "matched_numbers": matched_numbers,
            "prize": prize,
            "prize_level": level,
            "hit_rate": hit_rate,
            "status": status,
            "result_status": status,
            "draw_status": "finished" if has_draw else "waiting_draw",
            "badge_tone": analysis_badge_tone(hits or 0, status),
            "card_tone": result_card_tone(hits or 0, status),
        })

    row_count = len(rows)
    best_row = next((row for row in rows if (row["hits"] or 0) == best_match), None)
    has_winner = any((row["hits"] or 0) >= 2 for row in rows) if has_draw else False
    return {
        "latestDraw": latest_draw,
        "analysisPeriod": analysis_period,
        "drawPeriod": latest_draw.get("drawNo"),
        "drawNumbers": winning_numbers if has_draw else [],
        "analyzedCount": row_count,
        "bestMatch": best_match if has_draw else None,
        "averageHits": round(total_hits / row_count, 2) if has_draw and row_count else None,
        "highestHitRate": round(highest_hit_rate, 2) if has_draw and row_count else None,
        "totalPrize": total_prize,
        "bestSet": best_row["set_no"] if best_row else None,
        "hasWinner": has_winner if has_draw else None,
        "analysisTime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "winningSet": best_row,
        "status": "finished" if has_draw else "waiting_draw",
        "rows": rows,
    }


def empty_dashboard_data():
    return {
        "hot": [],
        "cold": [],
        "sumTrend": [],
        "spanTrend": [],
        "oddEven": {"odd": 0, "even": 0},
        "lowHigh": {"low": 0, "high": 0},
        "latestDraw": {},
        "databaseCount": 0,
        "recentDraws": [],
    }


def get_recent_draw_rows(limit=100):
    if not DATABASE_PATH.exists():
        return [], 0, None

    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS count FROM draw_history")
    database_count = cur.fetchone()["count"]

    cur.execute(
        """
        SELECT *
        FROM draw_history
        ORDER BY date(draw_date) DESC, draw_no DESC
        """,
    )
    all_rows = list(cur.fetchall())
    cur.execute(LATEST_DRAW_SQL)
    sql_latest = cur.fetchone()
    conn.close()

    sorted_rows = sorted(all_rows, key=draw_sort_key, reverse=True)
    latest_row = choose_latest_draw(sql_latest, sorted_rows)
    recent_rows = list(reversed(sorted_rows[:limit]))

    return recent_rows, database_count, latest_row


def number_rankings(draws):
    counter = Counter()
    for row in draws:
        counter.update(row_numbers(row))

    all_counts = [{"number": number, "count": counter.get(number, 0)} for number in range(1, 40)]
    hot = sorted(all_counts, key=lambda item: (-item["count"], item["number"]))[:10]
    cold = sorted(all_counts, key=lambda item: (item["count"], item["number"]))[:10]
    return hot, cold


def trend_data(draws, field):
    rows = []
    for row in draws:
        draw = format_draw(row)
        rows.append(
            {
                "label": draw["drawDate"],
                "drawNo": draw["drawNo"],
                "value": draw[field],
            }
        )
    return rows


def ratio_data(draws):
    odd = even = low = high = 0
    for row in draws:
        draw = format_draw(row)
        odd += draw["odd"]
        even += draw["even"]
        low += draw["low"]
        high += draw["high"]

    return {"odd": odd, "even": even}, {"low": low, "high": high}


def dashboard_data(limit=100):
    draws, database_count, latest_row = get_recent_draw_rows(limit=limit)
    if not draws:
        return empty_dashboard_data()

    hot, cold = number_rankings(draws)
    odd_even, low_high = ratio_data(draws)
    recent_draws = [format_draw(row) for row in draws]

    return {
        "hot": hot,
        "cold": cold,
        "sumTrend": trend_data(draws, "sum"),
        "spanTrend": trend_data(draws, "span"),
        "oddEven": odd_even,
        "lowHigh": low_high,
        "latestDraw": format_draw(latest_row) if latest_row else recent_draws[-1],
        "databaseCount": database_count,
        "recentDraws": recent_draws,
    }


def clamp(value, low=0, high=100):
    return max(low, min(high, value))


def average(values, default=0):
    clean = [float(value) for value in values if value is not None]
    if not clean:
        return default
    return sum(clean) / len(clean)


def recommendation(score):
    if score >= 82:
        return "Strong Buy"
    if score >= 68:
        return "Buy"
    if score >= 48:
        return "Neutral"
    return "Avoid"


def confidence_label(score):
    if score >= 80:
        return "High"
    if score >= 60:
        return "Medium"
    return "Low"


def risk_label(score, cold_overlap, trend_score):
    if score < 50 or cold_overlap >= 4 or trend_score < 50:
        return "High"
    if score < 70 or cold_overlap >= 2:
        return "Medium"
    return "Low"


def star_rating(score):
    filled = int(round(score / 20))
    filled = max(0, min(5, filled))
    return "*" * filled + "-" * (5 - filled)


def decision_center():
    predictions = latest_predictions()
    learning = latest_learning()
    data = dashboard_data()

    predicted_numbers = []
    for item in predictions:
        predicted_numbers.extend(item["numbers"])

    hot_numbers = [item["number"] for item in data["hot"][:10]]
    cold_numbers = [item["number"] for item in data["cold"][:10]]
    hot_overlap = sorted(set(predicted_numbers) & set(hot_numbers))
    cold_overlap = sorted(set(predicted_numbers) & set(cold_numbers))

    ai_component = average([item.get("ai_score") for item in predictions], default=50)
    final_component = clamp(average([item.get("final_score") for item in predictions], default=0.5) * 100)

    roi = learning.get("roi")
    hit2 = learning.get("hit2")
    hit3 = learning.get("hit3")
    hit4 = learning.get("hit4")

    roi_component = clamp(((float(roi) if roi is not None else -70) + 100) * 1.0)
    hit_component = clamp(
        average([
            (hit2 or 0),
            (hit3 or 0) * 1.7,
            (hit4 or 0) * 3.0,
        ], default=35)
    )
    learning_component = average([roi_component, hit_component], default=50)

    latest_draw = data.get("latestDraw") or {}
    latest_sum = latest_draw.get("sum")
    latest_span = latest_draw.get("span")
    sum_normal = latest_sum is not None and 80 <= latest_sum <= 130
    span_normal = latest_span is not None and 20 <= latest_span <= 36
    trend_component = average([
        100 if sum_normal else 55,
        100 if span_normal else 55,
    ], default=60)

    hot_cold_component = clamp(55 + len(hot_overlap) * 6 - len(cold_overlap) * 5)

    score = round(
        ai_component * 0.22
        + final_component * 0.18
        + learning_component * 0.20
        + roi_component * 0.12
        + hit_component * 0.10
        + hot_cold_component * 0.10
        + trend_component * 0.08,
        2,
    )

    reasons = {
        "Hot Number": [f"{number:02d}" for number in hot_overlap[:5]],
        "Cold Number": [f"{number:02d}" for number in cold_overlap[:5]],
        "Trend": [
            "Sum normal" if sum_normal else "Sum outside range",
            "Span normal" if span_normal else "Span outside range",
        ],
        "Learning": [
            f"Recent ROI {roi:.2f}%" if roi is not None else "No ROI yet",
            f"Hit2 {hit2:.2f}%" if hit2 is not None else "No hit rate yet",
        ],
        "AI": [round(ai_component, 2)],
        "Final": [round(final_component, 2)],
    }

    return {
        "decisionScore": score,
        "stars": star_rating(score),
        "confidence": confidence_label(score),
        "risk": risk_label(score, len(cold_overlap), trend_component),
        "recommendation": recommendation(score),
        "components": {
            "aiScore": round(ai_component, 2),
            "finalScore": round(final_component, 2),
            "learning": round(learning_component, 2),
            "recentRoi": round(roi_component, 2),
            "recentHitRate": round(hit_component, 2),
            "hotCold": round(hot_cold_component, 2),
            "trend": round(trend_component, 2),
        },
        "reasons": reasons,
    }


def parse_float(value, default=0.0):
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_int(value, default=0):
    return int(parse_float(value, default))


def empty_backtest_center():
    return {
        "summary": {
            "total_periods": 0,
            "cumulative_roi": 0,
            "hit2_rate": 0,
            "hit3_rate": 0,
            "hit4_rate": 0,
            "hit5_rate": 0,
            "avg_best_match": 0,
            "max_losing_streak": 0,
        },
        "roiTrend": [],
        "hitTrend": [],
        "bestMatchDistribution": [],
        "recentRows": [],
    }


def read_backtest_csv():
    if not BACKTEST_REPORT.exists():
        return []

    with BACKTEST_REPORT.open("r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def format_backtest_row(row):
    best_match = parse_int(row.get("best_match"))
    period_prize = parse_float(row.get("period_prize"))
    return {
        "model_version": row.get("model_version", ""),
        "draw_no": row.get("draw_no", ""),
        "draw_date": row.get("draw_date", ""),
        "winning_numbers": row.get("winning_numbers", ""),
        "prediction_sets": row.get("prediction_sets", ""),
        "best_match": best_match,
        "period_roi": parse_float(row.get("period_roi")),
        "cumulative_roi": parse_float(row.get("cumulative_roi")),
        "period_cost": parse_float(row.get("period_cost")),
        "period_prize": period_prize,
        "hit2": 1 if best_match >= 2 else 0,
        "hit3": 1 if best_match >= 3 else 0,
        "hit4": 1 if best_match >= 4 else 0,
        "hit5": 1 if best_match >= 5 else 0,
    }


def max_losing_streak(rows):
    current = 0
    maximum = 0
    for row in rows:
        if row["period_prize"] <= 0:
            current += 1
            maximum = max(maximum, current)
        else:
            current = 0
    return maximum


def rolling_hit_rate(rows, key, window=20):
    trend = []
    for index, row in enumerate(rows):
        start = max(0, index - window + 1)
        sample = rows[start:index + 1]
        rate = sum(item[key] for item in sample) / len(sample) * 100 if sample else 0
        trend.append({
            "label": row["draw_date"] or row["draw_no"],
            "value": round(rate, 2),
        })
    return trend


def backtest_center():
    raw_rows = read_backtest_csv()
    if not raw_rows:
        return empty_backtest_center()

    rows = [format_backtest_row(row) for row in raw_rows]
    total = len(rows)
    distribution = Counter(row["best_match"] for row in rows)

    summary = {
        "total_periods": total,
        "cumulative_roi": round(rows[-1]["cumulative_roi"], 2),
        "hit2_rate": round(sum(row["hit2"] for row in rows) / total * 100, 2),
        "hit3_rate": round(sum(row["hit3"] for row in rows) / total * 100, 2),
        "hit4_rate": round(sum(row["hit4"] for row in rows) / total * 100, 2),
        "hit5_rate": round(sum(row["hit5"] for row in rows) / total * 100, 4),
        "avg_best_match": round(sum(row["best_match"] for row in rows) / total, 2),
        "max_losing_streak": max_losing_streak(rows),
    }

    return {
        "summary": summary,
        "roiTrend": [
            {
                "label": row["draw_date"] or row["draw_no"],
                "value": row["cumulative_roi"],
                "period_roi": row["period_roi"],
            }
            for row in rows
        ],
        "hitTrend": {
            "hit2": rolling_hit_rate(rows, "hit2"),
            "hit3": rolling_hit_rate(rows, "hit3"),
            "hit4": rolling_hit_rate(rows, "hit4"),
        },
        "bestMatchDistribution": [
            {"match": match, "count": distribution.get(match, 0)}
            for match in range(0, 6)
        ],
        "recentRows": list(reversed(rows[-50:])),
    }


def read_learning_strategy_rows(limit=50):
    if not DATABASE_PATH.exists():
        return []

    conn = get_connection()
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
    conn.close()
    return rows


def read_prediction_strategy_rows(limit=50):
    if not DATABASE_PATH.exists():
        return []

    conn = get_connection()
    cur = conn.cursor()
    try:
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
    conn.close()
    return rows


def risk_from_metrics(roi, hit2_rate, volatility=0):
    if roi < -70 or hit2_rate < 18 or volatility > 80:
        return "High"
    if roi < -35 or hit2_rate < 32 or volatility > 45:
        return "Medium"
    return "Low"


def risk_score(label):
    return {"Low": 80, "Medium": 50, "High": 25}.get(label, 50)


def strategy_score(roi, hit2_rate, hit3_rate, risk):
    roi_component = clamp(roi + 100)
    hit_component = clamp(hit2_rate * 0.65 + hit3_rate * 1.25)
    return round(roi_component * 0.42 + hit_component * 0.38 + risk_score(risk) * 0.20, 2)


def backtest_strategy():
    data = backtest_center()
    summary = data["summary"]
    roi_values = [row["value"] for row in data.get("roiTrend", [])]
    volatility = 0
    if len(roi_values) >= 2:
        deltas = [abs(roi_values[index] - roi_values[index - 1]) for index in range(1, len(roi_values))]
        volatility = average(deltas, default=0)

    roi = summary.get("cumulative_roi", 0)
    hit2 = summary.get("hit2_rate", 0)
    hit3 = summary.get("hit3_rate", 0)
    risk = risk_from_metrics(roi, hit2, volatility)
    return {
        "id": "backtest",
        "name": "Backtest Strategy",
        "source": "reports/backtest_result.csv",
        "roi": round(roi, 2),
        "hit2Rate": round(hit2, 2),
        "hit3Rate": round(hit3, 2),
        "risk": risk,
        "score": strategy_score(roi, hit2, hit3, risk),
        "sampleSize": summary.get("total_periods", 0),
    }


def learning_strategy():
    rows = read_learning_strategy_rows(limit=50)
    if not rows:
        roi = hit2 = hit3 = 0
    else:
        roi = average([row["roi"] for row in rows[:10]], default=0)
        hit2 = average([row["hit2"] for row in rows[:10]], default=0)
        hit3 = average([row["hit3"] for row in rows[:10]], default=0)

    risk = risk_from_metrics(roi, hit2)
    return {
        "id": "learning",
        "name": "Learning Strategy",
        "source": "learning_history",
        "roi": round(roi, 2),
        "hit2Rate": round(hit2, 2),
        "hit3Rate": round(hit3, 2),
        "risk": risk,
        "score": strategy_score(roi, hit2, hit3, risk),
        "sampleSize": len(rows),
    }


def prediction_strategy():
    rows = read_prediction_strategy_rows(limit=50)
    if not rows:
        ai = final = 0
    else:
        ai = average([row["ai_score"] for row in rows], default=0)
        final = average([row["final_score"] for row in rows], default=0) * 100

    roi = clamp(((final + ai) / 2) - 100, -100, 100)
    hit2 = clamp(ai * 0.48)
    hit3 = clamp(final * 0.18)
    risk = risk_from_metrics(roi, hit2)
    return {
        "id": "prediction",
        "name": "Prediction Strategy",
        "source": "prediction_history",
        "roi": round(roi, 2),
        "hit2Rate": round(hit2, 2),
        "hit3Rate": round(hit3, 2),
        "risk": risk,
        "score": strategy_score(roi, hit2, hit3, risk),
        "sampleSize": len(rows),
    }


def hybrid_strategy(strategies):
    if not strategies:
        roi = hit2 = hit3 = 0
    else:
        total_score = sum(max(item["score"], 1) for item in strategies)
        roi = sum(item["roi"] * max(item["score"], 1) for item in strategies) / total_score
        hit2 = sum(item["hit2Rate"] * max(item["score"], 1) for item in strategies) / total_score
        hit3 = sum(item["hit3Rate"] * max(item["score"], 1) for item in strategies) / total_score

    risk = risk_from_metrics(roi, hit2)
    return {
        "id": "hybrid",
        "name": "Hybrid Strategy",
        "source": "weighted aggregate",
        "roi": round(roi, 2),
        "hit2Rate": round(hit2, 2),
        "hit3Rate": round(hit3, 2),
        "risk": risk,
        "score": strategy_score(roi, hit2, hit3, risk),
        "sampleSize": sum(item["sampleSize"] for item in strategies),
    }


def strategy_lab():
    base_strategies = [
        backtest_strategy(),
        learning_strategy(),
        prediction_strategy(),
    ]
    strategies = base_strategies + [hybrid_strategy(base_strategies)]
    ranking = sorted(strategies, key=lambda item: item["score"], reverse=True)
    labels = [item["name"] for item in ranking]
    recommended = ranking[0] if ranking else None

    return {
        "strategies": strategies,
        "ranking": ranking,
        "roiCompare": {
            "labels": labels,
            "values": [item["roi"] for item in ranking],
        },
        "hitCompare": {
            "labels": labels,
            "hit2": [item["hit2Rate"] for item in ranking],
            "hit3": [item["hit3Rate"] for item in ranking],
        },
        "riskCompare": [
            {
                "name": item["name"],
                "risk": item["risk"],
                "riskScore": risk_score(item["risk"]),
                "sampleSize": item["sampleSize"],
            }
            for item in ranking
        ],
        "recommendation": {
            "strategy": recommended["name"] if recommended else "-",
            "score": recommended["score"] if recommended else 0,
            "risk": recommended["risk"] if recommended else "-",
            "reason": (
                f"{recommended['name']} has the best combined ROI, hit-rate, and risk score."
                if recommended else "No strategy data available yet."
            ),
        },
    }


def model_comparison():
    base_strategies = [
        prediction_strategy(),
        backtest_strategy(),
        learning_strategy(),
    ]
    strategies = base_strategies + [hybrid_strategy(base_strategies)]
    rows = []
    for item in strategies:
        hit2 = item.get("hit2Rate", 0)
        hit3 = item.get("hit3Rate", 0)
        average_hits = clamp(hit2 / 100 * 2 + hit3 / 100 * 3, 0, 5)
        rows.append({
            "id": item.get("id"),
            "name": item.get("name"),
            "recentRoi": item.get("roi", 0),
            "hitRate": hit2,
            "averageHits": round(average_hits, 2),
            "risk": item.get("risk", "Medium"),
            "recommendation": recommendation(item.get("score", 0)),
            "score": item.get("score", 0),
            "sampleSize": item.get("sampleSize", 0),
        })
    ranking = sorted(rows, key=lambda item: item["score"], reverse=True)
    return {
        "models": rows,
        "ranking": ranking,
        "bestModel": ranking[0] if ranking else None,
    }


def strategy_optimizer():
    return {
        "strategies": rank_strategies(),
        "comparison": compare_strategies(),
        "recommendation": recommend_best_strategy(),
    }


def prediction_quality_score(prediction):
    final_score = parse_float(prediction.get("final_score"), default=0) * 100
    ai_score = parse_float(prediction.get("ai_score"), default=0)
    return final_score * 0.45 + ai_score * 0.55


def best_prediction_pick(predictions, analysis):
    rows = analysis.get("rows") or []
    if rows and analysis.get("status") == "finished":
        return max(
            rows,
            key=lambda row: (
                row.get("hits") or 0,
                row.get("prize") or 0,
                prediction_quality_score(row),
            ),
        )

    if not predictions:
        return None
    return max(predictions, key=prediction_quality_score)


def dashboard_decision_trend(limit=30):
    rows = prediction_history(limit=limit)
    trend = []
    for row in reversed(rows):
        try:
            report = explain_prediction(row)
            value = report.get("decisionScore")
        except Exception:
            value = None
        trend.append({
            "label": row.get("created_at") or f"Set {row.get('set_no')}",
            "value": round(parse_float(value, default=0), 2),
        })
    return trend


def dashboard_pro():
    data = dashboard_data()
    predictions = latest_predictions()
    analysis = prediction_result_analysis()
    decision = decision_center()
    strategy = strategy_lab()
    optimizer = strategy_optimizer()
    backtest = backtest_center()
    performance = system_performance()
    system = system_info()

    latest_draw = data.get("latestDraw") or {}
    best_pick = best_prediction_pick(predictions, analysis)
    optimizer_recommendation = optimizer.get("recommendation") or {}
    strategy_recommendation = strategy.get("recommendation") or {}
    result_rows = analysis.get("rows") or []
    best_result = (
        max(result_rows, key=lambda row: (row.get("hits") or 0, row.get("prize") or 0))
        if result_rows else None
    )
    total_prize = analysis.get("totalPrize") or 0
    total_cost = len(result_rows) * 50 if result_rows else 0
    roi = round(((total_prize - total_cost) / total_cost) * 100, 2) if total_cost else 0
    roi_trend = (backtest.get("roiTrend") or [])[-30:]
    hit_trend = ((backtest.get("hitTrend") or {}).get("hit2") or [])[-30:]

    return {
        "todaySummary": {
            "latestDraw": latest_draw.get("drawNo"),
            "drawDate": latest_draw.get("drawDate"),
            "latestNumbers": latest_draw.get("numbers") or [],
            "bestPick": best_pick,
            "decisionScore": decision.get("decisionScore"),
            "recommendation": decision.get("recommendation"),
            "bestStrategy": optimizer_recommendation.get("strategy") or strategy_recommendation.get("strategy"),
            "drawStatus": analysis.get("status"),
        },
        "todayPrediction": {
            "rows": predictions[:5],
            "bestSet": best_pick.get("set_no") if best_pick else None,
        },
        "todayResult": {
            "status": analysis.get("status"),
            "bestHit": analysis.get("bestMatch"),
            "hitCount": best_result.get("hits") if best_result else None,
            "matchedNumbers": best_result.get("matched_numbers") if best_result else [],
            "prize": best_result.get("prize") if best_result else 0,
            "roi": roi,
            "bestSet": best_result.get("set_no") if best_result else None,
        },
        "decisionOverview": decision,
        "strategyOverview": {
            "strategies": optimizer.get("strategies") or strategy.get("strategies") or [],
            "ranking": strategy.get("ranking") or [],
            "roiCompare": strategy.get("roiCompare") or {},
            "hitCompare": strategy.get("hitCompare") or {},
            "riskCompare": strategy.get("riskCompare") or [],
            "bestStrategy": optimizer_recommendation.get("strategy") or strategy_recommendation.get("strategy"),
            "overallScore": optimizer_recommendation.get("overallScore") or strategy_recommendation.get("score"),
            "risk": optimizer_recommendation.get("risk") or strategy_recommendation.get("risk"),
            "confidence": optimizer_recommendation.get("confidence"),
            "radar": optimizer,
        },
        "performance": {
            **performance,
            "databaseCount": system.get("databaseCount"),
            "predictionCount": system.get("predictionCount"),
            "learningCount": system.get("learningCount"),
        },
        "trend30": {
            "roi": roi_trend,
            "hitRate": hit_trend,
            "decisionScore": dashboard_decision_trend(limit=30),
        },
    }


def simple_dashboard():
    pro = dashboard_pro()
    analysis = prediction_result_analysis()
    signal = ai_signal()
    comparison = model_comparison()
    auto_status = auto_model_loop_status()
    predictions = pro.get("todayPrediction", {}).get("rows") or latest_predictions()
    best_pick = pro.get("todaySummary", {}).get("bestPick")
    if not best_pick and predictions:
        best_pick = best_prediction_pick(predictions, analysis)

    result_rows = analysis.get("rows") or []
    total_prize = analysis.get("totalPrize") or 0
    total_cost = len(result_rows) * 50 if result_rows else 0
    roi = round(((total_prize - total_cost) / total_cost) * 100, 2) if total_cost else 0

    return {
        "currentPrediction": {
            "recommendations": predictions[:5],
            "bestPick": best_pick,
            "aiSignal": signal,
            "buyRecommendation": signal.get("signal") or pro.get("todaySummary", {}).get("recommendation"),
            "shouldBuy": (signal.get("score") or 0) >= 68,
        },
        "lastResult": {
            "drawNo": analysis.get("drawPeriod"),
            "drawNumbers": analysis.get("drawNumbers") or [],
            "predictions": result_rows[:5],
            "totalPrize": total_prize,
            "roi": roi,
            "status": analysis.get("status"),
        },
        "modelComparison": comparison.get("models") or [],
        "bestModel": comparison.get("bestModel"),
        "autoModel": auto_status,
    }


def auto_model_status():
    return auto_model_loop_status()


def auto_model_run():
    return run_auto_model_loop()


def all_prediction_rows(limit=300):
    if not DATABASE_PATH.exists():
        return []

    ensure_prediction_history_schema()
    conn = get_connection()
    cur = conn.cursor()
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
    conn.close()
    return [format_prediction(row) for row in rows]


def draw_history_rows(limit=400):
    rows, _, _ = get_recent_draw_rows(limit=limit)
    return [format_draw(row) for row in rows]


def matching_draw_for_prediction(prediction, draws):
    if not draws:
        return {}
    prediction_date = parse_draw_date(prediction.get("created_at"))
    candidates = [
        draw for draw in draws
        if parse_draw_date(draw.get("drawDate")) >= prediction_date
    ]
    return candidates[0] if candidates else draws[-1]


def prediction_match_row(prediction, draw):
    draw_numbers = draw.get("numbers") or []
    matched = sorted(set(prediction.get("numbers") or []) & set(draw_numbers))
    hits = len(matched)
    prize = prize_by_match(hits)
    return {
        **prediction,
        "drawNo": draw.get("drawNo"),
        "drawDate": draw.get("drawDate"),
        "drawNumbers": draw_numbers,
        "hits": hits,
        "matchedNumbers": matched,
        "hitRate": round(hits / 5 * 100, 2),
        "prizeLevel": prize_level_by_match(hits),
        "prize": prize,
        "status": prediction_status(hits, True),
    }


def prediction_performance():
    predictions = list(reversed(all_prediction_rows(limit=250)))
    draws = draw_history_rows(limit=500)
    rows = [prediction_match_row(prediction, matching_draw_for_prediction(prediction, draws)) for prediction in predictions]

    return {
        "hitTrend": [
            {
                "label": row.get("created_at") or f"Set {row.get('set_no')}",
                "value": row["hits"],
                "setNo": row.get("set_no"),
            }
            for row in rows
        ],
        "prizeTrend": [
            {
                "label": row.get("created_at") or f"Set {row.get('set_no')}",
                "value": row["prize"],
                "setNo": row.get("set_no"),
            }
            for row in rows
        ],
        "aiScoreVsHits": [
            {"x": row.get("ai_score") or 0, "y": row["hits"], "setNo": row.get("set_no")}
            for row in rows
        ],
        "finalScoreVsHits": [
            {"x": round((row.get("final_score") or 0) * 100, 2), "y": row["hits"], "setNo": row.get("set_no")}
            for row in rows
        ],
        "recentRows": list(reversed(rows[-50:])),
    }


def set_performance():
    rows = prediction_performance()["recentRows"]
    result = []
    for set_no in range(1, 6):
        set_rows = [row for row in rows if row.get("set_no") == set_no]
        total_prize = sum(row.get("prize") or 0 for row in set_rows)
        total_cost = len(set_rows) * 50
        result.append({
            "setNo": set_no,
            "totalPrize": total_prize,
            "averageHits": round(average([row.get("hits") for row in set_rows], default=0), 2),
            "bestHit": max([row.get("hits") or 0 for row in set_rows], default=0),
            "winCount": sum(1 for row in set_rows if (row.get("hits") or 0) >= 2),
            "roi": round(((total_prize - total_cost) / total_cost) * 100, 2) if total_cost else 0,
            "sampleSize": len(set_rows),
        })
    return {"sets": result}


def hit_heatmap():
    rows = prediction_performance()["recentRows"]
    set_hit = {
        set_no: {hit: 0 for hit in range(0, 6)}
        for set_no in range(1, 6)
    }
    number_frequency = {number: 0 for number in range(1, 40)}

    for row in rows:
        set_no = row.get("set_no")
        hits = row.get("hits") or 0
        if set_no in set_hit:
            set_hit[set_no][hits] += 1
        for number in row.get("matchedNumbers") or []:
            number_frequency[number] += 1

    return {
        "setHitCount": [
            {"setNo": set_no, "hits": hit, "count": count}
            for set_no, hit_map in set_hit.items()
            for hit, count in hit_map.items()
        ],
        "numberHitFrequency": [
            {"number": number, "count": count}
            for number, count in number_frequency.items()
        ],
    }


def ai_signal():
    decision = decision_center()
    predictions = latest_predictions()
    learning = latest_learning()
    backtest_summary = backtest_center().get("summary") or {}
    return calculate_ai_signal(
        decision=decision,
        predictions=predictions,
        learning=learning,
        backtest=backtest_summary,
    )


def table_count(table_name):
    if not DATABASE_PATH.exists():
        return 0

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) AS count FROM {table_name}")
        count = cur.fetchone()["count"]
    except sqlite3.Error:
        count = 0
    conn.close()
    return count


def file_mtime(path):
    if not path.exists():
        return None
    return path.stat().st_mtime


def file_mtime_text(path):
    timestamp = file_mtime(path)
    if timestamp is None:
        return None
    from datetime import datetime
    return datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")


def git_value(args):
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=5,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        return "unknown"
    return "unknown"


def git_info():
    return {
        "branch": git_value(["rev-parse", "--abbrev-ref", "HEAD"]),
        "commit": git_value(["rev-parse", "--short", "HEAD"]),
    }


def system_health():
    database_count = table_count("draw_history")
    prediction_count = table_count("prediction_history")
    learning_count = table_count("learning_history")

    return {
        "database": {
            "ok": DATABASE_PATH.exists() and database_count > 0,
            "label": f"{database_count} draws" if DATABASE_PATH.exists() else "missing",
        },
        "api": {
            "ok": True,
            "label": "online",
        },
        "learning": {
            "ok": learning_count > 0,
            "label": f"{learning_count} runs",
        },
        "dashboard": {
            "ok": DASHBOARD_FILE.exists(),
            "label": file_mtime_text(DASHBOARD_FILE) or "missing",
        },
        "prediction": {
            "ok": prediction_count > 0,
            "label": f"{prediction_count} rows",
        },
        "runAll": {
            "ok": (BASE_DIR / API_SCRIPTS["run_all"]).exists(),
            "label": "ready" if (BASE_DIR / API_SCRIPTS["run_all"]).exists() else "missing",
        },
    }


def system_info():
    git = git_info()
    return {
        "version": app_version(),
        "git": git,
        "gitBranch": git["branch"],
        "gitCommit": git["commit"],
        "buildTime": BUILD_TIME,
        "databaseCount": table_count("draw_history"),
        "predictionCount": table_count("prediction_history"),
        "learningCount": table_count("learning_history"),
        "dashboardTime": file_mtime_text(DASHBOARD_FILE),
        "modelVersion": MODEL_VERSION,
        "modelWeightsExists": MODEL_FILE.exists(),
        "backtestReportExists": BACKTEST_REPORT.exists(),
        "health": system_health(),
    }


def health_check():
    health = system_health()
    cache = cache_stats()
    performance = performance_stats()

    try:
        explain_ok = bool(explain_latest_predictions())
    except Exception:
        explain_ok = False

    return {
        "database": health["database"],
        "prediction": health["prediction"],
        "learning": health["learning"],
        "dashboard": health["dashboard"],
        "backtest": {
            "ok": BACKTEST_REPORT.exists(),
            "label": "ready" if BACKTEST_REPORT.exists() else "missing",
        },
        "explain": {
            "ok": explain_ok,
            "label": "ready" if explain_ok else "no prediction data",
        },
        "cache": {
            "ok": True,
            "label": f"{cache['size']} items, {cache['hitRate']}% hit",
            "stats": cache,
        },
        "logger": {
            "ok": True,
            "label": "enabled",
        },
        "api": {
            "ok": True,
            "label": f"{performance['averageApiTime']} ms avg",
        },
    }


def system_performance():
    return performance_stats()
