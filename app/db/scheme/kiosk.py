from pydantic import BaseModel, ConfigDict


# Base
class SchemeKioskBase(BaseModel):
    s_id: int


# C - 생성
class SchemeKioskCreate(SchemeKioskBase):
    k_id: str


# R - 조회
class SchemeKioskRead(SchemeKioskBase):
    k_id: str

    model_config = ConfigDict(from_attributes=True)


# U - 수정
class SchemeKioskUpdate(BaseModel):
    s_id: int | None = None