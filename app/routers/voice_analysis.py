from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select
from app.core.database import get_db
from app.models.voice_analysis import VoiceAnalysis

router = APIRouter()


@router.post("/interview/{session_id}/end")
async def end_interview(session_id: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(
            func.avg(VoiceAnalysis.avg_wpm).label("avg_wpm"),
            func.avg(VoiceAnalysis.avg_silence_duration).label("avg_silence_duration"),
            func.sum(VoiceAnalysis.filler_count).label("total_filler_count"),
        ).where(VoiceAnalysis.session_id == session_id)
    )
    row = result.fetchone()
    return {
        "session_id": session_id,
        "avg_wpm": round(row.avg_wpm or 0, 2),
        "avg_silence_duration": round(row.avg_silence_duration or 0, 4),
        "total_filler_count": row.total_filler_count or 0,
    }
