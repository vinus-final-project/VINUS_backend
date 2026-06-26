from pydantic import BaseModel
from typing import List, Optional
from pydantic import ConfigDict

# --- [메뉴 조회]용 스키마 ---
class SchemeMenusSimple(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    m_id: int
    c_id: int
    m_name: str
    m_price: int

class RoutersMenusListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True) # 여긴 안해도 되는데 통일성 차원에서 넣음
    menus: List[SchemeMenusSimple]


# --- [메뉴 상세 조회]용 중첩 스키마 ---
class SchemeAllergies(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    a_id: int
    a_name: str

class SchemeIngredients(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    i_id: int
    i_name: str

class SchemeOptions(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    op_id: int
    op_name: str
    op_price: int
    og_id: int

class SchemeOptionGroups(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    og_id: int
    og_name: str
    og_required: bool
    og_min: int
    og_max: int
    options: List[SchemeOptions]

class RoutersMenusDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    m_id: int
    m_name: str
    m_price: int
    m_description: Optional[str] = None
    allergies: List[SchemeAllergies]
    ingredients: List[SchemeIngredients]
    option_groups: List[SchemeOptionGroups]