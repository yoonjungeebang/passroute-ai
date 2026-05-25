import json
import logging

from openai import APIError, APITimeoutError, AsyncOpenAI

from app.core.config import settings
from app.schemas.follow_up import FollowUpRequest, FollowUpResponse

logger = logging.getLogger(__name__)

_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)

_BASE_SYSTEM_PROMPT = """\
당신은 개발자 채용 면접관입니다.
지원자의 답변을 분석하여 꼬리 질문이 필요한지 판단하고, 필요하다면 꼬리 질문을 생성하세요.

## 꼬리 질문을 생성해야 하는 경우
- 답변이 모호하거나 피상적이어서 구체적인 확인이 필요한 경우
- 기술적 깊이를 더 확인해야 하는 경우 (예: 원리, 트레이드오프, 대안)
- 실제 경험을 검증해야 하는 경우 (예: 구체적 사례, 수치, 결과)
- 답변에 논리적 허점이나 모순이 있는 경우

## 꼬리 질문을 생성하지 않아야 하는 경우
- 답변이 이미 충분히 구체적이고 깊이가 있는 경우
- 원래 질문이 단순 사실 확인(예/아니오)인 경우
- 추가 질문이 면접 흐름에 도움이 되지 않는 경우
- 답변과 무관한 방향으로 흘러갈 위험이 있는 경우

## 난이도별 판단 기준
{difficulty_criteria}

## 응답 형식
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 포함하지 마세요.
{{
  "has_follow_up": true 또는 false,
  "follow_up_question": "꼬리 질문 텍스트" 또는 null,
  "reason": "판단 근거"
}}\
"""

DIFFICULTY_CRITERIA = {
    "low": (
        "현재 난이도: 하 (관대한 평가)\n"
        "답변이 질문의 핵심 개념을 포함하고 있다면 추가 질문이 필요하지 않습니다.\n"
        "기본적인 이해를 확인하는 수준으로 판단하세요.\n"
        "구체적 사례나 경험이 없어도, 핵심 개념만 언급했다면 충분합니다."
    ),
    "middle": (
        "현재 난이도: 중 (보통 평가)\n"
        "답변에 개념 설명과 함께 구체적인 경험이나 사례가 포함되어야 합니다.\n"
        "경험이나 사례가 빠져 있다면 이를 확인하는 꼬리질문을 생성하세요.\n"
        "개념만 나열한 답변은 부족하며, 적용 경험까지 확인해야 합니다."
    ),
    "high": (
        "현재 난이도: 상 (엄격한 평가)\n"
        "답변에 깊은 이해, 트레이드오프 분석, 대안 제시가 포함되어야 합니다.\n"
        "표면적이거나 암기식 답변이라면 반드시 꼬리질문을 생성하세요.\n"
        "단순 개념 설명이나 경험 나열만으로는 부족하며, "
        "왜 그 선택을 했는지, 다른 대안은 무엇이었는지까지 확인하세요."
    ),
}


def _build_system_prompt(difficulty: str) -> str:
    """난이도에 맞는 시스템 프롬프트를 구성한다."""
    criteria = DIFFICULTY_CRITERIA[difficulty]
    return _BASE_SYSTEM_PROMPT.format(difficulty_criteria=criteria)

DIFFICULTY_LABELS = {
    "low": "하",
    "middle": "중",
    "high": "상",
}

INTERVIEW_TYPE_LABELS = {
    "technical": "기술 면접",
    "personality": "인성 면접",
}


def _build_user_message(request: FollowUpRequest) -> str:
    """OpenAI에 전달할 사용자 메시지를 구성한다."""
    interview_type = INTERVIEW_TYPE_LABELS[request.interview_type]
    difficulty = DIFFICULTY_LABELS[request.difficulty]

    parts = [
        f"[면접 정보] 유형: {interview_type} | 난이도: {difficulty}",
        "\n[대화 이력]",
    ]

    for i, turn in enumerate(request.conversation):
        label = "원래 질문" if i == 0 else f"꼬리 질문 {i}"
        parts.append(f"{label}: {turn.question}")
        parts.append(f"답변: {turn.answer}")

    return "\n".join(parts)


async def generate_follow_up(
    request: FollowUpRequest,
) -> FollowUpResponse:
    """꼬리 질문을 생성한다.

    OpenAI가 답변의 적합성을 판단하여 꼬리 질문 생성 여부를 결정한다.
    스킵 판단과 턴 제한은 Spring 서버에서 사전 처리한다.
    """
    user_message = _build_user_message(request)

    system_prompt = _build_system_prompt(request.difficulty)

    try:
        response = await _client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            max_tokens=512,
            temperature=0.7,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            timeout=30.0,
        )
    except APITimeoutError:
        logger.error("OpenAI API 타임아웃")
        return FollowUpResponse(
            has_follow_up=False,
            reason="AI 서비스 응답 시간 초과",
        )
    except APIError as e:
        logger.error("OpenAI API 오류: %s", e)
        return FollowUpResponse(
            has_follow_up=False,
            reason="AI 서비스 호출 실패",
        )

    raw_text = response.choices[0].message.content.strip()

    try:
        parsed = json.loads(raw_text)
        return FollowUpResponse(
            has_follow_up=parsed["has_follow_up"],
            follow_up_question=parsed.get("follow_up_question"),
            reason=parsed.get("reason"),
        )
    except (json.JSONDecodeError, KeyError, TypeError):
        logger.error("OpenAI 응답 파싱 실패: %s", raw_text)
        return FollowUpResponse(
            has_follow_up=False,
            reason="AI 응답 파싱 실패",
        )
