from pydantic import BaseModel, ConfigDict
from typing import Optional

class MenuAllergiesBase(BaseModel):
    m_id: int
    a_id: int

class MenuAllergiesCreate(MenuAllergiesBase):
    pass

class MenuAllergiesResponse(MenuAllergiesBase):
    m_a_id: int

    model_config = ConfigDict(from_attributes=True)
