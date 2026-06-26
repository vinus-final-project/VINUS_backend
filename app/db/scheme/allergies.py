from pydantic import BaseModel, ConfigDict
from typing import Optional

class SchemeAllergyBase(BaseModel):
    a_name: str

class SchemeAllergyCreate(SchemeAllergyBase):
    pass

class SchemeAllergyResponse(SchemeAllergyBase):
    a_id: int

    model_config = ConfigDict(from_attributes=True)
