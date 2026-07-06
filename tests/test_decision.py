from tests.conftest import assert_ok, client


def test_decision_api_format():
    data = assert_ok(client().get("/api/decision"))
    assert {"decisionScore", "confidence", "risk", "recommendation", "components", "reasons"}.issubset(data)
    assert 0 <= data["decisionScore"] <= 100
    assert data["risk"] in {"Low", "Medium", "High"}
