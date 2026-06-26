from pydantic import BaseModel
from typing import Optional

class SchemeIngredientsBase(BaseModel):
    i_name: str

class SchemeIngredientsCreate(SchemeIngredientsBase):
    pass

class SchemeIngredientsResponse(SchemeIngredientsBase):
    i_id: int

    class Config:
        from_attributes = True