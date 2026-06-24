from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from app.db.database import Base


class Brand(Base):
    __tablename__ = "brands"

    b_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    b_name: Mapped[str] = mapped_column(String(255), nullable=False)