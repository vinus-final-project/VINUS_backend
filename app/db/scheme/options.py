from pydantic import BaseModel, ConfigDict

# Base
class OptionsBase(BaseModel):
    og_id: int
    op_name: str
    op_price: int

# C - Create
class OptionsCreate(OptionsBase):
    pass

# R - Read
class OptionsResponse(OptionsBase):
    op_id: int

    model_config = ConfigDict(from_attributes=True)


# U - Update
class OptionsUpdate(BaseModel):
    op_name: str | None = None
    op_price: int | None = None

# D - Delete
# 삭제는 op_id로 처리 (Response 재사용)