# app/db/models/orders.py
from sqlalchemy import Column, Integer, String, DateTime, Enum, ForeignKey
from sqlalchemy.sql import func
import enum
from app.db.database import Base
from sqlalchemy.orm import relationship


class OdState(enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"


class Orders(Base):
    __tablename__ = "orders"

    # 변수 선언
    od_id = Column(Integer, primary_key=True)
    se_id = Column(String(36), ForeignKey("sessions.se_id"), nullable=False)
    od_time = Column(DateTime, default=func.now())
    od_price = Column(Integer, nullable=False)
    od_state = Column(Enum(OdState), default=OdState.PENDING)
    od_no = Column(Integer, nullable=False)
    pa_key = Column(String(200), nullable=True)

    # 관계 설정
    session = relationship("Sessions", back_populates="orders")
    order_menus = relationship("OrderMenus", back_populates="order")