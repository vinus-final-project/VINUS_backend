from pydantic import BaseModel

# Base
class SchemeCategoriesBase(BaseModel):
    c_name: str

# C - Create
class SchemeCategoriesCreate(SchemeCategoriesBase):
    pass

# R - Read
class SchemeCategoriesResponse(SchemeCategoriesBase):
    c_id: int

    class Config:
        from_attributes = True

# U - Update
class SchemeCategoriesUpdate(BaseModel):
    c_name: str | None = None

# D - Delete
# 삭제는 c_id로 처리 (Response 재사용)