from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from pydantic import ConfigDict

# --- [메뉴 조회]용 스키마 ---
class Menus(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    m_id: int
    c_id: int
    m_name: str
    m_price: int

class MenusListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True) # 여긴 안해도 되는데 통일성 차원에서 넣음
    menus: List[Menus]
    menus: List[Menus]


# --- [메뉴 상세 조회]용 중첩 스키마 ---
class Allergies(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    a_id: int
    a_name: str

class Ingredients(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    i_id: int
    i_name: str

class Options(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    op_id: int
    op_name: str
    op_price: int
    og_id: int

class OptionGroups(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    og_id: int
    og_name: str
    og_required: bool
    og_min: int
    og_max: int
    options: List[Options]
    options: List[Options]

class MenusDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    m_id: int
    m_name: str
    m_price: int
    m_description: Optional[str] = None
    allergies: List[Allergies]
    ingredients: List[Ingredients]
    option_groups: List[OptionGroups]
    allergies: List[Allergies]
    ingredients: List[Ingredients]
    option_groups: List[OptionGroups]