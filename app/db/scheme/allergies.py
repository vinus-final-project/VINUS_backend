from pydantic import BaseModel, ConfigDict
from typing import Optional

class AllergiesBase(BaseModel):
    a_name: str

class AllergiesCreate(AllergiesBase):
    pass

class AllergiesResponse(AllergiesBase):
    a_id: int

    model_config = ConfigDict(from_attributes=True)
