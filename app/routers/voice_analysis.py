from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.voice_analysis import VoiceAnalysis

router = APIRouter(tags=["평가"])


@router.post("/interview/{session_id}/end",
              summary="면접 종료 후 음성 분석 집계")
async def end_interview(session_id: str, db: AsyncSession = Depends(get_db)):
    """세션 전체의 평균 WPM, 평균 침묵 시간, 총 필러워드 수를 집계하여 반환한다."""
    result = await db.execute(
        select(
            func.avg(VoiceAnalysis.avg_wpm).label("avg_wpm"),
            func.avg(VoiceAnalysis.avg_silence_duration).label("avg_silence_duration"),
            func.sum(VoiceAnalysis.filler_count).label("total_filler_count"),
        ).where(VoiceAnalysis.session_id == session_id)
    )
    row = result.fetchone()
    if row is None or row.avg_wpm is None:
        return {
            "session_id": session_id,
            "avg_wpm": None,
            "avg_silence_duration": None,
            "total_filler_count": None,
        }
    return {
        "session_id": session_id,
        "avg_wpm": round(row.avg_wpm, 2),
        "avg_silence_duration": round(row.avg_silence_duration or 0, 4),
        "total_filler_count": row.total_filler_count or 0,
    }
