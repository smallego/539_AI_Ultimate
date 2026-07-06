from tests.conftest import assert_ok, client


def test_decision_api_format():
    data = assert_ok(client().get("/api/decision"))
    expected = {
        "decisionScore",
        "confidence",
        "risk",
        "recommendation",
        "components",
        "reasons",
    }
    assert expected.issubset(data)
    assert 0 <= data["decisionScore"] <= 100
    assert data["risk"] in {"Low", "Medium", "High"}
