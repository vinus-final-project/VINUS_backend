from sqlalchemy import Column, Integer, ForeignKey
from app.db.database import Base
from sqlalchemy.orm import relationship

class OrderMenus(Base):
    __tablename__ = "orderMenus"

    # 변수 선언
    o_m_id = Column(Integer, primary_key=True)
    od_id = Column(Integer, ForeignKey("orders.od_id"), nullable=False)
    m_id = Column(Integer, ForeignKey("menus.m_id"), nullable=False)   # menus 테이블 - 다른 분 담당
    o_m_qty = Column(Integer, default=1)

    #관계 설정
    order = relationship("Orders", back_populates="order_menus")
    menu = relationship("Menus", back_populates="order_menus")
    order_menu_options = relationship("OrderMenuOptions", back_populates="order_menu")