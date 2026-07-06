# Contributing

Thank you for improving 539 AI Ultimate Professional.

## Ground Rules

- Do not change Prediction, Learning, Decision, Backtest, or Explainer algorithms without an explicit versioned task.
- Do not change the database schema without a migration plan and release note.
- Keep Web changes separated from core algorithm changes.
- Prefer smoke tests for local-only resources such as SQLite databases and generated reports.

## Development Setup

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

## Quality Checks

```bash
python -m compileall core web tests
python -m pytest tests
python -m ruff check .
python -m black --check .
```

## Pull Request Checklist

- The change is scoped and documented.
- Tests pass locally or the reason is noted.
- README/docs are updated when APIs, routes, or release behavior change.
- No generated files, logs, databases, or local reports are committed.

## Commit Style

Use concise messages:

```text
docs: prepare v7 release candidate
web: add health status panel
tests: add explain api smoke test
```
