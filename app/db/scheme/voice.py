from pydantic import BaseModel, ConfigDict


# Base
class SchemeVoiceBase(BaseModel):
    v_value: str
    v_code: str


# C - 생성
class SchemeVoiceCreate(SchemeVoiceBase):
    pass


# R - 조회
class SchemeVoiceRead(SchemeVoiceBase):
    v_id: int

    model_config = ConfigDict(from_attributes=True)


# U - 수정
class SchemeVoiceUpdate(BaseModel):
    v_value: str | None = None
    v_code: str | None = None