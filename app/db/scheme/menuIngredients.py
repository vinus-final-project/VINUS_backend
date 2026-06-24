from pydantic import BaseModel
from typing import Optional

class SchemeMenuIngredientBase(BaseModel):
    m_id: int
    i_id: int

class SchemeMenuIngredientCreate(SchemeMenuIngredientBase):
    pass

class SchemeMenuIngredientResponse(SchemeMenuIngredientBase):
    m_i_id: int

    class Config:
        from_attributes = True