from pydantic import BaseModel, ConfigDict
from typing import Optional

class SchemeIngredientBase(BaseModel):
    i_name: str

class SchemeIngredientCreate(SchemeIngredientBase):
    pass

class SchemeIngredientResponse(SchemeIngredientBase):
    i_id: int

    model_config = ConfigDict(from_attributes=True)
