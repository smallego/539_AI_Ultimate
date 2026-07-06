from tests.conftest import assert_ok, client


def test_backtest_center_api_format():
    data = assert_ok(client().get("/api/backtest-center"))
    assert {"summary", "roiTrend", "hitTrend", "bestMatchDistribution", "recentRows"}.issubset(data)
    summary = data["summary"]
    for key in ["total_periods", "cumulative_roi", "hit2_rate", "hit3_rate", "avg_best_match"]:
        assert key in summary
