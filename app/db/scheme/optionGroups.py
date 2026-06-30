from pydantic import BaseModel, ConfigDict

# Base
class OptionGroupsBase(BaseModel):
    m_id: int
    og_name: str
    og_required: bool = False
    og_min: int = 0
    og_max: int = 999

# C - Create
class OptionGroupsCreate(OptionGroupsBase):
    pass

# R - Read
class OptionGroupsResponse(OptionGroupsBase):
    og_id: int

    model_config = ConfigDict(from_attributes=True)


# U - Update
class OptionGroupsUpdate(BaseModel):
    og_name: str | None = None
    og_required: bool | None = None
    og_min: int | None = None
    og_max: int | None = None

# D - Delete
# 삭제는 og_id로 처리 (Response 재사용)