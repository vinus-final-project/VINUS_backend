from sqlalchemy import Column, Integer, ForeignKey
from database import Base

class ModelsOrderMenus(Base):
    __tablename__ = "orderMenus"

    # 변수 선언
    o_m_id = Column(Integer, primary_key=True)
    od_id = Column(Integer, ForeignKey("orders.od_id"), nullable=False)
    m_id = Column(Integer, ForeignKey("menus.m_id"), nullable=False)   # menus 테이블 - 다른 분 담당
    o_m_qty = Column(Integer, default=1)