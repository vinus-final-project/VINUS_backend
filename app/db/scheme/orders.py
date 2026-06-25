from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class OdState(str, Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    CANCELLED = "CANCELLED"
    REFUNDED = "REFUNDED"

# Base
class SchemeOrdersBase(BaseModel):
    se_id: str
    od_price: int
    od_no: int
    od_state: OdState = OdState.PENDING

# C - Create
class SchemeOrdersCreate(SchemeOrdersBase):
    pass

# R - Read
class SchemeOrdersResponse(SchemeOrdersBase):
    od_id: int
    od_time: datetime

    class Config:
        from_attributes = True

# U - Update
class SchemeOrdersUpdate(BaseModel):
    od_state: OdState | None = None
    od_price: int | None = None

# D - Delete
# 삭제는 od_id로 처리 (Response 재사용)