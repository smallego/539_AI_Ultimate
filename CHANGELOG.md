# Changelog

All notable changes for 539 AI Ultimate Professional are summarized here.

## V7 Release Candidate

### Added

- Multi-page FastAPI Web application.
- Professional Dashboard with Sidebar, Topbar, Breadcrumb, Footer, and Bootstrap 5 layout.
- Chart.js data visualization pages for Dashboard, Data Center, Learning, and Backtest.
- Prediction History with SQLite persistence.
- Explainable AI Engine in `core/explainer.py`.
- Explain Drawer on the Prediction page.
- Decision Center with score, confidence, risk, recommendation, and reasons.
- Strategy Backtest Center with ROI, hit trend, match distribution, and recent row table.
- AI Learning Center with ROI history, hit-rate charts, and weight history.
- System Health API and dashboard widgets.
- System Performance API with API timing, cache hit/miss, CPU, memory, and recent request metrics.
- 60-second TTL cache for dashboard, decision, explain, backtest, and learning data.
- Unified API request logging with request ID, duration, success/fail, and exception fields.
- Pytest smoke/contract tests.
- GitHub Actions CI for compile, tests, Ruff, and Black.
- Dockerfile and Docker Compose release runtime.

### Changed

- Dashboard moved from a single-page button interface to a multi-page Web application.
- README and docs were expanded for Release Candidate readiness.
- Requirements were split into runtime and development dependency files.

### Compatibility

- Prediction, Learning, Decision, Backtest, and Explainer algorithms are preserved.
- Database schema is not changed by this release candidate.

## V6

### Added

- FastAPI Web UI foundation.
- Jinja2 templates with Bootstrap 5 and Chart.js.
- Web API endpoints for run-all, update, predict, backtest, dashboard, status, dashboard data, learning, decision, and backtest center.
- Prediction persistence through `prediction_history`.
- Learning persistence through `learning_history`.
- Web dashboard charts for hot/cold numbers, sum trend, span trend, odd/even ratio, and low/high ratio.
- Config and logger modules for Web runtime settings and daily logs.

### Changed

- Tkinter GUI was deprecated in favor of a Web UI.
- Web UI was progressively upgraded from action buttons to visual analytics.

## V5

### Added

- B-Model V5 configuration.
- Candidate scorer pipeline.
- AI score integration.
- Rolling backtest workflow.
- Learning weights stored in `models/weights.json`.
- SQLite historical draw storage.

### Changed

- Core model weighting and scorer workflow matured into the baseline used by V6 and V7.
