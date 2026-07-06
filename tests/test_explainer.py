from core.explainer import explain_prediction
from tests.conftest import assert_ok, client


def test_explainer_engine_format():
    report = explain_prediction(
        {
            "id": 1,
            "set_no": 1,
            "numbers": [1, 8, 21, 25, 39],
            "final_score": 0.88,
            "ai_score": 92,
            "model_version": "test",
            "created_at": "test",
        }
    )
    assert {"decisionScore", "confidence", "risk", "reasons", "timeline"}.issubset(report)
    assert 0 <= report["decisionScore"] <= 100
    assert isinstance(report["reasons"], list)


def test_explain_latest_api_smoke():
    data = assert_ok(client().get("/api/explain/latest"))
    assert isinstance(data, list)
    if not data:
        return
    assert {"decisionScore", "confidence", "risk", "reasons", "timeline"}.issubset(data[0])


def test_explain_by_id_api_smoke():
    latest = assert_ok(client().get("/api/predictions/latest"))
    if not latest:
        return

    data = assert_ok(client().get(f"/api/explain/{latest[0]['id']}"))
    assert data["predictionId"] == latest[0]["id"]
    assert isinstance(data["reasons"], list)
