from pathlib import Path
import sys

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "core"))

from core.engine import build_final_weights


def test_engine_final_weights():
    if not (BASE_DIR / "database" / "history.db").exists():
        pytest.skip("local SQLite database is not available in CI")

    result = build_final_weights()

    assert "final_weights" in result
    assert "draw_count" in result
    assert result["draw_count"] > 0

    weights = result["final_weights"]

    assert len(weights) == 39

    for n in range(1, 40):
        assert n in weights
        assert weights[n] > 0
