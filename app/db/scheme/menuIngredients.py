from pydantic import BaseModel, ConfigDict
from typing import Optional

class SchemeMenuIngredientBase(BaseModel):
    m_id: int
    i_id: int

class SchemeMenuIngredientCreate(SchemeMenuIngredientBase):
    pass

class SchemeMenuIngredientResponse(SchemeMenuIngredientBase):
    m_i_id: int

    model_config = ConfigDict(from_attributes=True)
