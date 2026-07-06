import csv
import sqlite3
import subprocess
import sys

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates

from web.config import (
    API_SCRIPTS,
    BACKTEST_REPORT,
    BASE_DIR,
    DASHBOARD_FILE,
    DATABASE_PATH,
    MODEL_FILE,
    WEB_DIR,
)
from web.logger import log_event
from web.services import (
    dashboard_data,
    decision_center,
    ensure_prediction_history_schema,
    latest_learning,
    latest_predictions,
    learning_history,
    learning_weights,
    prediction_history,
    system_info,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def run_script(action):
    script_path = API_SCRIPTS[action]
    log_event(action, "START", script=script_path)
    process = subprocess.run(
        [sys.executable, script_path],
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    log_event(
        action,
        "SUCCESS" if process.returncode == 0 else "FAILED",
        returncode=process.returncode,
        stdout_tail=process.stdout[-1000:],
        stderr_tail=process.stderr[-1000:],
    )
    return {
        "ok": process.returncode == 0,
        "returncode": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr,
    }


def database_counts():
    data = dashboard_data()
    predictions = []
    if DATABASE_PATH.exists():
        ensure_prediction_history_schema()
        conn = sqlite3.connect(DATABASE_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) AS count FROM prediction_history")
        prediction_count = cur.fetchone()["count"]
        conn.close()
        predictions = latest_predictions()
    else:
        prediction_count = 0

    latest_draw = data["latestDraw"] or None
    return {
        "database_exists": DATABASE_PATH.exists(),
        "draw_count": data["databaseCount"],
        "prediction_count": prediction_count,
        "latest_draw": latest_draw,
        "latest_predictions": predictions,
    }


def format_numbers(row):
    if row is None:
        return []
    return [int(row[f"n{i}"]) for i in range(1, 6)]


def format_draw(row):
    if row is None:
        return None
    return {
        "draw_no": row["draw_no"],
        "draw_date": row["draw_date"],
        "numbers": format_numbers(row),
    }


def format_prediction(row):
    return {
        "set_no": row["set_no"],
        "predict_date": row["predict_date"],
        "model_version": row["model_version"],
        "numbers": format_numbers(row),
    }


def read_backtest_rows(limit=120):
    if not BACKTEST_REPORT.exists():
        return []

    with BACKTEST_REPORT.open("r", encoding="utf-8-sig", newline="") as file:
        rows = list(csv.DictReader(file))

    chart_rows = []
    for row in rows[-limit:]:
        chart_rows.append(
            {
                "label": row.get("draw_date") or row.get("draw_no") or "",
                "best_match": int(float(row.get("best_match") or 0)),
                "cumulative_roi": float(row.get("cumulative_roi") or 0),
            }
        )
    return chart_rows


def backtest_status():
    rows = read_backtest_rows()
    if not rows:
        return {
            "exists": BACKTEST_REPORT.exists(),
            "count": 0,
            "latest_roi": None,
            "best_match": None,
        }

    return {
        "exists": True,
        "count": len(rows),
        "latest_roi": rows[-1]["cumulative_roi"],
        "best_match": max(row["best_match"] for row in rows),
    }


@router.get("/")
def index(request: Request):
    log_event("page.index", "SUCCESS")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"title": "539 AI Ultimate V6"},
    )


@router.post("/api/run-all")
def api_run_all():
    return JSONResponse(run_script("run_all"))


@router.post("/api/update")
def api_update():
    return JSONResponse(run_script("update"))


@router.post("/api/predict")
def api_predict():
    return JSONResponse(run_script("predict"))


@router.post("/api/backtest")
def api_backtest():
    return JSONResponse(run_script("backtest"))


@router.post("/api/dashboard")
def api_dashboard():
    return JSONResponse(run_script("dashboard"))


@router.get("/api/status")
def api_status():
    log_event("api.status", "SUCCESS")
    status = database_counts()
    status.update(
        {
            "dashboard_exists": DASHBOARD_FILE.exists(),
            "weights_exists": MODEL_FILE.exists(),
            "backtest": backtest_status(),
        }
    )
    return status


@router.get("/api/dashboard-data")
def api_dashboard_data():
    log_event("api.dashboard_data", "SUCCESS")
    return dashboard_data()


@router.get("/api/decision")
def api_decision():
    log_event("api.decision", "SUCCESS")
    return decision_center()


@router.get("/api/predictions/latest")
def api_predictions_latest():
    log_event("api.predictions.latest", "SUCCESS")
    return latest_predictions()


@router.get("/api/predictions/history")
def api_predictions_history():
    log_event("api.predictions.history", "SUCCESS")
    return prediction_history(limit=50)


@router.get("/api/learning/latest")
def api_learning_latest():
    log_event("api.learning.latest", "SUCCESS")
    return latest_learning()


@router.get("/api/learning/history")
def api_learning_history():
    log_event("api.learning.history", "SUCCESS")
    return learning_history(limit=50)


@router.get("/api/learning/weights")
def api_learning_weights():
    log_event("api.learning.weights", "SUCCESS")
    return learning_weights(limit=20)


@router.get("/api/system")
def api_system():
    log_event("api.system", "SUCCESS")
    return system_info()


@router.get("/api/backtest-chart")
def api_backtest_chart():
    log_event("api.backtest_chart", "SUCCESS")
    rows = read_backtest_rows()
    return {
        "labels": [row["label"] for row in rows],
        "best_match": [row["best_match"] for row in rows],
        "cumulative_roi": [row["cumulative_roi"] for row in rows],
    }
