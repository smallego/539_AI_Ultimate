from tests.conftest import assert_ok, client


def test_prediction_latest_format():
    data = assert_ok(client().get("/api/predictions/latest"))
    assert isinstance(data, list)
    if not data:
        return

    item = data[0]
    assert {"id", "set_no", "numbers", "final_score", "ai_score"}.issubset(item)
    assert isinstance(item["numbers"], list)
    assert len(item["numbers"]) == 5
