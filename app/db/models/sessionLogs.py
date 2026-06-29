# app/db/models/sessionLogs.py
import enum

from sqlalchemy import Column, Integer, String, Text, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class SpeakerType(enum.Enum):
    AI = "AI"
    SYSTEM = "SYSTEM"
    USER = "USER"


class SessionLogs(Base):
    __tablename__ = "sessionLogs"

    # 변수 선언
    sl_id = Column(Integer, primary_key=True, autoincrement=True)
    se_id = Column(String(36), ForeignKey("sessions.se_id"), nullable=False)
    sl_speaker = Column(Enum(SpeakerType), nullable=False)
    sl_message = Column(Text, nullable=False)
    sl_intent = Column(String(100), nullable=True)
    sl_created_at = Column(DateTime, nullable=False, default=func.now())

    # 관계 설정
    session = relationship("ModelsSessions", back_populates="session_logs")