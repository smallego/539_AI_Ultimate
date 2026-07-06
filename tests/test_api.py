from tests.conftest import assert_ok, client


def test_api_status_smoke():
    data = assert_ok(client().get("/api/status"))
    assert "database_exists" in data
    assert "prediction_count" in data
    assert "backtest" in data


def test_api_health_smoke():
    data = assert_ok(client().get("/api/health"))
    for key in ["database", "prediction", "learning", "dashboard", "backtest", "explain", "cache", "logger"]:
        assert key in data
        assert "ok" in data[key]


def test_api_performance_smoke():
    data = assert_ok(client().get("/api/performance"))
    assert "averageApiTime" in data
    assert "cacheHit" in data
    assert "cacheMiss" in data
    assert isinstance(data["recentApi"], list)
