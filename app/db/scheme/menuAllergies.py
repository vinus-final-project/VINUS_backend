from pydantic import BaseModel, ConfigDict
from typing import Optional

class SchemeMenuAllergiesBase(BaseModel):
    m_id: int
    a_id: int

class SchemeMenuAllergiesCreate(SchemeMenuAllergiesBase):
    pass

class SchemeMenuAllergiesResponse(SchemeMenuAllergiesBase):
    m_a_id: int

    model_config = ConfigDict(from_attributes=True)
