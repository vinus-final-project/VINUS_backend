from pydantic import BaseModel
from typing import Optional

class SchemeAllergiesBase(BaseModel):
    a_name: str

class SchemeAllergiesCreate(SchemeAllergiesBase):
    pass

class SchemeAllergiesResponse(SchemeAllergiesBase):
    a_id: int

    class Config:
        from_attributes = True