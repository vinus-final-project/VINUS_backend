# app/db/models/sessions.py
import enum

from sqlalchemy import Column, String, DateTime, Enum
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class SessionStatus(enum.Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"


class SeCarry(enum.Enum):
    STORE = "STORE"
    TAKEOUT = "TAKEOUT"


class ModelsSessions(Base):
    __tablename__ = "sessions"

    # 변수 선언
    se_id = Column(String(36), primary_key=True)  # UUID 문자열
    se_status = Column(Enum(SessionStatus), nullable=False, default=SessionStatus.ACTIVE)
    se_carry = Column(Enum(SeCarry), nullable=True)
    se_started_at = Column(DateTime, nullable=False, default=func.now())
    se_ended_at = Column(DateTime, nullable=True)

    # 관계 설정
    orders = relationship("ModelsOrders", back_populates="session")
    session_logs = relationship("ModelsSessionLogs", back_populates="session")