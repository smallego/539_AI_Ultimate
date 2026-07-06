# 539 AI Ultimate Professional

[![CI](https://github.com/your-org/539_AI_Ultimate/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/539_AI_Ultimate/actions/workflows/ci.yml)

539 AI Ultimate Professional is a local-first FastAPI dashboard for 539 prediction workflows. V7 turns the project into a multi-page professional Web application while preserving the existing Prediction, Learning, Decision, Backtest, and Explainable AI engines.

## Architecture

```text
539_AI_Ultimate
├── app/                 Legacy app scripts and orchestration
├── core/                Prediction, learning, backtest, scorer, explainer
├── database/            SQLite runtime database
├── docs/                Architecture, API, database, learning, explain, decision docs
├── models/              Model weight files
├── reports/             Generated backtest reports
├── tests/               Pytest smoke and API contract tests
└── web/                 FastAPI, routes, services, templates, static assets
```

Web runtime:

- FastAPI for HTTP API and page routing.
- Jinja2 for templates.
- Bootstrap 5 for professional UI.
- Chart.js for dashboard visualization.
- SQLite for local historical data.
- TTL cache and structured daily logs for performance and observability.

## Screenshots

Screenshots are not committed in this release candidate. Recommended captures:

- `/dashboard`: health, performance, KPI cards, and trend charts.
- `/prediction`: recommendation cards, history, and Explain drawer.
- `/learning`: ROI, hit rate, and weight history.
- `/backtest`: ROI trend, hit trend, distribution, and recent rows.

## API

Core read APIs:

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

Action APIs:

- `POST /api/run-all`
- `POST /api/update`
- `POST /api/predict`
- `POST /api/backtest`
- `POST /api/dashboard`

See [docs/API.md](docs/API.md) for details.

## Install

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Run

```bash
uvicorn web.app:app --host 127.0.0.1 --port 8000
```

Open:

```text
http://127.0.0.1:8000/dashboard
```

Docker:

```bash
docker compose up --build
```

## Testing

```bash
python -m compileall core web tests
python -m pytest tests
python -m ruff check .
python -m black --check .
```

The test suite is designed as smoke and contract coverage. It does not require external network calls. Local database/report dependent checks are skipped or relaxed when data is unavailable.

## Documentation

- [Architecture](docs/Architecture.md)
- [API](docs/API.md)
- [Database](docs/Database.md)
- [Learning](docs/Learning.md)
- [Explain](docs/Explain.md)
- [Decision](docs/Decision.md)
- [Release Checklist](docs/RELEASE_CHECKLIST.md)

## License

MIT. See [LICENSE](LICENSE).
