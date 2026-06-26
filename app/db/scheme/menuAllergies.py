from pydantic import BaseModel
from typing import Optional

class SchemeMenuAllergiesBase(BaseModel):
    m_id: int
    a_id: int

class SchemeMenuAllergiesCreate(SchemeMenuAllergiesBase):
    pass

class SchemeMenuAllergiesResponse(SchemeMenuAllergiesBase):
    m_a_id: int

    class Config:
        from_attributes = True