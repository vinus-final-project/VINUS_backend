from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base 


class Store(Base):
    __tablename__ = "stores"

    s_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    s_name: Mapped[str] = mapped_column(String(255), nullable=False)
    b_id: Mapped[int] = mapped_column(Integer, ForeignKey("brands.b_id"), nullable=False)
    ad_id: Mapped[int] = mapped_column(Integer, ForeignKey("admin.ad_id"), nullable=False)
