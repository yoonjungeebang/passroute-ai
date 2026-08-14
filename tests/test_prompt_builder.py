import sys
from unittest.mock import MagicMock

# prompt_builder -> resume_vector_store -> database 임포트 체인의 부작용 방지
# resume_vector_store가 아직 로드되지 않았으면 mock으로 대체
if "app.services.resume_vector_store" not in sys.modules:
    sys.modules["app.services.resume_vector_store"] = MagicMock()

from app.services.prompt_builder import (
    _difficulty_guideline,
    _followup_guideline,
    _format_guideline,
    _interview_type_guideline,
    _pressure_guideline,
    _resolve_crawled_sources,
    build_prompt,
)


class TestPressureGuideline:
    def test_low(self):
        for level in (0, 1, 2, 3):
            result = _pressure_guideline(level)
            assert "낮음" in result

    def test_mid(self):
        for level in (4, 5, 6):
            result = _pressure_guideline(level)
            assert "중간" in result

    def test_high(self):
        for level in (7, 8, 9, 10):
            result = _pressure_guideline(level)
            assert "높음" in result


class TestDifficultyGuideline:
    def test_easy(self):
        assert "기초" in _difficulty_guideline("EASY")

    def test_normal(self):
        assert "중간" in _difficulty_guideline("NORMAL")

    def test_hard(self):
        assert "심화" in _difficulty_guideline("HARD")


class TestFollowupGuideline:
    def test_zero(self):
        result = _followup_guideline(0)
        assert "꼬리질문 없이" in result

    def test_one(self):
        result = _followup_guideline(1)
        assert "1개" in result

    def test_many(self):
        result = _followup_guideline(4)
        assert "4개" in result
        assert "빈틈" in result


class TestInterviewTypeGuideline:
    def test_personality(self):
        result = _interview_type_guideline("PERSONALITY")
        assert "인성" in result

    def test_technical(self):
        result = _interview_type_guideline("TECHNICAL")
        assert "기술" in result


class TestFormatGuideline:
    def test_one_on_one(self):
        result = _format_guideline("ONE_ON_ONE")
        assert "1:1" in result

    def test_debate(self):
        result = _format_guideline("DEBATE")
        assert "토론" in result


class TestResolveCrawledSources:
    def test_debate_format(self):
        sources, label = _resolve_crawled_sources("TECHNICAL", "DEBATE")
        assert "naver_news" in sources

    def test_technical_type(self):
        sources, label = _resolve_crawled_sources("TECHNICAL", "ONE_ON_ONE")
        assert "tech_blog" in sources

    def test_personality_type(self):
        sources, label = _resolve_crawled_sources("PERSONALITY", "ONE_ON_ONE")
        assert "jobkorea" in sources


class TestBuildPrompt:
    def test_contains_persona(self):
        prompt = build_prompt(
            persona="HR_MANAGER",
            pressure_level=5,
            difficulty="NORMAL",
            followup_count=2,
            interview_type="PERSONALITY",
            interview_format="ONE_ON_ONE",
            cover_letter="저는 열정적인 개발자입니다.",
        )
        assert "HR 담당자" in prompt

    def test_contains_cover_letter(self):
        cover = "저는 3년차 백엔드 개발자입니다."
        prompt = build_prompt(
            persona="TECH_INTERVIEWER",
            pressure_level=7,
            difficulty="HARD",
            followup_count=0,
            interview_type="TECHNICAL",
            interview_format="ONE_ON_ONE",
            cover_letter=cover,
        )
        assert cover in prompt

    def test_optional_resume(self):
        prompt = build_prompt(
            persona="TEAM_LEAD",
            pressure_level=3,
            difficulty="EASY",
            followup_count=1,
            interview_type="TECHNICAL",
            interview_format="ONE_ON_ONE",
            cover_letter="자소서",
            resume="이력서 내용",
        )
        assert "[이력서]" in prompt
        assert "이력서 내용" in prompt

    def test_no_resume(self):
        prompt = build_prompt(
            persona="TEAM_LEAD",
            pressure_level=3,
            difficulty="EASY",
            followup_count=1,
            interview_type="TECHNICAL",
            interview_format="ONE_ON_ONE",
            cover_letter="자소서",
        )
        assert "[이력서]" not in prompt

    def test_optional_portfolio(self):
        prompt = build_prompt(
            persona="EXECUTIVE",
            pressure_level=5,
            difficulty="NORMAL",
            followup_count=0,
            interview_type="PERSONALITY",
            interview_format="ONE_ON_ONE",
            cover_letter="자소서",
            portfolio="포트폴리오 내용",
        )
        assert "[포트폴리오]" in prompt

    def test_followup_zero_json_format(self):
        prompt = build_prompt(
            persona="HR_MANAGER",
            pressure_level=1,
            difficulty="EASY",
            followup_count=0,
            interview_type="PERSONALITY",
            interview_format="ONE_ON_ONE",
            cover_letter="자소서",
        )
        assert '"followup_questions": []' in prompt

    def test_followup_nonzero_json_format(self):
        prompt = build_prompt(
            persona="HR_MANAGER",
            pressure_level=1,
            difficulty="EASY",
            followup_count=3,
            interview_type="PERSONALITY",
            interview_format="ONE_ON_ONE",
            cover_letter="자소서",
        )
        assert "꼬리질문3" in prompt

    def test_crawled_context_included(self):
        prompt = build_prompt(
            persona="TECH_INTERVIEWER",
            pressure_level=5,
            difficulty="NORMAL",
            followup_count=0,
            interview_type="TECHNICAL",
            interview_format="ONE_ON_ONE",
            cover_letter="자소서",
            crawled_context="크롤링 데이터",
            crawled_label="참고 자료",
        )
        assert "[참고 자료]" in prompt
        assert "크롤링 데이터" in prompt
