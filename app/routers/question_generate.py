from fastapi import APIRouter, HTTPException

from app.schemas.prompt_builder import QuestionGenerateRequest, QuestionGenerateResponse
from app.services.prompt_builder import generate_questions

router = APIRouter(prefix="/api/questions", tags=["question-generate"])


@router.post("/generate", response_model=QuestionGenerateResponse)
async def generate(body: QuestionGenerateRequest) -> QuestionGenerateResponse:
    """페르소나·슬라이더 설정을 바탕으로 면접 질문을 생성한다."""
    try:
        return await generate_questions(request=body)
    except ValueError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"질문 생성 중 오류: {e}")
