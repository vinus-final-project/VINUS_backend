from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from app.db.database import Base
from sqlalchemy.orm import relationship


class Allergies(Base):
    __tablename__ = "allergies"

    # 변수 설정
    a_id = Column(Integer, primary_key=True, autoincrement=True)
    a_name = Column(String(100), nullable=False)

    #관계 설정

    menu_allergies = relationship("MenuAllergies", back_populates="allergy")