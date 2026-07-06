# 539 AI Ultimate Professional

539 AI Ultimate is a local professional dashboard for 539 prediction workflows. V7 separates the web experience into a multi-page FastAPI application while keeping the existing Prediction, Learning, Decision, and Backtest engines intact.

## V7 Architecture

- `core/`: prediction scorer, learning, backtest, and explainable AI helpers.
- `database/`: SQLite data store (`history.db`).
- `web/`: FastAPI routes, Jinja2 templates, Bootstrap 5 UI, Chart.js views, TTL cache, logging, health, and performance APIs.
- `reports/`: backtest CSV outputs.
- `models/`: learning weights.
- `tests/`: pytest smoke and contract tests.

## Web Pages

- `/dashboard`: system dashboard, charts, health, and performance.
- `/prediction`: latest recommendations, history, and Explain drawer.
- `/decision`: decision score and reasons.
- `/learning`: learning center and weight history.
- `/backtest`: strategy backtest center.
- `/data`: draw data center.
- `/settings`: version, git, counts, and health details.

## API

- `GET /api/status`
- `GET /api/health`
- `GET /api/performance`
- `GET /api/system`
- `GET /api/dashboard-data`
- `GET /api/decision`
- `GET /api/backtest-center`
- `GET /api/predictions/latest`
- `GET /api/predictions/history`
- `GET /api/explain/latest`
- `GET /api/explain/{prediction_id}`
- `GET /api/learning/latest`
- `GET /api/learning/history`
- `GET /api/learning/weights`
- `POST /api/run-all`
- `POST /api/update`
- `POST /api/predict`
- `POST /api/backtest`
- `POST /api/dashboard`

## Install

Use any available Python environment.

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Quick Start

```bash
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/dashboard
```

## Tests

```bash
pytest
```

The test suite covers API status, health, prediction format, decision, learning, backtest, explain API, and smoke checks.

## Quality Layer

- `web/cache.py`: 60-second TTL cache for dashboard, decision, explain, backtest, and learning APIs.
- `web/logger.py`: JSON daily logs with request id, duration, success/fail, and exception fields.
- `GET /api/health`: reports Database, Prediction, Learning, Dashboard, Backtest, Explain, Cache, and Logger health.
- `GET /api/performance`: reports average API time, cache hit/miss, memory, CPU, and recent API timings.
