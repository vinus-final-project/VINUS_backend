from pydantic import BaseModel

# Base
class SchemeSoldoutsBase(BaseModel):
    s_id: int
    m_id: int
    so_sold: bool

# C - Create
class SchemeSoldoutsCreate(SchemeSoldoutsBase):
    pass

# R - Read
class SchemeSoldoutsResponse(SchemeSoldoutsBase):
    so_id: int

    class Config:
        from_attributes = True

# U - Update
class SchemeSoldoutsUpdate(BaseModel):
    so_sold: bool | None = None

# D - Delete
# 삭제는 so_id로 처리 (Response 재사용)