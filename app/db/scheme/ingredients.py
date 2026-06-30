from pydantic import BaseModel, ConfigDict
from typing import Optional

class IngredientsBase(BaseModel):
    i_name: str

class IngredientsCreate(IngredientsBase):
    pass

class IngredientsResponse(IngredientsBase):
    i_id: int

    model_config = ConfigDict(from_attributes=True)
