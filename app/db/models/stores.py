from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class ModelsStores(Base):
    __tablename__ = "stores"

    s_id = Column(Integer, primary_key=True)
    s_name = Column(String(255), nullable=False)
    b_id = Column(Integer, ForeignKey("brands.b_id"), nullable=False)
    ad_id = Column(Integer, ForeignKey("admin.ad_id"), nullable=False)

    brand = relationship("ModelsBrands", back_populates="stores")
    admin = relationship("ModelsAdmin", back_populates="stores")
    kiosks = relationship("ModelsKiosk", back_populates="store")