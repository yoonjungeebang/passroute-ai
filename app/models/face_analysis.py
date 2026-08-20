from sqlalchemy import BigInteger, Column, Float, Integer
from app.core.database import Base


class FaceAnalysis(Base):
    __tablename__ = "face_analysis"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    session_id = Column(BigInteger, nullable=False, index=True)
    question_id = Column(BigInteger, nullable=False)
    gaze_off_count = Column(Integer)
    avg_gaze_ratio = Column(Float)
    avg_blink_per_min = Column(Float)
