from fastapi import APIRouter

from app.schemas.debate import (
    DebateReportRequest,
    DebateReportResponse,
    DebateSessionSummaryRequest,
    DebateSessionSummaryResponse,
    DebateTurnEvalRequest,
    DebateTurnEvalResponse,
)
from app.schemas.evaluation import (
    QuestionEvaluationRequest,
    QuestionEvaluationResponse,
    ReportGenerationRequest,
    ReportGenerationResponse,
    SelfIntroSummaryRequest,
    SelfIntroSummaryResponse,
    SessionSummaryRequest,
    SessionSummaryResponse,
    StarEvaluationRequest,
    StarEvaluationResponse,
)
from app.services.debate_llm_service import (
    evaluate_debate_turn,
    generate_debate_report,
    generate_debate_session_summary,
)
from app.services.llm_service import (
    evaluate_question,
    evaluate_star,
    generate_report,
    generate_self_intro_summary,
    generate_session_summary,
)

router = APIRouter()


# ── 1대1 면접 평가 ─────────────────────────────────────────────────────────────

@router.post("/evaluate/question", response_model=QuestionEvaluationResponse, tags=["평가"],
              summary="단일 질문 답변 평가")
async def evaluate_question_endpoint(req: QuestionEvaluationRequest) -> QuestionEvaluationResponse:
    """질문-답변 쌍에 대해 논리성, 구체성 등 항목별 점수와 피드백을 반환한다."""
    return await evaluate_question(req)


@router.post("/evaluate/star", response_model=StarEvaluationResponse, tags=["평가"],
              summary="STAR 기법 답변 평가")
async def evaluate_star_endpoint(req: StarEvaluationRequest) -> StarEvaluationResponse:
    """STAR(Situation-Task-Action-Result) 구조로 작성된 답변을 평가한다."""
    return await evaluate_star(req)


@router.post("/evaluate/session-summary", response_model=SessionSummaryResponse, tags=["평가"],
              summary="1대1 면접 세션 요약")
async def session_summary_endpoint(req: SessionSummaryRequest) -> SessionSummaryResponse:
    """세션 내 모든 질문-답변 평가를 종합하여 세션 단위 요약을 생성한다."""
    return await generate_session_summary(req)


@router.post("/report/generate", response_model=ReportGenerationResponse, tags=["리포트"],
              summary="1대1 면접 리포트 생성")
async def report_generate_endpoint(req: ReportGenerationRequest) -> ReportGenerationResponse:
    """세션 평가 결과를 바탕으로 종합 면접 리포트를 생성한다."""
    return await generate_report(req)


@router.post("/report/self-intro/generate", response_model=SelfIntroSummaryResponse, tags=["리포트"],
              summary="자소서 종합 피드백 생성")
async def self_intro_summary_endpoint(req: SelfIntroSummaryRequest) -> SelfIntroSummaryResponse:
    """자기소개서 문항별 평가를 종합하여 피드백 리포트를 생성한다."""
    return await generate_self_intro_summary(req)


# ── 토론 면접 평가 ─────────────────────────────────────────────────────────────

@router.post("/evaluate/debate-turn", response_model=DebateTurnEvalResponse, tags=["평가"],
              summary="토론 턴 평가")
async def evaluate_debate_turn_endpoint(req: DebateTurnEvalRequest) -> DebateTurnEvalResponse:
    """토론 면접의 개별 턴(입론/반론/최종발언)에 대해 평가한다."""
    return await evaluate_debate_turn(req)


@router.post("/debate/session-summary", response_model=DebateSessionSummaryResponse, tags=["평가"],
              summary="토론 면접 세션 요약")
async def debate_session_summary_endpoint(req: DebateSessionSummaryRequest) -> DebateSessionSummaryResponse:
    """토론 면접 세션의 전체 턴 평가를 종합하여 요약한다."""
    return await generate_debate_session_summary(req)


@router.post("/report/debate/generate", response_model=DebateReportResponse, tags=["리포트"],
              summary="토론 면접 리포트 생성")
async def debate_report_generate_endpoint(req: DebateReportRequest) -> DebateReportResponse:
    """토론 면접 세션의 종합 리포트를 생성한다."""
    return await generate_debate_report(req)
