import pytest

from app.schemas.evaluation import LLMScores, ScoreItem
from app.services.llm_service import _merge_weights, _parse_json


class TestParseJson:
    def test_plain_json(self):
        result = _parse_json('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_markdown_fence(self):
        text = '```json\n{"key": "value"}\n```'
        result = _parse_json(text)
        assert result == {"key": "value"}

    def test_json_with_generic_fence(self):
        text = '```\n{"key": 42}\n```'
        result = _parse_json(text)
        assert result == {"key": 42}

    def test_json_with_whitespace(self):
        text = '  \n  {"a": 1}  \n  '
        result = _parse_json(text)
        assert result == {"a": 1}

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            _parse_json("not json")

    def test_nested_json(self):
        text = '{"scores": {"logic": {"score": 4, "feedback": "좋습니다"}}}'
        result = _parse_json(text)
        assert result["scores"]["logic"]["score"] == 4


class TestMergeWeights:
    def _make_score(self, score: int = 3) -> ScoreItem:
        return ScoreItem(score=score, feedback="테스트")

    def test_technical_weights(self):
        scores = LLMScores(
            relevance=self._make_score(4),
            logic=self._make_score(3),
            specificity=self._make_score(5),
            conciseness=self._make_score(4),
            clarity=self._make_score(3),
            job_relevance=self._make_score(2),
            accuracy=self._make_score(4),
            depth=self._make_score(3),
            authenticity=None,
            growth=None,
        )
        result = _merge_weights(scores, "technical")
        assert result.relevance.weight == 0.15
        assert result.accuracy is not None
        assert result.accuracy.weight == 0.15
        assert result.authenticity is None
        assert result.growth is None

    def test_personality_weights(self):
        scores = LLMScores(
            relevance=self._make_score(4),
            logic=self._make_score(3),
            specificity=self._make_score(5),
            conciseness=self._make_score(4),
            clarity=self._make_score(3),
            job_relevance=self._make_score(2),
            accuracy=None,
            depth=None,
            authenticity=self._make_score(4),
            growth=self._make_score(3),
        )
        result = _merge_weights(scores, "personality")
        assert result.logic.weight == 0.20
        assert result.authenticity is not None
        assert result.authenticity.weight == 0.10
        assert result.accuracy is None
        assert result.depth is None
