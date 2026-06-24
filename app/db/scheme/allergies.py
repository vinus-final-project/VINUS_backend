from pydantic import BaseModel
from typing import Optional

class SchemeAllergyBase(BaseModel):
    a_name: str

class SchemeAllergyCreate(SchemeAllergyBase):
    pass

class SchemeAllergyResponse(SchemeAllergyBase):
    a_id: int

    class Config:
        from_attributes = True