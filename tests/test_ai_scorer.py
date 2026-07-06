from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "core"))

from core.ai_scorer import ai_score


def test_ai_score_range():
    result = ai_score([2, 10, 15, 31, 37])

    assert 0 <= result["ai_score"] <= 100


def test_ai_score_has_fields():
    result = ai_score([2, 10, 15, 31, 37])

    assert "features" in result
    assert "scores" in result
    assert "numbers" in result


def test_ai_numbers_sorted():
    result = ai_score([37, 2, 31, 15, 10])

    assert result["numbers"] == [2, 10, 15, 31, 37]