from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class ModelsStores(Base):
    __tablename__ = "stores"

    
    #변수 설정

    s_id = Column(Integer, primary_key=True)
    s_name = Column(String(255), nullable=False)
    b_id = Column(Integer, ForeignKey("brands.b_id"), nullable=False)
    ad_id = Column(Integer, ForeignKey("admin.ad_id"), nullable=False)

    

    #관계 설정

    brand = relationship("ModelsBrands", back_populates="stores")
    admin = relationship("ModelsAdmin", back_populates="stores")
    kiosks = relationship("ModelsKiosk", back_populates="store")
    sold_outs = relationship("ModelsSoldouts", back_populates="store")
    orders = relationship("ModelsOrders", back_populates="store")