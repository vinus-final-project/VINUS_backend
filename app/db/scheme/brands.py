from pydantic import BaseModel, ConfigDict


# Base
class SchemeBrandsBase(BaseModel):
    b_name: str


# C - 생성
class SchemeBrandsCreate(SchemeBrandsBase):
    pass


# R - 조회
class SchemeBrandsRead(SchemeBrandsBase):
    b_id: int

    model_config = ConfigDict(from_attributes=True)


# U - 수정
class SchemeBrandsUpdate(BaseModel):
    b_name: str | None = None