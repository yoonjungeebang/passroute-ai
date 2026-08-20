from sqlalchemy import BigInteger, Column, Float, Integer
from app.core.database import Base


class VoiceAnalysis(Base):
    __tablename__ = "voice_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, nullable=False, index=True)
    question_id = Column(BigInteger, nullable=False)
    avg_wpm = Column(Float)
    avg_silence_duration = Column(Float)
    filler_count = Column(Integer)
