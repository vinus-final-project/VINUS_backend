from pydantic import BaseModel, ConfigDict
from typing import Optional

class SchemeIngredientsBase(BaseModel):
    i_name: str

class SchemeIngredientsCreate(SchemeIngredientsBase):
    pass

class SchemeIngredientsResponse(SchemeIngredientsBase):
    i_id: int

    model_config = ConfigDict(from_attributes=True)
