from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from database import Base

class ModelsOptions(Base):
    __tablename__ = "options"

    # 변수 선언
    op_id = Column(Integer, primary_key=True)
    og_id = Column(Integer, ForeignKey("optionGroups.og_id"), nullable=False)
    op_name = Column(String(100), nullable=False)
    op_price = Column(Integer, nullable=False)

    

    __table_args__ = (
        UniqueConstraint("og_id", "op_name", name="uq_options_og_id_op_name"),
    )