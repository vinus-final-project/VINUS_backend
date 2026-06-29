from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base


class OptionGroups(Base):
    __tablename__ = "optionGroups"

    # 변수 선언
    og_id = Column(Integer, primary_key=True)
    m_id = Column(Integer, ForeignKey("menus.m_id"), nullable=False)  # menus 테이블 - 다른 분 담당
    og_name = Column(String(100), nullable=False)
    og_required = Column(Boolean, nullable=False, default=False)
    og_min = Column(Integer, nullable=False, default=0)
    og_max = Column(Integer, nullable=False, default=999)


    ## (m_id, og_name) 복합 유니크 제약조건 추가
    __table_args__ = (
        UniqueConstraint("m_id", "og_name", name="uq_optionGroups_m_id_og_name"),
    )

    #관계 설정

    menu = relationship("ModelsMenus", back_populates="option_groups")
    options = relationship("ModelsOptions", back_populates="option_group")