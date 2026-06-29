from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.database import Base
from sqlalchemy.orm import relationship

class MenuIngredients(Base):
    __tablename__ = "menuIngredients"

    #변수 설정
    m_i_id = Column(Integer, primary_key=True, autoincrement=True)
    m_id = Column(Integer, ForeignKey("menus.m_id"), nullable=False)
    i_id = Column(Integer, ForeignKey("ingredients.i_id"), nullable=False)

    # (m_id, i_id) 복합 유니크 제약조건 추가
    __table_args__ = (
        UniqueConstraint('m_id', 'i_id', name='uq_menu_ingredient'),
    )

    #관계설정
    menu = relationship("ModelsMenus", back_populates="menu_ingredients")
    ingredient = relationship("ModelsIngredients", back_populates="menu_ingredients")