import csv
import sqlite3
import subprocess
import sys

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, RedirectResponse, StreamingResponse
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
from web.cache import cached, clear_cache
from web.export_excel import build_excel_report, excel_filename
from web.export_service import build_pdf, build_xlsx, export_filename
from web.logger import log_event
from web.services import (
    ai_signal,
    auto_model_run,
    auto_model_status,
    backtest_center,
    dashboard_data,
    dashboard_pro,
    decision_center,
    ensure_prediction_history_schema,
    explain_latest_predictions,
    explain_prediction_by_id,
    health_check,
    latest_learning,
    latest_predictions,
    learning_history,
    learning_weights,
    hit_heatmap,
    model_comparison,
    prediction_history,
    prediction_performance,
    prediction_result_analysis,
    set_performance,
    simple_dashboard,
    strategy_lab,
    strategy_optimizer,
    system_performance,
    system_info,
)

router = APIRouter()
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


PAGE_META = {
    "dashboard": ("Dashboard", "/dashboard"),
    "prediction": ("Prediction", "/prediction"),
    "decision": ("Decision", "/decision"),
    "learning": ("Learning", "/learning"),
    "backtest": ("Backtest", "/backtest"),
    "strategy": ("Strategy Lab", "/strategy"),
    "data": ("Data Center", "/data"),
    "settings": ("Settings", "/settings"),
}


def render_page(request, template_name, page_key):
    page_title, _ = PAGE_META[page_key]
    return templates.TemplateResponse(
        request=request,
        name=template_name,
        context={
            "title": "539 AI Ultimate Professional",
            "page_title": page_title,
            "active_page": page_key,
            "breadcrumb": ["Home", page_title],
            "pages": PAGE_META,
        },
    )


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
    if process.returncode == 0:
        clear_cache()
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
    return RedirectResponse(url="/dashboard")


@router.get("/dashboard")
def dashboard_page(request: Request):
    log_event("page.dashboard", "SUCCESS")
    return render_page(request, "pages/dashboard.html", "dashboard")


@router.get("/prediction")
def prediction_page(request: Request):
    log_event("page.prediction", "SUCCESS")
    return render_page(request, "pages/prediction.html", "prediction")


@router.get("/decision")
def decision_page(request: Request):
    log_event("page.decision", "SUCCESS")
    return render_page(request, "pages/decision.html", "decision")


@router.get("/learning")
def learning_page(request: Request):
    log_event("page.learning", "SUCCESS")
    return render_page(request, "pages/learning.html", "learning")


@router.get("/backtest")
def backtest_page(request: Request):
    log_event("page.backtest", "SUCCESS")
    return render_page(request, "pages/backtest.html", "backtest")


@router.get("/strategy")
def strategy_page(request: Request):
    log_event("page.strategy", "SUCCESS")
    return render_page(request, "pages/strategy.html", "strategy")


@router.get("/data")
def data_page(request: Request):
    log_event("page.data", "SUCCESS")
    return render_page(request, "pages/data.html", "data")


@router.get("/settings")
def settings_page(request: Request):
    log_event("page.settings", "SUCCESS")
    return render_page(request, "pages/settings.html", "settings")


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
    status = cached("status", database_counts)
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
    return cached("dashboard_data", dashboard_data)


@router.get("/api/dashboard-pro")
def api_dashboard_pro():
    log_event("api.dashboard_pro", "SUCCESS")
    return cached("dashboard_pro", dashboard_pro)


@router.get("/api/simple-dashboard")
def api_simple_dashboard():
    log_event("api.simple_dashboard", "SUCCESS")
    return cached("simple_dashboard", simple_dashboard)


@router.get("/api/model-comparison")
def api_model_comparison():
    log_event("api.model_comparison", "SUCCESS")
    return cached("model_comparison", model_comparison)


@router.get("/api/auto-model/status")
def api_auto_model_status():
    log_event("api.auto_model.status", "SUCCESS")
    return auto_model_status()


@router.post("/api/auto-model/run")
def api_auto_model_run():
    log_event("api.auto_model.run", "START")
    result = auto_model_run()
    clear_cache()
    log_event("api.auto_model.run", "SUCCESS", adopted=result.get("adopted"), reason=result.get("reason"))
    return result


@router.get("/api/decision")
def api_decision():
    log_event("api.decision", "SUCCESS")
    return cached("decision", decision_center)


@router.get("/api/backtest-center")
def api_backtest_center():
    log_event("api.backtest_center", "SUCCESS")
    return cached("backtest_center", backtest_center)


@router.get("/api/strategies")
def api_strategies():
    log_event("api.strategies", "SUCCESS")
    return cached("strategies", lambda: strategy_lab()["strategies"])


@router.get("/api/strategy-lab")
def api_strategy_lab():
    log_event("api.strategy_lab", "SUCCESS")
    return cached("strategy_lab", strategy_lab)


@router.get("/api/strategy-optimizer")
def api_strategy_optimizer():
    log_event("api.strategy_optimizer", "SUCCESS")
    return cached("strategy_optimizer", strategy_optimizer)


@router.get("/api/predictions/latest")
def api_predictions_latest():
    log_event("api.predictions.latest", "SUCCESS")
    return cached("predictions_latest", latest_predictions)


@router.get("/api/predictions/history")
def api_predictions_history():
    log_event("api.predictions.history", "SUCCESS")
    return cached("predictions_history_50", lambda: prediction_history(limit=50))


@router.get("/api/prediction-analysis")
def api_prediction_analysis():
    log_event("api.prediction_analysis", "SUCCESS")
    return cached("prediction_analysis", prediction_result_analysis)


@router.get("/api/prediction-performance")
def api_prediction_performance():
    log_event("api.prediction_performance", "SUCCESS")
    return cached("prediction_performance", prediction_performance)


@router.get("/api/set-performance")
def api_set_performance():
    log_event("api.set_performance", "SUCCESS")
    return cached("set_performance", set_performance)


@router.get("/api/hit-heatmap")
def api_hit_heatmap():
    log_event("api.hit_heatmap", "SUCCESS")
    return cached("hit_heatmap", hit_heatmap)


@router.get("/api/ai-signal")
def api_ai_signal():
    log_event("api.ai_signal", "SUCCESS")
    return cached("ai_signal", ai_signal)


@router.get("/api/explain/latest")
def api_explain_latest():
    log_event("api.explain.latest", "SUCCESS")
    return cached("explain_latest", explain_latest_predictions)


@router.get("/api/explain/{prediction_id}")
def api_explain_prediction(prediction_id: int):
    log_event("api.explain.prediction", "SUCCESS", prediction_id=prediction_id)
    report = cached(f"explain_{prediction_id}", lambda: explain_prediction_by_id(prediction_id))
    if report is None:
        return JSONResponse({"error": "Prediction not found"}, status_code=404)
    return report


@router.get("/api/learning/latest")
def api_learning_latest():
    log_event("api.learning.latest", "SUCCESS")
    return cached("learning_latest", latest_learning)


@router.get("/api/learning/history")
def api_learning_history():
    log_event("api.learning.history", "SUCCESS")
    return cached("learning_history_50", lambda: learning_history(limit=50))


@router.get("/api/learning/weights")
def api_learning_weights():
    log_event("api.learning.weights", "SUCCESS")
    return cached("learning_weights_20", lambda: learning_weights(limit=20))


@router.get("/api/system")
def api_system():
    log_event("api.system", "SUCCESS")
    return system_info()


@router.get("/api/health")
def api_health():
    log_event("api.health", "SUCCESS")
    return health_check()


@router.get("/api/performance")
def api_performance():
    log_event("api.performance", "SUCCESS")
    return system_performance()


@router.get("/api/backtest-chart")
def api_backtest_chart():
    log_event("api.backtest_chart", "SUCCESS")
    rows = read_backtest_rows()
    return {
        "labels": [row["label"] for row in rows],
        "best_match": [row["best_match"] for row in rows],
        "cumulative_roi": [row["cumulative_roi"] for row in rows],
    }


@router.get("/api/export/excel")
def api_export_excel():
    log_event("api.export.excel", "SUCCESS")
    return StreamingResponse(
        build_excel_report(),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{excel_filename()}"'},
    )


@router.get("/api/export/pdf")
def api_export_pdf_report():
    log_event("api.export.pdf.report", "SUCCESS")
    filename = excel_filename().replace(".xlsx", ".pdf")
    return StreamingResponse(
        build_pdf("dashboard"),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/export/{report_type}.xlsx")
def api_export_xlsx(report_type: str):
    if report_type not in {"dashboard", "prediction", "decision", "strategy"}:
        return JSONResponse({"error": "Unsupported report type"}, status_code=404)
    log_event("api.export.xlsx", "SUCCESS", report_type=report_type)
    filename = export_filename(report_type, "xlsx")
    return StreamingResponse(
        build_xlsx(report_type),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/api/export/{report_type}.pdf")
def api_export_pdf(report_type: str):
    if report_type not in {"dashboard", "prediction", "decision", "strategy"}:
        return JSONResponse({"error": "Unsupported report type"}, status_code=404)
    log_event("api.export.pdf", "SUCCESS", report_type=report_type)
    filename = export_filename(report_type, "pdf")
    return StreamingResponse(
        build_pdf(report_type),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
