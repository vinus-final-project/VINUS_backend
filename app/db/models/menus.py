from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.database import Base
from sqlalchemy.orm import relationship

class Menus(Base):
    __tablename__ = "menus"

    #변수 설정
    m_id = Column(Integer, primary_key=True, autoincrement=True)
    c_id = Column(Integer, ForeignKey("categories.c_id"), nullable=False)  # categories 테이블이 있다고 가정
    m_name = Column(String(100), nullable=False)
    m_price = Column(Integer, nullable=False)
    m_description = Column(String(255), nullable=True)

    # 관계 설정
    option_groups = relationship("OptionGroups", back_populates="menu")
    order_menus = relationship("OrderMenus", back_populates="menu")
    menu_allergies = relationship("MenuAllergies", back_populates="menu")
    menu_ingredients = relationship("MenuIngredients", back_populates="menu")