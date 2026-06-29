from sqlalchemy import Column, Integer, ForeignKey
from app.db.database import Base
from sqlalchemy.orm import relationship

class OrderMenuOptions(Base):
    __tablename__ = "orderMenuOptions"

    # 변수 선언
    o_m_o_id = Column(Integer, primary_key=True)
    o_m_id = Column(Integer, ForeignKey("orderMenus.o_m_id"), nullable=False)
    op_id = Column(Integer, ForeignKey("options.op_id"), nullable=False)

    #관계 설정
    order_menu = relationship("OrderMenus", back_populates="order_menu_options")
    option = relationship("Options", back_populates="order_menu_options")