# app/database.py

import sqlite3
from pathlib import Path
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
DB_DIR = BASE_DIR / "database"
DB_PATH = DB_DIR / "history.db"


def now_text():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_connection():
    DB_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS draw_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        draw_no TEXT UNIQUE NOT NULL,
        draw_date TEXT NOT NULL,
        n1 INTEGER NOT NULL,
        n2 INTEGER NOT NULL,
        n3 INTEGER NOT NULL,
        n4 INTEGER NOT NULL,
        n5 INTEGER NOT NULL,
        odd_count INTEGER,
        even_count INTEGER,
        low_count INTEGER,
        high_count INTEGER,
        total_sum INTEGER,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prediction_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        predict_date TEXT NOT NULL,
        model_version TEXT NOT NULL,
        set_no INTEGER NOT NULL,
        n1 INTEGER NOT NULL,
        n2 INTEGER NOT NULL,
        n3 INTEGER NOT NULL,
        n4 INTEGER NOT NULL,
        n5 INTEGER NOT NULL,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS verify_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        draw_no TEXT,
        draw_date TEXT,
        set_no INTEGER,
        predicted_numbers TEXT,
        winning_numbers TEXT,
        match_count INTEGER,
        prize INTEGER,
        cost INTEGER,
        roi REAL,
        created_at TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS model_weights (
        number INTEGER PRIMARY KEY,
        frequency_score REAL DEFAULT 1.0,
        miss_score REAL DEFAULT 1.0,
        montecarlo_score REAL DEFAULT 1.0,
        bayesian_score REAL DEFAULT 1.0,
        cooccurrence_score REAL DEFAULT 1.0,
        final_weight REAL DEFAULT 1.0,
        updated_at TEXT
    )
    """)

    for num in range(1, 40):
        cur.execute("""
        INSERT OR IGNORE INTO model_weights
        (
            number,
            frequency_score,
            miss_score,
            montecarlo_score,
            bayesian_score,
            cooccurrence_score,
            final_weight,
            updated_at
        )
        VALUES (?, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, ?)
        """, (num, now_text()))

    conn.commit()
    conn.close()


def calculate_draw_features(numbers):
    numbers = sorted([int(n) for n in numbers])

    odd_count = sum(1 for n in numbers if n % 2 == 1)
    even_count = 5 - odd_count

    low_count = sum(1 for n in numbers if n <= 19)
    high_count = 5 - low_count

    total_sum = sum(numbers)

    return {
        "numbers": numbers,
        "odd_count": odd_count,
        "even_count": even_count,
        "low_count": low_count,
        "high_count": high_count,
        "total_sum": total_sum,
    }


def insert_draw(draw_no, draw_date, numbers):
    features = calculate_draw_features(numbers)
    nums = features["numbers"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    INSERT OR IGNORE INTO draw_history
    (
        draw_no,
        draw_date,
        n1, n2, n3, n4, n5,
        odd_count,
        even_count,
        low_count,
        high_count,
        total_sum,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        str(draw_no),
        str(draw_date),
        nums[0], nums[1], nums[2], nums[3], nums[4],
        features["odd_count"],
        features["even_count"],
        features["low_count"],
        features["high_count"],
        features["total_sum"],
        now_text()
    ))

    conn.commit()
    conn.close()


def insert_prediction(model_version, sets):
    predict_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_connection()
    cur = conn.cursor()

    for idx, numbers in enumerate(sets, start=1):
        nums = sorted([int(n) for n in numbers])

        cur.execute("""
        INSERT INTO prediction_history
        (
            predict_date,
            model_version,
            set_no,
            n1, n2, n3, n4, n5,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            predict_date,
            model_version,
            idx,
            nums[0], nums[1], nums[2], nums[3], nums[4],
            now_text()
        ))

    conn.commit()
    conn.close()


def get_all_draws():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM draw_history
    ORDER BY draw_date ASC, draw_no ASC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def get_latest_draw():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM draw_history
    ORDER BY draw_date DESC, draw_no DESC
    LIMIT 1
    """)

    row = cur.fetchone()
    conn.close()
    return row


def get_latest_predictions(limit=5):
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

    return list(reversed(rows))


def get_weights():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT *
    FROM model_weights
    ORDER BY final_weight DESC
    """)

    rows = cur.fetchall()
    conn.close()
    return rows


def update_weight(number, final_weight):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    UPDATE model_weights
    SET final_weight = ?,
        updated_at = ?
    WHERE number = ?
    """, (
        float(final_weight),
        now_text(),
        int(number)
    ))

    conn.commit()
    conn.close()


def database_summary():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS cnt FROM draw_history")
    draw_count = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) AS cnt FROM prediction_history")
    prediction_count = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) AS cnt FROM verify_history")
    verify_count = cur.fetchone()["cnt"]

    cur.execute("SELECT COUNT(*) AS cnt FROM model_weights")
    weight_count = cur.fetchone()["cnt"]

    conn.close()

    return {
        "db_path": str(DB_PATH),
        "draw_count": draw_count,
        "prediction_count": prediction_count,
        "verify_count": verify_count,
        "weight_count": weight_count,
    }


def test_insert_sample_data():
    insert_draw(
        draw_no="TEST001",
        draw_date="2026-07-04",
        numbers=[4, 11, 24, 25, 31]
    )


if __name__ == "__main__":
    init_database()

    summary = database_summary()

    print("===================================")
    print("539 AI Ultimate - Database Module")
    print("資料庫初始化完成")
    print("===================================")
    print(f"資料庫位置：{summary['db_path']}")
    print(f"開獎資料筆數：{summary['draw_count']}")
    print(f"預測資料筆數：{summary['prediction_count']}")
    print(f"驗證資料筆數：{summary['verify_count']}")
    print(f"權重資料筆數：{summary['weight_count']}")
    print("===================================")