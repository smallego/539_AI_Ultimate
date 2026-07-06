import sqlite3
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "history.db"
MODEL_FILE = BASE_DIR / "models" / "weights.json"


def number_fields():
    return ["n1", "n2", "n3", "n4", "n5"]


def row_numbers(row):
    return [int(row[field]) for field in number_fields()]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_prediction_history_schema():
    if not DB_PATH.exists():
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
    if not DB_PATH.exists():
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
    if not DB_PATH.exists():
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
    if not DB_PATH.exists():
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
    if not DB_PATH.exists():
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
    if not DB_PATH.exists():
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
    if not DB_PATH.exists():
        return [], 0

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS count FROM draw_history")
    database_count = cur.fetchone()["count"]

    cur.execute(
        """
        SELECT *
        FROM draw_history
        ORDER BY draw_date DESC, draw_no DESC
        LIMIT ?
        """,
        (limit,),
    )
    rows = list(cur.fetchall())
    conn.close()

    return list(reversed(rows)), database_count


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
    draws, database_count = get_recent_draw_rows(limit=limit)
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
        "latestDraw": recent_draws[-1],
        "databaseCount": database_count,
        "recentDraws": recent_draws,
    }
