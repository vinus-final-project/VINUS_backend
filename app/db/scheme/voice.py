from pydantic import BaseModel, ConfigDict


# Base
class VoiceBase(BaseModel):
    v_value: str
    v_code: str


# C - 생성
class VoiceCreate(VoiceBase):
    pass


# R - 조회
class VoiceRead(VoiceBase):
    v_id: int

    model_config = ConfigDict(from_attributes=True)


# U - 수정
class VoiceUpdate(BaseModel):
    v_value: str | None = None
    v_code: str | None = None