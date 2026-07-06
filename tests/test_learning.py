from tests.conftest import assert_ok, client


def test_learning_latest_api_smoke():
    data = assert_ok(client().get("/api/learning/latest"))
    assert isinstance(data, dict)


def test_learning_weights_api_smoke():
    data = assert_ok(client().get("/api/learning/weights"))
    assert "current" in data
    assert "history" in data
    assert isinstance(data["history"], list)
