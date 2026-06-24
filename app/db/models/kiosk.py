from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base


class ModelsKiosk(Base):
    __tablename__ = "kiosk"

    k_id = Column(String(255), primary_key=True)
    s_id = Column(Integer, ForeignKey("stores.s_id"), nullable=False)

    store = relationship("ModelsStores", back_populates="kiosks")