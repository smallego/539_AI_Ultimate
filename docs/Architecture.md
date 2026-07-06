# Architecture

539 AI Ultimate Professional V7 is organized as a local-first Web application around existing prediction engines.

## Layers

- `core/`: algorithmic and analytical modules.
- `web/routes.py`: page routes and API endpoints.
- `web/services.py`: read-oriented service functions used by APIs.
- `web/cache.py`: in-memory 60-second TTL cache and recent API metrics.
- `web/logger.py`: daily JSON log writer.
- `web/templates/`: Jinja2 layouts and pages.
- `web/static/`: CSS and page-specific JavaScript.

## Request Flow

```text
Browser
  -> FastAPI route
  -> service/cache layer
  -> SQLite, reports, models, or core explainer
  -> JSON API or Jinja2 page
```

## Release Candidate Boundary

V7.1.3 focuses on packaging and documentation. It does not alter Prediction, Learning, Backtest, Decision, or Explain algorithms.
