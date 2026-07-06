from pathlib import Path
import json
import sqlite3
from datetime import datetime

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"
MODEL_DIR.mkdir(exist_ok=True)

MODEL_FILE = MODEL_DIR / "weights.json"
DB_PATH = BASE_DIR / "database" / "history.db"

DEFAULT = {
    "SCORER_WEIGHT": 0.40,
    "COOCCURRENCE_WEIGHT": 0.20,
    "BALANCE_WEIGHT": 0.15,
    "AI_WEIGHT": 0.25,
}


def load_weights():
    if not MODEL_FILE.exists():
        save_weights(DEFAULT)
        return DEFAULT.copy()

    with open(MODEL_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_weights(w):
    with open(MODEL_FILE, "w", encoding="utf-8") as f:
        json.dump(w, f, indent=4)


def ensure_learning_history_schema():
    conn = sqlite3.connect(DB_PATH)
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


def save_learning_result(
    model_version,
    roi,
    hit2,
    hit3,
    hit4,
    hit5,
    avg_match,
    weights,
):
    ensure_learning_history_schema()

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
    INSERT INTO learning_history
    (
        created_at,
        model_version,
        roi,
        hit2,
        hit3,
        hit4,
        hit5,
        avg_match,
        weights_json
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        model_version,
        float(roi),
        float(hit2),
        float(hit3),
        float(hit4),
        float(hit5),
        float(avg_match),
        json.dumps(weights, ensure_ascii=False),
    ))

    conn.commit()
    conn.close()


def learn(roi):

    w = load_weights()

    if roi < -70:
        w["AI_WEIGHT"] += 0.02
        w["SCORER_WEIGHT"] -= 0.01
        w["COOCCURRENCE_WEIGHT"] -= 0.01

    elif roi > -40:
        w["AI_WEIGHT"] -= 0.01
        w["SCORER_WEIGHT"] += 0.01

    total = sum(w.values())

    for k in w:
        w[k] /= total

    save_weights(w)

    return w
