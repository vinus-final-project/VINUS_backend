from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from database import Base

class ModelsIngredient(Base):
    __tablename__ = "ingredients"

    i_id = Column(Integer, primary_key=True, autoincrement=True)
    i_name = Column(String, nullable=False)