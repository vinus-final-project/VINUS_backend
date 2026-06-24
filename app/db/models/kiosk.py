from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class ModelsKiosk(Base):
    __tablename__ = "kiosk"

    #변수 설정
    k_id = Column(String(255), primary_key=True)
    s_id = Column(Integer, ForeignKey("stores.s_id"), nullable=False)

    

    #관계 설정
    store = relationship("ModelsStores", back_populates="kiosks")
    orders = relationship("ModelsOrders", back_populates="kiosk")