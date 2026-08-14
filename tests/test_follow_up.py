import sys
from unittest.mock import MagicMock

# follow_up 모듈의 무거운 의존성 임포트 체인 방지
for mod in ("app.services.resume_vector_store", "langgraph", "langgraph.graph"):
    if mod not in sys.modules:
        sys.modules[mod] = MagicMock()

from app.schemas.follow_up import FollowUpRequest, QATurn
from app.services.follow_up import (
    DIFFICULTY_CRITERIA,
    _build_conversation_text,
    _build_system_prompt,
)


class TestBuildConversationText:
    def test_single_turn(self):
        req = FollowUpRequest(
            interview_type="technical",
            difficulty="middle",
            conversation=[
                QATurn(question="RESTful API에 대해 설명해주세요.", answer="HTTP 메서드를 사용합니다.")
            ],
        )
        text = _build_conversation_text(req)
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
        text = _build_conversation_text(req)
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
        text = _build_conversation_text(req)
        assert "인성 면접" in text
        assert "난이도: 하" in text


class TestBuildSystemPrompt:
    def test_low_difficulty(self):
        prompt = _build_system_prompt("low")
        assert "관대한 평가" in prompt

    def test_middle_difficulty(self):
        prompt = _build_system_prompt("middle")
        assert "보통 평가" in prompt

    def test_high_difficulty(self):
        prompt = _build_system_prompt("high")
        assert "엄격한 평가" in prompt

    def test_contains_base_prompt(self):
        prompt = _build_system_prompt("middle")
        assert "시니어 개발자 면접관" in prompt

    def test_all_difficulties_have_criteria(self):
        for key in ("low", "middle", "high"):
            assert key in DIFFICULTY_CRITERIA
