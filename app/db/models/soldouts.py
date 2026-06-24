from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint
from database import Base

class ModelsSoldouts(Base):
    __tablename__ = "soldouts"

    # 변수 선언
    so_id = Column(Integer, primary_key=True)
    s_id = Column(Integer, ForeignKey("stores.s_id"), nullable=False)  # stores 테이블 - 다른 분 담당
    m_id = Column(Integer, ForeignKey("menus.m_id"), nullable=False)   # menus 테이블 - 다른 분 담당
    so_sold = Column(Boolean, nullable=False)

    __table_args__ = (
        UniqueConstraint("s_id", "m_id", name="uq_soldouts_s_id_m_id"),
    )