from sqlalchemy import Column, Integer, String

from app.db.database import Base


class ModelsVoice(Base):
    __tablename__ = "voice"

    v_id = Column(Integer, primary_key=True)
    v_value = Column(String(255), nullable=False, unique=True)
    v_code = Column(String(100), nullable=False, unique=True)