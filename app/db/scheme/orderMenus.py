from pydantic import BaseModel, ConfigDict

# Base
class OrderMenusBase(BaseModel):
    od_id: int
    m_id: int
    o_m_qty: int = 1

# C - Create
class OrderMenusCreate(OrderMenusBase):
    pass

# R - Read
class OrderMenusResponse(OrderMenusBase):
    o_m_id: int

    model_config = ConfigDict(from_attributes=True)


# U - Update
class OrderMenusUpdate(BaseModel):
    o_m_qty: int | None = None

# D - Delete
# 삭제는 o_m_id로 처리 (Response 재사용)