from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# ── 공통 ──────────────────────────────────────────────────────────────────────

class EvaluationSummary(BaseModel):
    strengths: str
    improvements: str


# ── 질문 단위 평가 (/evaluate/question) ────────────────────────────────────────

class QuestionEvaluationRequest(BaseModel):
    job_title: str
    company_name: str
    jd_keywords: list[str]
    question_type: Literal["technical", "personality"]
    question: str
    answer: str


class ScoreItem(BaseModel):
    score: int = Field(ge=1, le=5)
    feedback: str


class ScoreItemWithWeight(BaseModel):
    score: int = Field(ge=1, le=5)
    weight: float
    feedback: str


class LLMScores(BaseModel):
    relevance: ScoreItem
    logic: ScoreItem
    specificity: ScoreItem
    conciseness: ScoreItem
    clarity: ScoreItem
    job_relevance: ScoreItem
    accuracy: ScoreItem | None = None
    depth: ScoreItem | None = None
    authenticity: ScoreItem | None = None
    growth: ScoreItem | None = None


class LLMScoresWithWeight(BaseModel):
    relevance: ScoreItemWithWeight
    logic: ScoreItemWithWeight
    specificity: ScoreItemWithWeight
    conciseness: ScoreItemWithWeight
    clarity: ScoreItemWithWeight
    job_relevance: ScoreItemWithWeight
    accuracy: ScoreItemWithWeight | None = None
    depth: ScoreItemWithWeight | None = None
    authenticity: ScoreItemWithWeight | None = None
    growth: ScoreItemWithWeight | None = None


class QuestionEvaluationResponse(BaseModel):
    llm_scores: LLMScoresWithWeight
    summary: EvaluationSummary


# ── STAR 평가 (/evaluate/star) ────────────────────────────────────────────────

class StarEvaluationRequest(BaseModel):
    question: str
    answer: str


class StarBreakdownItem(BaseModel):
    present: bool
    feedback: str


class StarBreakdown(BaseModel):
    situation: StarBreakdownItem
    task: StarBreakdownItem
    action: StarBreakdownItem
    result: StarBreakdownItem


class StarEvaluationDetail(BaseModel):
    applicable: bool
    reason: str
    star_breakdown: StarBreakdown | None = None
    star_score: int | None = Field(default=None, ge=0, le=4)

    @model_validator(mode='after')
    def check_non_applicable_fields(self) -> StarEvaluationDetail:
        if not self.applicable:
            if self.star_breakdown is not None or self.star_score is not None:
                raise ValueError("applicable=false일 때 star_breakdown, star_score는 null이어야 합니다.")
        return self


class StarEvaluationResponse(BaseModel):
    star_evaluation: StarEvaluationDetail


# ── 세션 요약 (/evaluate/session-summary) ─────────────────────────────────────

class QuestionSummaryItem(BaseModel):
    question_index: int
    question_type: Literal["technical", "personality"]
    question: str
    percentage: float = Field(ge=0, le=100)
    summary: EvaluationSummary


class ItemAvg(BaseModel):
    avg: float = Field(ge=1, le=5)
    evaluated_count: int = Field(ge=0)


class ItemAverages(BaseModel):
    relevance: ItemAvg
    logic: ItemAvg
    specificity: ItemAvg
    conciseness: ItemAvg
    clarity: ItemAvg
    job_relevance: ItemAvg
    accuracy: ItemAvg | None = None
    depth: ItemAvg | None = None
    authenticity: ItemAvg | None = None
    growth: ItemAvg | None = None


class SessionScore(BaseModel):
    raw: float
    percentage: float = Field(ge=0, le=100)
    consistency_score: float = Field(ge=0, le=1)


class BestWorstQ(BaseModel):
    question_index: int
    question: str
    percentage: float = Field(ge=0, le=100)


class SessionSummaryRequest(BaseModel):
    job_title: str
    company_name: str
    per_question_summaries: list[QuestionSummaryItem]
    item_averages: ItemAverages
    session_score: SessionScore
    best_q: BestWorstQ
    worst_q: BestWorstQ


class QuestionHighlight(BaseModel):
    question_index: int
    type: Literal["best", "worst"]
    comment: str


class SessionSummaryOutput(BaseModel):
    overall: str
    strengths: str
    improvements: str
    question_highlights: list[QuestionHighlight]


class SessionSummaryResponse(BaseModel):
    session_summary: SessionSummaryOutput


# ── 리포트 생성 (/report/generate) ───────────────────────────────────────────

class StarEvalForReport(BaseModel):
    applicable: bool
    star_score: int | None = Field(default=None, ge=0, le=4)


class QuestionEvalForReport(BaseModel):
    question_index: int
    question_type: Literal["technical", "personality"]
    question: str
    percentage: float = Field(ge=0, le=100)
    summary: EvaluationSummary
    star_evaluation: StarEvalForReport
    voice_feedback: str | None = None


class InterviewReadiness(BaseModel):
    decision: Literal["READY", "NEEDS_REVIEW", "NEEDS_IMPROVEMENT"]
    reason: str


class SessionResultForReport(BaseModel):
    percentage: float = Field(ge=0, le=100)
    consistency_score: float = Field(ge=0, le=1)
    item_averages: ItemAverages
    key_weakness: list[str]
    interview_readiness: InterviewReadiness


class VoiceHighlightMoment(BaseModel):
    question_index: int
    timestamp_range: str
    reason: str


class VoiceHighlight(BaseModel):
    best_moment: VoiceHighlightMoment | None = None
    improvement_moment: VoiceHighlightMoment | None = None


class ReportGenerationRequest(BaseModel):
    job_title: str
    company_name: str
    question_evaluations: list[QuestionEvalForReport]
    session_result: SessionResultForReport
    voice_highlight: VoiceHighlight | None = None


class WeaknessItem(BaseModel):
    item: str
    comment: str


class QuestionFeedback(BaseModel):
    question_index: int
    question: str
    question_type: Literal["technical", "personality"]
    percentage: float = Field(ge=0, le=100)
    feedback: str
    star_comment: str | None = None
    voice_comment: str | None = None


class ReportGenerationResponse(BaseModel):
    overall: str
    strengths: str
    weaknesses: list[WeaknessItem]
    improvements: str
    question_feedback: list[QuestionFeedback]
    recommended_questions: list[str]
    final_advice: str
    readiness_comment: str