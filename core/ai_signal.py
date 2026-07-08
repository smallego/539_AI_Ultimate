from core.explainer import explain_prediction
from core.strategy_optimizer import recommend_best_strategy


def _clamp(value, low=0, high=100):
    return max(low, min(high, value))


def _average(values, default=0):
    clean = [float(value) for value in values if value is not None]
    return sum(clean) / len(clean) if clean else default


def _signal_label(score, risk):
    if risk == "High" and score < 65:
        return "Skip Today"
    if score >= 82:
        return "Strong Buy"
    if score >= 68:
        return "Buy"
    if score >= 50:
        return "Neutral"
    if score >= 36:
        return "Reduce"
    return "Skip Today"


def _stars(score):
    filled = int(round(score / 20))
    filled = max(0, min(5, filled))
    return "*" * filled + "-" * (5 - filled)


def _color(signal):
    return {
        "Strong Buy": "success",
        "Buy": "primary",
        "Neutral": "secondary",
        "Reduce": "warning",
        "Skip Today": "danger",
    }.get(signal, "secondary")


def calculate_ai_signal(
    decision=None,
    predictions=None,
    learning=None,
    backtest=None,
):
    decision = decision or {}
    predictions = predictions or []
    learning = learning or {}
    backtest = backtest or {}

    strategy = recommend_best_strategy()
    explain_reports = []
    for prediction in predictions[:5]:
        try:
            explain_reports.append(explain_prediction(prediction))
        except Exception:
            continue

    decision_score = float(decision.get("decisionScore") or 50)
    confidence_value = decision.get("confidence")
    if isinstance(confidence_value, str):
        confidence = {"High": 84, "Medium": 62, "Low": 38}.get(confidence_value, 50)
    else:
        confidence = float(confidence_value or 50)

    risk = decision.get("risk") or strategy.get("risk") or "Medium"
    risk_score = {"Low": 88, "Medium": 58, "High": 28}.get(risk, 58)
    strategy_score = float(strategy.get("overallScore") or 50)
    recent_roi = float(learning.get("roi") or backtest.get("cumulative_roi") or -50)
    recent_hit = _average([
        learning.get("hit2"),
        learning.get("hit3"),
        backtest.get("hit2_rate"),
        backtest.get("hit3_rate"),
    ], default=28)
    explain_score = _average([report.get("decisionScore") for report in explain_reports], default=decision_score)
    final_score = _average([(item.get("final_score") or 0) * 100 for item in predictions], default=50)

    score = round(
        decision_score * 0.22
        + confidence * 0.14
        + risk_score * 0.14
        + strategy_score * 0.16
        + _clamp(recent_roi + 100) * 0.10
        + _clamp(recent_hit) * 0.10
        + explain_score * 0.08
        + final_score * 0.06,
        2,
    )
    signal = _signal_label(score, risk)

    reasons = [
        f"Decision Score {decision_score:.2f}",
        f"Confidence {confidence:.2f}",
        f"Risk {risk}",
        f"Strategy {strategy.get('strategy', '-')}",
        f"Recent ROI {recent_roi:.2f}",
        f"Recent Hit Rate {recent_hit:.2f}",
        f"Explain Score {explain_score:.2f}",
        f"Final Score {final_score:.2f}",
    ]

    return {
        "signal": signal,
        "score": score,
        "confidence": round(confidence, 2),
        "risk": risk,
        "reason": reasons,
        "color": _color(signal),
        "stars": _stars(score),
    }
