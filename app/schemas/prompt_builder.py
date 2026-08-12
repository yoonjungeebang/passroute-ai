from typing import Literal

from pydantic import BaseModel, Field


class QuestionGenerateRequest(BaseModel):
    persona: Literal["HR_MANAGER", "TEAM_LEAD", "EXECUTIVE", "TECH_INTERVIEWER"]
    pressure_level: int = Field(ge=0, le=10)
    difficulty: Literal["EASY", "NORMAL", "HARD"]
    followup_count: int = Field(ge=0, le=5)
    interview_type: Literal["PERSONALITY", "TECHNICAL"]
    interview_format: Literal["ONE_ON_ONE", "DEBATE"]
    cover_letter: str
    resume: str | None = None
    portfolio: str | None = None
    question_count: int = Field(default=5, ge=1, le=20)


class GeneratedQuestion(BaseModel):
    question: str
    followup_questions: list[str] = []
    intent: str | None = None


class QuestionGenerateResponse(BaseModel):
    persona: str
    questions: list[GeneratedQuestion]
