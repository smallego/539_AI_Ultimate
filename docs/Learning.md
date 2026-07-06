# Learning

Learning stores model feedback and weights without changing the prediction algorithm during this release candidate.

## Data Sources

- `models/weights.json`
- `learning_history` in SQLite
- Backtest summary outputs

## Web Views

The Learning page shows:

- current model
- current weights
- recent ROI
- hit rates
- ROI history
- hit-rate history
- weight history

## API

- `GET /api/learning/latest`
- `GET /api/learning/history`
- `GET /api/learning/weights`
