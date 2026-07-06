# API

## System

- `GET /api/status`: database, prediction, dashboard, weight, and backtest status.
- `GET /api/health`: health for Database, Prediction, Learning, Dashboard, Backtest, Explain, Cache, Logger.
- `GET /api/performance`: average API time, cache hit/miss, CPU, memory, and recent API timings.
- `GET /api/system`: version, git, counts, dashboard time, and model version.

## Dashboard

- `GET /api/dashboard-data`: hot/cold numbers, sum trend, span trend, ratios, latest draw, and count.

## Prediction

- `GET /api/predictions/latest`: latest saved prediction set group.
- `GET /api/predictions/history`: latest 50 saved prediction rows.
- `POST /api/predict`: runs the existing prediction script.

## Explain

- `GET /api/explain/latest`: explain reports for the latest prediction group.
- `GET /api/explain/{prediction_id}`: explain report for one prediction row.

## Decision

- `GET /api/decision`: decision score, confidence, risk, recommendation, components, and reasons.

## Learning

- `GET /api/learning/latest`: latest learning result.
- `GET /api/learning/history`: recent learning rows.
- `GET /api/learning/weights`: current weights and recent weight history.

## Backtest

- `GET /api/backtest-center`: summary, ROI trend, hit trend, distribution, and recent rows.
- `POST /api/backtest`: runs the existing backtest script.

## Operations

- `POST /api/run-all`
- `POST /api/update`
- `POST /api/dashboard`
