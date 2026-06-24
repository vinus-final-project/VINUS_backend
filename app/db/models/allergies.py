from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from database import Base
from sqlalchemy.orm import relationship


class ModelsAllergy(Base):
    __tablename__ = "allergies"

    # 변수 설정
    a_id = Column(Integer, primary_key=True, autoincrement=True)
    a_name = Column(String, nullable=False)

    #관계 설정

    menu_allergies = relationship("ModelsMenuAllergies", back_populates="allergy")