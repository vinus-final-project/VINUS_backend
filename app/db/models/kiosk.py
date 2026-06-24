from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base 


class Kiosk(Base):
    __tablename__ = "kiosk"

    k_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    s_id: Mapped[int] = mapped_column(Integer, ForeignKey("stores.s_id"), nullable=False)