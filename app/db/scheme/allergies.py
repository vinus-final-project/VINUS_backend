from pydantic import BaseModel, ConfigDict
from typing import Optional

class SchemeAllergiesBase(BaseModel):
    a_name: str

class SchemeAllergyCreate(SchemeAllergiesBase):
    pass

class SchemeAllergyResponse(SchemeAllergiesBase):
    a_id: int

    model_config = ConfigDict(from_attributes=True)
