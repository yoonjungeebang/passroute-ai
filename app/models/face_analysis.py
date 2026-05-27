from datetime import datetime, timezone
from sqlalchemy import BigInteger, Column, DateTime, Float, Integer, String
from app.core.database import Base


class FaceAnalysis(Base):
    __tablename__ = "face_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(String(255), nullable=False, index=True)
    question_id = Column(String(255), nullable=False)
    gaze_off_count = Column(Integer)
    avg_gaze_ratio = Column(Float)
    avg_blink_per_min = Column(Float)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
