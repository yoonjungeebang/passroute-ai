from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String
from app.core.database import Base


class VoiceAnalysis(Base):
    __tablename__ = "voice_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=False, index=True)
    question_id = Column(String(255), nullable=False)
    avg_wpm = Column(Float)
    silence_ratio = Column(Float)
    filler_count = Column(Integer)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
