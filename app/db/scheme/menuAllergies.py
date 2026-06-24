from pydantic import BaseModel
from typing import Optional

class SchemeMenuAllergyBase(BaseModel):
    m_id: int
    a_id: int

class SchemeMenuAllergyCreate(SchemeMenuAllergyBase):
    pass

class SchemeMenuAllergyResponse(SchemeMenuAllergyBase):
    m_a_id: int

    class Config:
        from_attributes = True