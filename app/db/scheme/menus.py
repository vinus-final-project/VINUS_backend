from pydantic import BaseModel, ConfigDict
from typing import List, Optional

# --- [메뉴 조회]용 스키마 ---
class SchemeMenuSimple(BaseModel):
    m_id: int
    c_id: int
    m_name: str
    m_price: int

    model_config = ConfigDict(from_attributes=True)


class RoutersMenuListResponse(BaseModel):
    menus: List[SchemeMenuSimple]


# --- [메뉴 상세 조회]용 중첩 스키마 ---
class SchemeAllergy(BaseModel):
    a_id: int
    a_name: str

class SchemeIngredient(BaseModel):
    i_id: int
    i_name: str

class SchemeOption(BaseModel):
    op_id: int
    op_name: str
    op_price: int
    og_id: int

class SchemeOptionGroup(BaseModel):
    og_id: int
    og_name: str
    og_required: bool
    og_min: int
    og_max: int
    options: List[SchemeOption]

class RoutersMenuDetailResponse(BaseModel):
    m_id: int
    m_name: str
    m_price: int
    m_description: Optional[str] = None
    allergies: List[SchemeAllergy]
    ingredients: List[SchemeIngredient]
    option_groups: List[SchemeOptionGroup]