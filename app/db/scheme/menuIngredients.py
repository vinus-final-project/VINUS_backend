from pydantic import BaseModel
from typing import Optional

class SchemeMenuIngredientsBase(BaseModel):
    m_id: int
    i_id: int

class SchemeMenuIngredientsCreate(SchemeMenuIngredientsBase):
    pass

class SchemeMenuIngredientsResponse(SchemeMenuIngredientsBase):
    m_i_id: int

    class Config:
        from_attributes = True