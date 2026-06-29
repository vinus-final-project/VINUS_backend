from pydantic import BaseModel, ConfigDict

# Base
class SchemeOrderMenuOptionsBase(BaseModel):
    o_m_id: int
    op_id: int

# C - Create
class SchemeOrderMenuOptionsCreate(SchemeOrderMenuOptionsBase):
    pass

# R - Read
class SchemeOrderMenuOptionsResponse(SchemeOrderMenuOptionsBase):
    o_m_o_id: int

    model_config = ConfigDict(from_attributes=True)


# U - Update
# 주문-메뉴-옵션은 수정 없음 (삭제 후 재생성)
class SchemeOrderMenuOptionsUpdate(BaseModel):
    pass

# D - Delete
# 삭제는 o_m_o_id로 처리 (Response 재사용)