from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from app.db.database import Base

class ModelsOptions(Base):
    __tablename__ = "options"

    # 변수 선언
    op_id = Column(Integer, primary_key=True)
    og_id = Column(Integer, ForeignKey("optionGroups.og_id"), nullable=False)
    op_name = Column(String(100), nullable=False)
    op_price = Column(Integer, nullable=False)

    

    # # (og_id, op_name) 복합 유니크 제약조건 추가
    __table_args__ = (
        UniqueConstraint("og_id", "op_name", name="uq_options_og_id_op_name"),
    )

    #관계 설정
    option_group = relationship("ModelsOptionGroups", back_populates="options")
    order_menu_options = relationship("ModelsOrderMenuOptions", back_populates="option")