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

class ModelsOrders(Base):
    __tablename__ = "orders"

    # 변수 선언
    od_id = Column(Integer, primary_key=True)
    se_id = Column(String(36), ForeignKey("sessions.se_id"), nullable=False)   # sessions 테이블 - 다른 분 담당
    k_id = Column(String(255), ForeignKey("kiosk.k_id"), nullable=False)      # kiosk 테이블 - 다른 분 담당
    s_id = Column(Integer, ForeignKey("stores.s_id"), nullable=False)          # stores 테이블 - 다른 분 담당
    od_time = Column(DateTime, default=func.now())
    od_price = Column(Integer, nullable=False)
    od_state = Column(Enum(OdState), default=OdState.PENDING)
    od_no = Column(Integer, nullable=False)

    #관계 설정

    kiosk = relationship("ModelsKiosk", back_populates="orders")
    store = relationship("ModelsStores", back_populates="orders")
    order_menus = relationship("ModelsOrderMenus", back_populates="order")