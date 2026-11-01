import sys
from unittest.mock import MagicMock

# follow_up 모듈의 무거운 의존성 임포트 체인 방지
for mod in ("app.services.resume_vector_store",):
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from app.schemas.follow_up import FollowUpRequest, QATurn
from app.services.follow_up import (
    DIFFICULTY_CRITERIA,
    _build_system_prompt,
    _build_user_message,
)


class TestBuildUserMessage:
    def test_single_turn(self):
        req = FollowUpRequest(
            interview_type="technical",
            difficulty="middle",
            conversation=[
                QATurn(question="RESTful API에 대해 설명해주세요.", answer="HTTP 메서드를 사용합니다.")
            ],
        )
        text = _build_user_message(req, "", "")
        assert "기술 면접" in text
        assert "난이도: 중" in text
        assert "원래 질문" in text
        assert "RESTful API" in text

    def test_multi_turn_adds_duplicate_warning(self):
        req = FollowUpRequest(
            interview_type="technical",
            difficulty="high",
            conversation=[
                QATurn(question="Docker 경험을 말씀해주세요.", answer="Docker Compose를 사용했습니다."),
                QATurn(question="네트워킹은 어떻게 구성했나요?", answer="bridge 네트워크를 사용했습니다."),
            ],
        )
        text = _build_user_message(req, "", "")
        assert "꼬리 질문 1" in text
        assert "절대 반복 금지" in text

    def test_personality_interview(self):
        req = FollowUpRequest(
            interview_type="personality",
            difficulty="low",
            conversation=[
                QATurn(question="팀워크 경험을 말해주세요.", answer="좋은 팀원들과 일했습니다.")
            ],
        )
        text = _build_user_message(req, "", "")
        assert "인성 면접" in text
        assert "난이도: 하" in text

    def test_resume_context_included(self):
        req = FollowUpRequest(
            interview_type="technical",
            difficulty="middle",
            conversation=[
                QATurn(question="경험을 말씀해주세요.", answer="Spring Boot를 사용했습니다.")
            ],
        )
        text = _build_user_message(req, "3년간 Spring Boot 개발", "")
        assert "이력서 관련 정보" in text
        assert "3년간 Spring Boot" in text

    def test_crawled_context_included(self):
        req = FollowUpRequest(
            interview_type="technical",
            difficulty="middle",
            conversation=[
                QATurn(question="경험을 말씀해주세요.", answer="Kafka를 사용했습니다.")
            ],
        )
        text = _build_user_message(req, "", "Kafka 경험 3년 이상 우대")
        assert "업계 참고 자료" in text
        assert "Kafka 경험" in text


class TestBuildSystemPrompt:
    def test_technical_low(self):
        prompt = _build_system_prompt("technical", "low")
        assert "시니어 개발자 면접관" in prompt
        assert "관대한 평가" in prompt

    def test_technical_middle(self):
        prompt = _build_system_prompt("technical", "middle")
        assert "보통 평가" in prompt

    def test_technical_high(self):
        prompt = _build_system_prompt("technical", "high")
        assert "엄격한 평가" in prompt

    def test_personality_prompt(self):
        prompt = _build_system_prompt("personality", "middle")
        assert "인사 담당자" in prompt
        assert "가치관" in prompt
        assert "시니어 개발자" not in prompt

    def test_all_difficulties_have_criteria(self):
        for key in ("low", "middle", "high"):
            assert key in DIFFICULTY_CRITERIA
