from pydantic import BaseModel, ConfigDict, EmailStr


# Base
class SchemeAdminBase(BaseModel):
    ad_email: EmailStr
    ad_name: str


# C - 생성
class SchemeAdminCreate(SchemeAdminBase):
    ad_pw: str  # 평문으로 받음 → CRUD에서 해싱 후 저장


# R - 조회
class SchemeAdminRead(SchemeAdminBase):
    ad_id: int

    model_config = ConfigDict(from_attributes=True)


# U - 수정
class SchemeAdminUpdate(BaseModel):
    ad_email: EmailStr | None = None
    ad_pw: str | None = None
    ad_name: str | None = None