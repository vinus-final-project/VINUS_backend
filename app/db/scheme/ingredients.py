from pydantic import BaseModel
from typing import Optional

class SchemeIngredientBase(BaseModel):
    i_name: str

class SchemeIngredientCreate(SchemeIngredientBase):
    pass

class SchemeIngredientResponse(SchemeIngredientBase):
    i_id: int

    class Config:
        from_attributes = True