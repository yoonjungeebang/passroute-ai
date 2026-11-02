import asyncio
import json
import logging

from anthropic import APIError, APITimeoutError, AsyncAnthropic

from app.core.config import settings
from app.core.sources import BLOG_SOURCES, JD_SOURCES
from app.schemas.follow_up import FollowUpRequest, FollowUpResponse
from app.services.resume_vector_store import query_crawled_data, query_resume
from app.services.tts_service import synthesize_and_upload

logger = logging.getLogger(__name__)

_client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)

# ──────────────────────────────────────────────
# 프롬프트
# ──────────────────────────────────────────────

_TECHNICAL_SYSTEM_PROMPT = """\
당신은 실무 경험이 풍부한 시니어 개발자 면접관입니다.
지원자의 답변에서 언급된 구체적인 기술·개념을 포착하여, 실제 이해도와 실무 역량을 검증하는 날카로운 꼬리 질문을 생성하세요.

## 꼬리 질문 전략
답변에서 포착한 기술 키워드를 기반으로, 아래 전략 중 가장 적합한 것을 선택하세요:

1. **동작 원리 검증**: 기술을 언급했다면, 그 기술의 내부 동작을 이해하는지 확인
   - 예: "Redis를 캐시로 사용했다" → "Redis의 eviction 정책은 어떤 걸 사용하셨고, 그 이유는?"
2. **선택 근거 확인**: 특정 기술을 선택한 이유와 대안 비교를 확인
   - 예: "메시지 큐로 Kafka를 도입했다" → "RabbitMQ 대신 Kafka를 선택한 이유는?"
3. **장애·한계 경험 확인**: 해당 기술 사용 시 겪은 문제와 해결 과정을 확인
   - 예: "Docker로 배포했다" → "컨테이너 환경에서 겪은 가장 까다로운 문제는?"
4. **설계 의사결정 검증**: 아키텍처나 설계 선택의 트레이드오프를 확인
   - 예: "MSA로 전환했다" → "서비스 간 통신은 동기/비동기 중 어떤 방식을 선택했나요?"
5. **수치·성과 검증**: 정량적 결과를 주장했다면, 측정 방법과 기준을 확인
   - 예: "성능을 50% 개선했다" → "그 수치는 어떤 지표로 측정한 건가요?"

{difficulty_criteria}
{context_guidelines}
{common_rules}\
"""

_PERSONALITY_SYSTEM_PROMPT = """\
당신은 채용 면접 경험이 풍부한 인사 담당자입니다.
지원자의 답변에서 드러나는 가치관, 태도, 협업 방식, 성장 가능성을 심층적으로 파악하는 꼬리 질문을 생성하세요.

## 꼬리 질문 전략
답변에서 포착한 경험·태도를 기반으로, 아래 전략 중 가장 적합한 것을 선택하세요:

1. **행동 구체화**: 추상적인 태도 언급을 구체적 행동으로 확인
   - 예: "소통을 잘한다" → "팀원과 의견이 충돌했을 때 실제로 어떻게 해결하셨나요?"
2. **동기·가치관 확인**: 선택이나 행동 뒤의 동기를 파악
   - 예: "리더 역할을 맡았다" → "그 역할을 자원한 건가요? 어떤 점이 동기가 되었나요?"
3. **갈등·실패 경험 탐색**: 어려운 상황에서의 대처 방식을 확인
   - 예: "프로젝트를 성공적으로 마쳤다" → "과정에서 가장 힘들었던 순간은? 어떻게 극복하셨나요?"
4. **자기인식 확인**: 본인의 강점·약점에 대한 인식 수준을 파악
   - 예: "꼼꼼하다" → "꼼꼼함이 오히려 부정적으로 작용한 적은 없었나요?"
5. **성장·학습 태도 확인**: 경험에서 무엇을 배웠는지 확인
   - 예: "새로운 기술을 배웠다" → "그 과정에서 가장 어려웠던 점과 극복 방법은?"

{difficulty_criteria}
{context_guidelines}
{common_rules}\
"""

_COMMON_RULES = """\

## 꼬리 질문을 생성해야 하는 경우
- 답변이 표면적이거나 추상적인 수준에 머문 경우
- 결과만 말하고 과정·근거·트레이드오프 설명이 빠진 경우
- 이력서에 적힌 경험과 답변 사이에 괴리가 있는 경우
- 답변에 논리적 허점이나 모순이 있는 경우

## 꼬리 질문을 생성하지 않아야 하는 경우
- 답변이 이미 원리·근거·경험까지 충분히 다룬 경우
- 원래 질문이 단순 사실 확인(예/아니오)인 경우
- 추가 질문이 면접 흐름에 도움이 되지 않는 경우

## 중복 방지 지침 (필수)
- 대화 이력에 이미 등장한 질문과 동일하거나 유사한 질문을 절대 반복하지 마세요
- "구체적으로 설명해 주세요" 같은 포괄적 요청 대신, 특정 기술·상황을 지목하여 질문하세요
- 꼬리 질문은 반드시 최신 답변에서 새롭게 드러난 내용을 타겟으로 해야 합니다

## 응답 형식
반드시 아래 JSON 형식으로만 응답하세요. 다른 텍스트를 포함하지 마세요.
{{
  "has_follow_up": true 또는 false,
  "follow_up_question": "꼬리 질문 텍스트" 또는 null,
  "reason": "판단 근거"
}}"""

_CONTEXT_GUIDELINES = """\

## 이력서 활용 지침
- 이력서 정보가 제공되면, 지원자가 실제로 경험했다고 주장하는 내용과 답변을 대조하세요
- 이력서에 관련 경험이 있는데 답변에서 언급하지 않았다면, 해당 경험을 끌어내는 꼬리 질문을 생성하세요

## 업계 참고 자료 활용 지침
- 채용공고, 기술블로그, 뉴스 등의 참고 자료가 제공되면, 업계에서 실제로 요구하는 역량과 답변을 대조하세요
- 참고 자료가 없더라도 답변 자체의 품질만으로 판단하세요"""

DIFFICULTY_CRITERIA = {
    "low": (
        "\n## 난이도별 판단 기준\n"
        "현재 난이도: 하 (관대한 평가)\n"
        "답변이 질문의 핵심 개념을 포함하고 있다면 추가 질문이 필요하지 않습니다.\n"
        "기본적인 이해를 확인하는 수준으로 판단하세요.\n"
        "구체적 사례나 경험이 없어도, 핵심 개념만 언급했다면 충분합니다."
    ),
    "middle": (
        "\n## 난이도별 판단 기준\n"
        "현재 난이도: 중 (보통 평가)\n"
        "답변에 개념 설명과 함께 구체적인 경험이나 사례가 포함되어야 합니다.\n"
        "경험이나 사례가 빠져 있다면 이를 확인하는 꼬리질문을 생성하세요.\n"
        "개념만 나열한 답변은 부족하며, 적용 경험까지 확인해야 합니다."
    ),
    "high": (
        "\n## 난이도별 판단 기준\n"
        "현재 난이도: 상 (엄격한 평가)\n"
        "답변에 깊은 이해, 트레이드오프 분석, 대안 제시가 포함되어야 합니다.\n"
        "표면적이거나 암기식 답변이라면 반드시 꼬리질문을 생성하세요.\n"
        "단순 개념 설명이나 경험 나열만으로는 부족하며, "
        "왜 그 선택을 했는지, 다른 대안은 무엇이었는지까지 확인하세요."
    ),
}

DIFFICULTY_LABELS = {
    "low": "하",
    "middle": "중",
    "high": "상",
}

INTERVIEW_TYPE_LABELS = {
    "technical": "기술 면접",
    "personality": "인성 면접",
}

# 면접 유형별 검색할 크롤링 데이터 source
_SOURCE_FILTER: dict[str, list[str]] = {
    "technical": BLOG_SOURCES + JD_SOURCES,
    "personality": JD_SOURCES,
}


# ──────────────────────────────────────────────
# 프롬프트 빌더
# ──────────────────────────────────────────────

def _build_system_prompt(interview_type: str, difficulty: str) -> str:
    """면접 유형과 난이도에 맞는 시스템 프롬프트를 구성한다."""
    template = (
        _TECHNICAL_SYSTEM_PROMPT
        if interview_type == "technical"
        else _PERSONALITY_SYSTEM_PROMPT
    )
    return template.format(
        difficulty_criteria=DIFFICULTY_CRITERIA[difficulty],
        context_guidelines=_CONTEXT_GUIDELINES,
        common_rules=_COMMON_RULES,
    )


def _build_user_message(request: FollowUpRequest, resume_context: str, crawled_context: str) -> str:
    """대화 이력 + 컨텍스트를 결합한 user 메시지를 구성한다."""
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

    if len(request.conversation) > 1:
        asked = [turn.question for turn in request.conversation]
        parts.append("\n[이미 질문한 내용 - 절대 반복 금지]")
        for q in asked:
            parts.append(f"- {q}")

    if resume_context:
        parts.append(f"\n[지원자 이력서 관련 정보]\n{resume_context}")

    if crawled_context:
        parts.append(f"\n[업계 참고 자료 (채용공고/기술블로그/뉴스)]\n{crawled_context}")

    return "\n".join(parts)


# ──────────────────────────────────────────────
# 컨텍스트 검색
# ──────────────────────────────────────────────

def _format_crawled_data(crawled_data: dict[str, str]) -> str:
    """백엔드가 전달한 crawled_data를 프롬프트용 텍스트로 변환한다."""
    source_labels = {
        "tech_blog": "기술블로그",
        "jd": "채용공고",
        "news": "뉴스",
    }
    parts = []
    for key, text in crawled_data.items():
        if text and text.strip():
            label = source_labels.get(key, key)
            parts.append(f"[{label}]\n{text.strip()}")
    return "\n\n".join(parts)


async def _noop() -> str:
    return ""


async def _search_context(request: FollowUpRequest) -> tuple[str, str]:
    """이력서와 크롤링 데이터를 병렬 검색한다."""
    last_answer = request.conversation[-1].answer
    search_query = last_answer[:500].strip()

    # 이력서 검색
    resume_task = (
        query_resume(request.user_id, search_query)
        if request.user_id
        else _noop()
    )

    # 크롤링 데이터: 백엔드가 직접 전달했으면 사용, 아니면 pgvector 검색
    if request.crawled_data:
        crawled_context = _format_crawled_data(request.crawled_data)
        resume_context = await resume_task
        if isinstance(resume_context, Exception):
            logger.warning("이력서 검색 실패: %s", resume_context)
            resume_context = ""
        return resume_context, crawled_context

    sources = _SOURCE_FILTER.get(request.interview_type, JD_SOURCES)
    crawled_task = query_crawled_data(search_query, sources)

    results = await asyncio.gather(resume_task, crawled_task, return_exceptions=True)

    resume_context = results[0] if not isinstance(results[0], Exception) else ""
    crawled_context = results[1] if not isinstance(results[1], Exception) else ""

    if isinstance(results[0], Exception):
        logger.warning("이력서 검색 실패: %s", results[0])
    if isinstance(results[1], Exception):
        logger.warning("크롤링 데이터 검색 실패: %s", results[1])

    return resume_context, crawled_context


# ──────────────────────────────────────────────
# 외부 인터페이스
# ──────────────────────────────────────────────

async def generate_follow_up(request: FollowUpRequest) -> FollowUpResponse:
    """꼬리 질문을 생성한다.

    1단계: 이력서 + 크롤링 데이터 검색 (pgvector / 백엔드 직접 전달)
    2단계: 단일 LLM 호출 (대화이력 + 컨텍스트 → 꼬리질문 생성)
    """
    resume_context, crawled_context = await _search_context(request)

    system_prompt = _build_system_prompt(request.interview_type, request.difficulty)
    user_message = _build_user_message(request, resume_context, crawled_context)

    try:
        response = await _client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=512,
            temperature=0.7,
            system=system_prompt,
            messages=[
                {"role": "user", "content": user_message},
            ],
        )
        content = response.content[0].text
        if not content:
            raise ValueError("Empty response content")
        parsed = json.loads(content.strip())
        follow_up_question = parsed.get("follow_up_question")
        audio_url = None
        if parsed["has_follow_up"] and follow_up_question:
            audio_url = await synthesize_and_upload(
                follow_up_question, "tts/follow-up"
            )
        return FollowUpResponse(
            has_follow_up=parsed["has_follow_up"],
            follow_up_question=follow_up_question,
            reason=parsed.get("reason"),
            audio_url=audio_url,
        )
    except APITimeoutError:
        logger.error("꼬리 질문 생성 타임아웃")
        return FollowUpResponse(
            has_follow_up=False, reason="AI 서비스 응답 시간 초과"
        )
    except APIError as e:
        logger.error("꼬리 질문 생성 API 오류: %s", e)
        return FollowUpResponse(
            has_follow_up=False, reason="AI 서비스 호출 실패"
        )
    except (json.JSONDecodeError, KeyError, TypeError, IndexError, AttributeError, ValueError) as e:
        logger.error("꼬리 질문 응답 파싱 실패: %s", e)
        return FollowUpResponse(
            has_follow_up=False, reason="AI 응답 파싱 실패"
        )
