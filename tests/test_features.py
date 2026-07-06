# tests/test_features.py

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "core"))

from core.features import analyze_set


def test_analyze_set_basic():
    result = analyze_set([2, 10, 15, 31, 37])

    assert result["sum"] == 95
    assert result["span"] == 35
    assert result["odd"] == 3
    assert result["even"] == 2
    assert result["low"] == 3
    assert result["high"] == 2
    assert result["consecutive"] == 0
    assert result["same_tail"] == 0