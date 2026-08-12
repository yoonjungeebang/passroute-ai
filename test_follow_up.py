"""꼬리 질문 생성 테스트 스크립트 (LangGraph 파이프라인 단계별 출력)."""

import asyncio
import json
import time

from dotenv import load_dotenv

load_dotenv()

from app.schemas.follow_up import FollowUpRequest, FollowUpResponse, QATurn
from app.services.follow_up import (
    FollowUpState,
    _build_conversation_text,
    _build_graph,
    analyze_answer,
    generate_question,
    search_context,
)


def _print_header(title: str):
    print(f"\n{'=' * 70}")
    print(f"  {title}")
    print(f"{'=' * 70}")


def _print_step(step: str, content):
    print(f"\n--- [{step}] {'─' * 50}")
    if isinstance(content, dict):
        print(json.dumps(content, ensure_ascii=False, indent=2))
    else:
        print(content)


async def run_pipeline_verbose(request: FollowUpRequest) -> FollowUpResponse:
    """파이프라인을 단계별로 실행하며 각 노드의 입출력을 출력한다."""
    user_message = _build_conversation_text(request)
    _print_step("입력 텍스트", user_message)

    state: FollowUpState = {
        "request": request,
        "user_message": user_message,
        "analysis": {},
        "resume_context": "",
        "crawled_context": "",
        "response": FollowUpResponse(has_follow_up=False),
    }

    # 노드 1: 답변 분석
    t0 = time.perf_counter()
    result = await analyze_answer(state)
    state.update(result)
    t1 = time.perf_counter()
    _print_step(f"노드 1 - 답변 분석 ({t1 - t0:.2f}s)", state["analysis"])

    # 노드 2: ChromaDB 검색
    t0 = time.perf_counter()
    try:
        result = await search_context(state)
        state.update(result)
    except Exception as e:
        print(f"\n  (ChromaDB 미연결 - 검색 스킵: {e})")
    t1 = time.perf_counter()
    _print_step(
        f"노드 2 - 컨텍스트 검색 ({t1 - t0:.2f}s)",
        {
            "resume_context": state["resume_context"][:200] or "(없음)",
            "crawled_context": state["crawled_context"][:200] or "(없음)",
        },
    )

    # 노드 3: 꼬리질문 생성
    t0 = time.perf_counter()
    result = await generate_question(state)
    state.update(result)
    t1 = time.perf_counter()

    resp: FollowUpResponse = state["response"]
    _print_step(
        f"노드 3 - 꼬리질문 생성 ({t1 - t0:.2f}s)",
        {
            "has_follow_up": resp.has_follow_up,
            "follow_up_question": resp.follow_up_question,
            "reason": resp.reason,
        },
    )
    return resp


async def main():
    # 테스트 1: 피상적인 답변 → 꼬리질문 생성 예상
    _print_header("테스트 1 | 피상적 답변 | difficulty: middle")
    await run_pipeline_verbose(
        FollowUpRequest(
            interview_type="technical",
            difficulty="middle",
            conversation=[
                QATurn(
                    question="RESTful API 설계 원칙에 대해 설명해주세요.",
                    answer="HTTP 메서드를 사용하는 것입니다.",
                )
            ],
        )
    )

    # 테스트 2: 구체적인 답변 → 꼬리질문 미생성 예상
    _print_header("테스트 2 | 구체적 답변 | difficulty: middle")
    await run_pipeline_verbose(
        FollowUpRequest(
            interview_type="technical",
            difficulty="middle",
            conversation=[
                QATurn(
                    question="RESTful API 설계 원칙에 대해 설명해주세요.",
                    answer=(
                        "RESTful API는 리소스를 URI로 표현하고 HTTP 메서드로 행위를 구분합니다. "
                        "GET은 조회, POST는 생성, PUT은 전체 수정, PATCH는 부분 수정, DELETE는 삭제에 사용합니다. "
                        "실제 프로젝트에서 /api/users/{id}/orders 형태로 리소스 간 관계를 표현했고, "
                        "상태 코드도 200, 201, 404, 409 등을 구분하여 클라이언트가 응답을 명확히 처리할 수 있도록 했습니다."
                    ),
                )
            ],
        )
    )

    # 테스트 3: 높은 난이도 + 표면적 답변 → 꼬리질문 생성 예상
    _print_header("테스트 3 | 표면적 답변 | difficulty: high")
    await run_pipeline_verbose(
        FollowUpRequest(
            interview_type="technical",
            difficulty="high",
            conversation=[
                QATurn(
                    question="데이터베이스 인덱스의 동작 원리와 트레이드오프에 대해 설명해주세요.",
                    answer="인덱스를 걸면 조회가 빨라집니다. B-Tree 구조를 사용합니다.",
                )
            ],
        )
    )

    # 테스트 4: 꼬리질문 2턴째 (중복 방지 테스트)
    _print_header("테스트 4 | 꼬리질문 2턴 | difficulty: high (중복 방지)")
    await run_pipeline_verbose(
        FollowUpRequest(
            interview_type="technical",
            difficulty="high",
            conversation=[
                QATurn(
                    question="Docker를 활용한 배포 경험에 대해 말씀해 주세요.",
                    answer="Docker Compose로 멀티 컨테이너 환경을 구성했고, Nginx 리버스 프록시와 함께 사용했습니다.",
                ),
                QATurn(
                    question="Docker Compose에서 서비스 간 네트워킹은 어떻게 구성하셨나요?",
                    answer="기본 bridge 네트워크를 사용했고, 서비스 이름으로 통신했습니다.",
                ),
            ],
        )
    )


asyncio.run(main())
