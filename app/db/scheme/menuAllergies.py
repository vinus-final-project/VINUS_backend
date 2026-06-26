from pydantic import BaseModel, ConfigDict
from typing import Optional

class SchemeMenuAllergyBase(BaseModel):
    m_id: int
    a_id: int

class SchemeMenuAllergyCreate(SchemeMenuAllergyBase):
    pass

class SchemeMenuAllergyResponse(SchemeMenuAllergyBase):
    m_a_id: int

    model_config = ConfigDict(from_attributes=True)
