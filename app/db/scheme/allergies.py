from pydantic import BaseModel, ConfigDict
from typing import Optional

class SchemeAllergiesBase(BaseModel):
    a_name: str

class SchemeAllergiesCreate(SchemeAllergiesBase):
    pass

class SchemeAllergiesResponse(SchemeAllergiesBase):
    a_id: int

    model_config = ConfigDict(from_attributes=True)
