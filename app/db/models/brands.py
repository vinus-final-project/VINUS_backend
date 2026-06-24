from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class ModelsBrands(Base):
    __tablename__ = "brands"

    b_id = Column(Integer, primary_key=True)
    b_name = Column(String(255), nullable=False)

    stores = relationship("ModelsStores", back_populates="brand")