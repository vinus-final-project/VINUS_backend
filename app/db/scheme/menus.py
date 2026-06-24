from pydantic import BaseModel
from typing import Optional

class SchemeMenusBase(BaseModel):
    b_id: int
    c_id: int
    m_name: str
    m_price: int
    m_description: Optional[str] = None

class SchemeMenusCreate(SchemeMenusBase):
    pass

class SchemeMenusResponse(SchemeMenusBase):
    m_id: int

    class Config:
        from_attributes = True