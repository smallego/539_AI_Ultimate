# Explain

The Explainable AI Engine lives in:

```text
core/explainer.py
```

## Inputs

For one prediction, the explainer reads:

- prediction numbers
- AI score
- final score
- latest learning result
- current model weights
- recent backtest report
- recent draw trend
- hot/cold number rankings

## Output

The report includes:

- `decisionScore`
- `stars`
- `confidence`
- `risk`
- `components`
- `reasons`
- `timeline`

## UI

The Prediction page includes an Explain button that opens a right-side drawer with the report.
