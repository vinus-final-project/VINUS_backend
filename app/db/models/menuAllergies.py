from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.database import Base
from sqlalchemy.orm import relationship

class ModelsMenuAllergies(Base):
    __tablename__ = "menuAllergies"

    #변수 설정
    m_a_id = Column(Integer, primary_key=True, autoincrement=True)
    m_id = Column(Integer, ForeignKey("menus.m_id"), nullable=False)
    a_id = Column(Integer, ForeignKey("allergies.a_id"), nullable=False)

    # (m_id, a_id) 복합 유니크 제약조건 추가
    __table_args__ = (
        UniqueConstraint('m_id', 'a_id', name='uq_menu_allergy'),
    )

    #관계 설정

    menu = relationship("ModelsMenus", back_populates="menu_allergies")
    allergy = relationship("ModelsAllergies", back_populates="menu_allergies")