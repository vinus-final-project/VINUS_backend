from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from database import Base


class ModelsAllergy(Base):
    __tablename__ = "allergies"

    a_id = Column(Integer, primary_key=True, autoincrement=True)
    a_name = Column(String, nullable=False)