from sqlalchemy import Column, Integer, String
from app.db.database import Base

class Categories(Base):
    __tablename__ = "categories"

    # 변수 선언
    c_id = Column(Integer, primary_key=True)
    c_name = Column(String(100), nullable=False)