from fastapi import APIRouter
from app.schemas.evaluation import (
    QuestionEvaluationRequest,
    QuestionEvaluationResponse,
    StarEvaluationRequest,
    StarEvaluationResponse,
    SessionSummaryRequest,
    SessionSummaryResponse,
    ReportGenerationRequest,
    ReportGenerationResponse,
)
from app.services.llm_service import (
    evaluate_question,
    evaluate_star,
    generate_session_summary,
    generate_report,
)

router = APIRouter()


@router.post("/evaluate/question", response_model=QuestionEvaluationResponse)
async def evaluate_question_endpoint(req: QuestionEvaluationRequest) -> QuestionEvaluationResponse:
    return await evaluate_question(req)


@router.post("/evaluate/star", response_model=StarEvaluationResponse)
async def evaluate_star_endpoint(req: StarEvaluationRequest) -> StarEvaluationResponse:
    return await evaluate_star(req)


@router.post("/evaluate/session-summary", response_model=SessionSummaryResponse)
async def session_summary_endpoint(req: SessionSummaryRequest) -> SessionSummaryResponse:
    return await generate_session_summary(req)


@router.post("/report/generate", response_model=ReportGenerationResponse)
async def report_generate_endpoint(req: ReportGenerationRequest) -> ReportGenerationResponse:
    return await generate_report(req)