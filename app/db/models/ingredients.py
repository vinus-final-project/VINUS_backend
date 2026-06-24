from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from database import Base
from sqlalchemy.orm import relationship

class ModelsIngredient(Base):
    __tablename__ = "ingredients"

    #변수 설정
    i_id = Column(Integer, primary_key=True, autoincrement=True)
    i_name = Column(String, nullable=False)


    #관계 설정
    menu_ingredients = relationship("ModelsMenuIngredients", back_populates="ingredient")