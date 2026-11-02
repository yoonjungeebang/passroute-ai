from fastapi import APIRouter

from app.schemas.debate import (
    DebateClosingRequest,
    DebateClosingResponse,
    DebateOpeningRequest,
    DebateOpeningResponse,
    DebateRebuttalRequest,
    DebateRebuttalResponse,
    InterviewerClosingRequest,
    InterviewerClosingResponse,
    InterviewerCueRequest,
    InterviewerCueResponse,
    InterviewerOpeningRequest,
    InterviewerOpeningResponse,
    TopicDetailRequest,
    TopicDetailResponse,
    TopicSuggestRequest,
    TopicSuggestResponse,
)
from app.services.debate_llm_service import (
    generate_competitor_closing,
    generate_competitor_opening,
    generate_competitor_rebuttal,
    generate_interviewer_closing,
    generate_interviewer_cue,
    generate_interviewer_opening,
    generate_topic_detail,
    suggest_debate_topics,
)

router = APIRouter(tags=["토론 면접"])


@router.post("/debate/interviewer-opening", response_model=InterviewerOpeningResponse,
              summary="면접관 오프닝 발언 생성")
async def interviewer_opening_endpoint(req: InterviewerOpeningRequest) -> InterviewerOpeningResponse:
    """토론 면접 시작 시 면접관의 오프닝 발언을 생성한다."""
    return await generate_interviewer_opening(req)


@router.post("/debate/opening", response_model=DebateOpeningResponse,
              summary="AI 상대방 입론 생성")
async def competitor_opening_endpoint(req: DebateOpeningRequest) -> DebateOpeningResponse:
    """사용자의 입론에 대응하는 AI 상대방의 입론을 생성한다."""
    return await generate_competitor_opening(req)


@router.post("/debate/rebuttal", response_model=DebateRebuttalResponse,
              summary="AI 상대방 반론 생성")
async def competitor_rebuttal_endpoint(req: DebateRebuttalRequest) -> DebateRebuttalResponse:
    """사용자의 발언에 대한 AI 상대방의 반론을 생성한다."""
    return await generate_competitor_rebuttal(req)


@router.post("/debate/closing", response_model=DebateClosingResponse,
              summary="AI 상대방 최종발언 생성")
async def competitor_closing_endpoint(req: DebateClosingRequest) -> DebateClosingResponse:
    """사용자의 최종발언에 대응하는 AI 상대방의 최종발언을 생성한다."""
    return await generate_competitor_closing(req)


@router.post("/debate/interviewer-closing", response_model=InterviewerClosingResponse,
              summary="면접관 클로징 발언 생성")
async def interviewer_closing_endpoint(req: InterviewerClosingRequest) -> InterviewerClosingResponse:
    """토론 종료 시 면접관의 클로징 발언을 생성한다."""
    return await generate_interviewer_closing(req)


@router.post("/debate/interviewer-cue", response_model=InterviewerCueResponse,
              summary="면접관 큐 멘트 생성")
async def interviewer_cue_endpoint(req: InterviewerCueRequest) -> InterviewerCueResponse:
    """토론 진행 중 면접관의 전환 큐 멘트를 생성한다."""
    return await generate_interviewer_cue(req)


@router.post("/debate/topics/suggest", response_model=TopicSuggestResponse,
              summary="토론 주제 추천")
async def topic_suggest_endpoint(req: TopicSuggestRequest) -> TopicSuggestResponse:
    """직무·이력서를 기반으로 토론 면접 주제를 추천한다."""
    return await suggest_debate_topics(req)


@router.post("/debate/topics/detail", response_model=TopicDetailResponse,
              summary="토론 주제 상세 정보 생성")
async def topic_detail_endpoint(req: TopicDetailRequest) -> TopicDetailResponse:
    """선택된 토론 주제에 대한 배경 설명과 찬반 논점을 생성한다."""
    return await generate_topic_detail(req)
