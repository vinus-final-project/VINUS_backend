from pydantic import BaseModel, ConfigDict


# Base
class SchemeStoresBase(BaseModel):
    s_name: str
    b_id: int
    ad_id: int


# C - 생성
class SchemeStoresCreate(SchemeStoresBase):
    pass


# R - 조회
class SchemeStoresRead(SchemeStoresBase):
    s_id: int

    model_config = ConfigDict(from_attributes=True)


# U - 수정
class SchemeStoresUpdate(BaseModel):
    s_name: str | None = None
    b_id: int | None = None
    ad_id: int | None = None