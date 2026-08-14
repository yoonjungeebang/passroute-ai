import pytest
from pydantic import ValidationError

from app.schemas.evaluation import (
    ItemAvg,
    LLMScores,
    ScoreItem,
    StarEvaluationDetail,
)
from app.schemas.follow_up import FollowUpRequest, FollowUpResponse, QATurn
from app.schemas.prompt_builder import (
    GeneratedQuestion,
    QuestionGenerateRequest,
    QuestionGenerateResponse,
)


class TestFollowUpSchemas:
    def test_valid_request(self):
        req = FollowUpRequest(
            interview_type="technical",
            difficulty="middle",
            conversation=[QATurn(question="질문", answer="답변")],
        )
        assert req.interview_type == "technical"

    def test_user_id_coerced_to_str(self):
        req = FollowUpRequest(
            interview_type="technical",
            difficulty="low",
            conversation=[QATurn(question="q", answer="a")],
            user_id=123,
        )
        assert req.user_id == "123"

    def test_empty_conversation_rejected(self):
        with pytest.raises(ValidationError):
            FollowUpRequest(
                interview_type="technical",
                difficulty="low",
                conversation=[],
            )

    def test_invalid_interview_type_rejected(self):
        with pytest.raises(ValidationError):
            FollowUpRequest(
                interview_type="invalid",
                difficulty="low",
                conversation=[QATurn(question="q", answer="a")],
            )

    def test_response_no_followup(self):
        resp = FollowUpResponse(has_follow_up=False)
        assert resp.follow_up_question is None

    def test_response_with_followup(self):
        resp = FollowUpResponse(
            has_follow_up=True,
            follow_up_question="꼬리 질문입니다",
            reason="답변이 부족합니다",
        )
        assert resp.follow_up_question == "꼬리 질문입니다"


class TestQuestionGenerateSchemas:
    def test_valid_request(self):
        req = QuestionGenerateRequest(
            persona="HR_MANAGER",
            pressure_level=5,
            difficulty="NORMAL",
            followup_count=2,
            interview_type="PERSONALITY",
            interview_format="ONE_ON_ONE",
            cover_letter="자기소개서입니다.",
        )
        assert req.question_count == 5

    def test_pressure_level_bounds(self):
        with pytest.raises(ValidationError):
            QuestionGenerateRequest(
                persona="HR_MANAGER",
                pressure_level=11,
                difficulty="NORMAL",
                followup_count=0,
                interview_type="PERSONALITY",
                interview_format="ONE_ON_ONE",
                cover_letter="test",
            )

    def test_followup_count_bounds(self):
        with pytest.raises(ValidationError):
            QuestionGenerateRequest(
                persona="HR_MANAGER",
                pressure_level=5,
                difficulty="NORMAL",
                followup_count=6,
                interview_type="PERSONALITY",
                interview_format="ONE_ON_ONE",
                cover_letter="test",
            )

    def test_generated_question(self):
        q = GeneratedQuestion(
            question="경험을 말해주세요.",
            followup_questions=["왜요?", "어떻게요?"],
            intent="경험 확인",
        )
        assert len(q.followup_questions) == 2

    def test_response(self):
        resp = QuestionGenerateResponse(
            persona="TECH_INTERVIEWER",
            questions=[GeneratedQuestion(question="질문1")],
        )
        assert len(resp.questions) == 1


class TestEvaluationSchemas:
    def test_score_item_bounds(self):
        with pytest.raises(ValidationError):
            ScoreItem(score=0, feedback="too low")
        with pytest.raises(ValidationError):
            ScoreItem(score=6, feedback="too high")

    def test_valid_score_item(self):
        item = ScoreItem(score=3, feedback="보통입니다")
        assert item.score == 3

    def test_star_evaluation_non_applicable(self):
        detail = StarEvaluationDetail(
            applicable=False,
            reason="기술 개념 질문",
        )
        assert detail.star_breakdown is None
        assert detail.star_score is None

    def test_star_evaluation_non_applicable_with_breakdown_rejected(self):
        with pytest.raises(ValidationError):
            StarEvaluationDetail(
                applicable=False,
                reason="기술 개념 질문",
                star_score=3,
            )

    def test_item_avg_bounds(self):
        with pytest.raises(ValidationError):
            ItemAvg(avg=0, evaluated_count=1)
        with pytest.raises(ValidationError):
            ItemAvg(avg=6, evaluated_count=1)

    def test_llm_scores_technical(self):
        def s(score=3):
            return ScoreItem(score=score, feedback="ok")
        scores = LLMScores(
            relevance=s(), logic=s(), specificity=s(),
            conciseness=s(), clarity=s(), job_relevance=s(),
            accuracy=s(), depth=s(),
        )
        assert scores.authenticity is None
