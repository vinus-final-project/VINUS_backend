from sqlalchemy import Column, Integer, ForeignKey
from database import Base

class ModelsOrderMenuOptions(Base):
    __tablename__ = "orderMenuOptions"

    # 변수 선언
    o_m_o_id = Column(Integer, primary_key=True)
    o_m_id = Column(Integer, ForeignKey("orderMenus.o_m_id"), nullable=False)
    op_id = Column(Integer, ForeignKey("options.op_id"), nullable=False)