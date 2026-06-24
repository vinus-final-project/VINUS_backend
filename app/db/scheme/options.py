from pydantic import BaseModel

# Base
class SchemeOptionsBase(BaseModel):
    og_id: int
    op_name: str
    op_price: int

# C - Create
class SchemeOptionsCreate(SchemeOptionsBase):
    pass

# R - Read
class SchemeOptionsResponse(SchemeOptionsBase):
    op_id: int

    class Config:
        from_attributes = True

# U - Update
class SchemeOptionsUpdate(BaseModel):
    op_name: str | None = None
    op_price: int | None = None

# D - Delete
# 삭제는 op_id로 처리 (Response 재사용)