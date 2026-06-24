from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.database import Base
from sqlalchemy.orm import relationship

class ModelsMenus(Base):
    __tablename__ = "menus"

    #변수 설정
    m_id = Column(Integer, primary_key=True, autoincrement=True)
    b_id = Column(Integer, ForeignKey("brands.b_id"), nullable=False)  # brands 테이블이 있다고 가정
    c_id = Column(Integer, ForeignKey("categories.c_id"), nullable=False)  # categories 테이블이 있다고 가정
    m_name = Column(String(100), nullable=False)
    m_price = Column(Integer, nullable=False)
    m_description = Column(String(255), nullable=True)

    # 관계 설정
    option_groups = relationship("ModelsOptionGroups", back_populates="menu")
    sold_outs = relationship("ModelsSoldouts", back_populates="menu")
    order_menus = relationship("ModelsOrderMenus", back_populates="menu")
    menu_allergies = relationship("ModelsMenuAllergies", back_populates="menu")
    menu_ingredients = relationship("ModelsMenuIngredients", back_populates="menu")