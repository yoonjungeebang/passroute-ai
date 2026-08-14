import pytest

from app.services.debate_llm_service import (
    _DEBATE_WEIGHTS,
    _ROUND_ACTIVE_FIELDS,
    _fill_template,
    _format_history,
    _format_list,
    _renormalize_and_score,
)


class TestFillTemplate:
    def test_simple_substitution(self):
        result = _fill_template("Hello {name}!", {"name": "World"})
        assert result == "Hello World!"

    def test_escaped_braces(self):
        result = _fill_template("JSON: {{key}}", {})
        assert result == "JSON: {key}"

    def test_mixed(self):
        result = _fill_template("{{\"name\": \"{name}\"}}", {"name": "test"})
        assert result == '{"name": "test"}'

    def test_no_variables(self):
        result = _fill_template("No vars here {{safe}}", {})
        assert result == "No vars here {safe}"

    def test_multiple_variables(self):
        result = _fill_template("{a} and {b}", {"a": "X", "b": "Y"})
        assert result == "X and Y"

    def test_variable_not_in_template(self):
        result = _fill_template("Hello", {"name": "World"})
        assert result == "Hello"


class TestFormatHistory:
    def test_empty_history(self):
        assert _format_history([]) == "없음"
        assert _format_history(None) == "없음"

    def test_with_turns(self):
        class FakeTurn:
            speaker_type = "USER"
            round_type = "OPENING"
            content = "찬성 입론입니다."
        result = _format_history([FakeTurn()])
        assert "사용자" in result
        assert "입론" in result

    def test_ai_competitor(self):
        class FakeTurn:
            speaker_type = "AI_COMPETITOR"
            round_type = "REBUTTAL_1"
            content = "반박합니다."
        result = _format_history([FakeTurn()])
        assert "AI 경쟁자" in result
        assert "반박 1" in result


class TestFormatList:
    def test_basic(self):
        result = _format_list(["항목1", "항목2"])
        assert result == "- 항목1\n- 항목2"


class TestRenormalizeAndScore:
    def test_opening_round(self):
        raw_scores = {
            "logic": {"score": 4, "feedback": "논리적"},
            "attitude": {"score": 5, "feedback": "좋은 태도"},
        }
        scores, weighted = _renormalize_and_score(raw_scores, "OPENING")
        assert scores.logic is not None
        assert scores.attitude is not None
        assert scores.rebuttal_quality is None
        assert scores.consistency is None
        assert 0 <= weighted <= 100

    def test_rebuttal_round_all_fields(self):
        raw_scores = {
            "logic": {"score": 3, "feedback": "보통"},
            "rebuttal_quality": {"score": 4, "feedback": "좋음"},
            "consistency": {"score": 5, "feedback": "일관적"},
            "attitude": {"score": 4, "feedback": "좋음"},
        }
        scores, weighted = _renormalize_and_score(raw_scores, "REBUTTAL_1")
        assert scores.logic is not None
        assert scores.rebuttal_quality is not None
        assert scores.consistency is not None
        assert scores.attitude is not None
        assert 0 <= weighted <= 100

    def test_closing_round_no_rebuttal(self):
        raw_scores = {
            "logic": {"score": 4, "feedback": "좋음"},
            "consistency": {"score": 3, "feedback": "보통"},
            "attitude": {"score": 5, "feedback": "좋음"},
        }
        scores, weighted = _renormalize_and_score(raw_scores, "CLOSING")
        assert scores.rebuttal_quality is None

    def test_weights_sum_to_one(self):
        for round_type, active in _ROUND_ACTIVE_FIELDS.items():
            total = sum(_DEBATE_WEIGHTS[f] for f in active)
            raw_scores = {f: {"score": 3, "feedback": "test"} for f in active}
            scores, _ = _renormalize_and_score(raw_scores, round_type)
            weight_sum = 0.0
            for field in ("logic", "rebuttal_quality", "consistency", "attitude"):
                item = getattr(scores, field)
                if item is not None:
                    weight_sum += item.weight
            assert abs(weight_sum - 1.0) < 0.01

    def test_perfect_score(self):
        raw_scores = {
            "logic": {"score": 5, "feedback": "완벽"},
            "attitude": {"score": 5, "feedback": "완벽"},
        }
        _, weighted = _renormalize_and_score(raw_scores, "OPENING")
        assert weighted == 100.0
