from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class ModelsAdmin(Base):
    __tablename__ = "admin"

    ad_id = Column(Integer, primary_key=True)
    ad_email = Column(String(255), nullable=False, unique=True)
    ad_pw = Column(String(255), nullable=False)
    ad_name = Column(String(255), nullable=False)

    stores = relationship("ModelsStores", back_populates="admin")