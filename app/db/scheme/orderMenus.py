from pydantic import BaseModel, ConfigDict

# Base
class SchemeOrderMenusBase(BaseModel):
    od_id: int
    m_id: int
    o_m_qty: int = 1

# C - Create
class SchemeOrderMenusCreate(SchemeOrderMenusBase):
    pass

# R - Read
class SchemeOrderMenusResponse(SchemeOrderMenusBase):
    o_m_id: int

    model_config = ConfigDict(from_attributes=True)


# U - Update
class SchemeOrderMenusUpdate(BaseModel):
    o_m_qty: int | None = None

# D - Delete
# 삭제는 o_m_id로 처리 (Response 재사용)