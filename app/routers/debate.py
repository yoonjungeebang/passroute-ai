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
    InterviewerOpeningRequest,
    InterviewerOpeningResponse,
)
from app.services.debate_llm_service import (
    generate_competitor_closing,
    generate_competitor_opening,
    generate_competitor_rebuttal,
    generate_interviewer_closing,
    generate_interviewer_opening,
)

router = APIRouter(tags=["debate"])


@router.post("/debate/interviewer-opening", response_model=InterviewerOpeningResponse)
async def interviewer_opening_endpoint(req: InterviewerOpeningRequest) -> InterviewerOpeningResponse:
    return await generate_interviewer_opening(req)


@router.post("/debate/opening", response_model=DebateOpeningResponse)
async def competitor_opening_endpoint(req: DebateOpeningRequest) -> DebateOpeningResponse:
    return await generate_competitor_opening(req)


@router.post("/debate/rebuttal", response_model=DebateRebuttalResponse)
async def competitor_rebuttal_endpoint(req: DebateRebuttalRequest) -> DebateRebuttalResponse:
    return await generate_competitor_rebuttal(req)


@router.post("/debate/closing", response_model=DebateClosingResponse)
async def competitor_closing_endpoint(req: DebateClosingRequest) -> DebateClosingResponse:
    return await generate_competitor_closing(req)


@router.post("/debate/interviewer-closing", response_model=InterviewerClosingResponse)
async def interviewer_closing_endpoint(req: InterviewerClosingRequest) -> InterviewerClosingResponse:
    return await generate_interviewer_closing(req)
