from pydantic import BaseModel, ConfigDict
from typing import Optional

class MenuIngredientsBase(BaseModel):
    m_id: int
    i_id: int

class MenuIngredientsCreate(MenuIngredientsBase):
    pass

class MenuIngredientsResponse(MenuIngredientsBase):
    m_i_id: int

    model_config = ConfigDict(from_attributes=True)
