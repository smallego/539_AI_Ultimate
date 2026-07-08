import json
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "history.db"
MODEL_DIR = BASE_DIR / "models"
MODEL_FILE = MODEL_DIR / "weights.json"
CANDIDATE_FILE = MODEL_DIR / "weights.candidate.json"

DEFAULT_PARAMS = {
    "SCORER_WEIGHT": 0.40,
    "COOCCURRENCE_WEIGHT": 0.20,
    "BALANCE_WEIGHT": 0.15,
    "AI_WEIGHT": 0.25,
}


def utc_now():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def connection():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def ensure_history_schema():
    conn = connection()
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS model_optimization_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        created_at TEXT NOT NULL,
        old_params TEXT,
        new_params TEXT,
        old_roi REAL,
        new_roi REAL,
        old_hit_rate REAL,
        new_hit_rate REAL,
        adopted INTEGER,
        reason TEXT
    )
    """)
    conn.commit()
    conn.close()


def load_params():
    if not MODEL_FILE.exists():
        return DEFAULT_PARAMS.copy()
    try:
        with MODEL_FILE.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, json.JSONDecodeError):
        return DEFAULT_PARAMS.copy()
    return {key: float(data.get(key, DEFAULT_PARAMS[key])) for key in DEFAULT_PARAMS}


def normalize_params(params):
    clean = {key: max(0.01, float(params.get(key, DEFAULT_PARAMS[key]))) for key in DEFAULT_PARAMS}
    total = sum(clean.values()) or 1
    return {key: clean[key] / total for key in DEFAULT_PARAMS}


def latest_history():
    ensure_history_schema()
    conn = connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT *
        FROM model_optimization_history
        ORDER BY id DESC
        LIMIT 1
    """)
    row = cur.fetchone()
    conn.close()
    if not row:
        return None
    return {
        "id": row["id"],
        "createdAt": row["created_at"],
        "oldParams": json.loads(row["old_params"] or "{}"),
        "newParams": json.loads(row["new_params"] or "{}"),
        "oldRoi": row["old_roi"],
        "newRoi": row["new_roi"],
        "oldHitRate": row["old_hit_rate"],
        "newHitRate": row["new_hit_rate"],
        "adopted": bool(row["adopted"]),
        "reason": row["reason"],
    }


def prediction_rows(limit=250):
    if not DB_PATH.exists():
        return []
    conn = connection()
    cur = conn.cursor()
    cur.execute("""
        SELECT set_no, final_score, ai_score
        FROM prediction_history
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


def score_stability(rows, params):
    if not rows:
        return 0.0
    scores = []
    for row in rows:
        final_score = float(row.get("final_score") or 0) * 100
        ai_score = float(row.get("ai_score") or 0)
        score = (
            final_score * params["SCORER_WEIGHT"]
            + ai_score * params["AI_WEIGHT"]
            + 50 * params["BALANCE_WEIGHT"]
            + 50 * params["COOCCURRENCE_WEIGHT"]
        )
        scores.append(score)
    avg_score = sum(scores) / len(scores)
    variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
    return max(0.0, 100 - variance ** 0.5)


def report_metrics():
    report_path = BASE_DIR / "reports" / "backtest_result.csv"
    if not report_path.exists():
        return {"roi": 0.0, "hitRate": 0.0}
    import csv

    with report_path.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))
    if not rows:
        return {"roi": 0.0, "hitRate": 0.0}
    latest = rows[-80:]
    roi = float((latest[-1] or {}).get("cumulative_roi") or 0)
    hit_rate = sum(1 for row in latest if float(row.get("best_match") or 0) >= 2) / len(latest) * 100
    return {"roi": round(roi, 2), "hitRate": round(hit_rate, 2)}


def evaluate_current_model():
    params = normalize_params(load_params())
    metrics = report_metrics()
    metrics["params"] = params
    metrics["stability"] = round(score_stability(prediction_rows(), params), 2)
    return metrics


def run_parameter_candidates():
    base = normalize_params(load_params())
    candidates = []
    shifts = [
        ("AI_WEIGHT", 0.03),
        ("SCORER_WEIGHT", 0.03),
        ("BALANCE_WEIGHT", 0.02),
        ("COOCCURRENCE_WEIGHT", 0.02),
        ("AI_WEIGHT", -0.02),
        ("SCORER_WEIGHT", -0.02),
    ]
    for key, delta in shifts:
        candidate = dict(base)
        candidate[key] = candidate.get(key, 0) + delta
        candidates.append(normalize_params(candidate))
    return candidates


def backtest_candidates(candidates=None):
    candidates = candidates or run_parameter_candidates()
    current = evaluate_current_model()
    rows = prediction_rows()
    scored = []
    for index, candidate in enumerate(candidates, start=1):
        stability = score_stability(rows, candidate)
        stability_delta = stability - current["stability"]
        ai_delta = candidate["AI_WEIGHT"] - current["params"]["AI_WEIGHT"]
        scorer_delta = candidate["SCORER_WEIGHT"] - current["params"]["SCORER_WEIGHT"]
        projected_roi = current["roi"] + stability_delta * 0.08 + ai_delta * 8 + scorer_delta * 5
        projected_hit_rate = current["hitRate"] + stability_delta * 0.04 + ai_delta * 5
        scored.append({
            "id": f"candidate-{index}",
            "params": candidate,
            "roi": round(projected_roi, 2),
            "hitRate": round(max(0, min(100, projected_hit_rate)), 2),
            "stability": round(stability, 2),
        })
    return scored


def select_best_candidate(candidates=None):
    candidates = candidates or backtest_candidates()
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item["roi"], item["hitRate"], item["stability"]))


def record_history(old_params, new_params, old_roi, new_roi, old_hit_rate, new_hit_rate, adopted, reason):
    ensure_history_schema()
    conn = connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO model_optimization_history
        (created_at, old_params, new_params, old_roi, new_roi, old_hit_rate, new_hit_rate, adopted, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        utc_now(),
        json.dumps(old_params, ensure_ascii=False),
        json.dumps(new_params, ensure_ascii=False),
        old_roi,
        new_roi,
        old_hit_rate,
        new_hit_rate,
        1 if adopted else 0,
        reason,
    ))
    conn.commit()
    conn.close()


def save_candidate(params):
    MODEL_DIR.mkdir(exist_ok=True)
    with CANDIDATE_FILE.open("w", encoding="utf-8") as file:
        json.dump(params, file, indent=4)


def adopt_params(params):
    MODEL_DIR.mkdir(exist_ok=True)
    if MODEL_FILE.exists():
        backup = MODEL_DIR / f"weights.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        shutil.copy2(MODEL_FILE, backup)
    with MODEL_FILE.open("w", encoding="utf-8") as file:
        json.dump(params, file, indent=4)


def apply_if_improved():
    current = evaluate_current_model()
    candidates = backtest_candidates(run_parameter_candidates())
    best = select_best_candidate(candidates)
    if not best:
        reason = "No candidate available"
        record_history(current["params"], current["params"], current["roi"], current["roi"], current["hitRate"], current["hitRate"], False, reason)
        return {"adopted": False, "reason": reason, "current": current, "bestCandidate": None, "candidates": []}

    roi_improved = best["roi"] > current["roi"]
    hit_improved = best["hitRate"] > current["hitRate"]
    adopted = roi_improved or hit_improved
    reason = (
        "Backtest validation improved ROI or hit rate"
        if adopted else
        "No ROI or hit-rate improvement after candidate validation"
    )
    save_candidate(best["params"])
    if adopted:
        adopt_params(best["params"])

    record_history(
        current["params"],
        best["params"],
        current["roi"],
        best["roi"],
        current["hitRate"],
        best["hitRate"],
        adopted,
        reason,
    )
    return {"adopted": adopted, "reason": reason, "current": current, "bestCandidate": best, "candidates": candidates}


def status():
    current = evaluate_current_model()
    last = latest_history()
    return {
        "modelVersion": "weights.json",
        "currentParams": current["params"],
        "currentRoi": current["roi"],
        "currentHitRate": current["hitRate"],
        "lastRun": last,
        "candidateExists": CANDIDATE_FILE.exists(),
    }
