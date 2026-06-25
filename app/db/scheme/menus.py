from pydantic import BaseModel, ConfigDict
from typing import Optional, List

# --- 하위 릴레이션 조회를 위한 개별 Response 컴포넌트 스키마 ---
class SchemeMenuAllergyRead(BaseModel):
    a_id: int
    a_name: str
    model_config = ConfigDict(from_attributes=True)

class SchemeMenuIngredientRead(BaseModel):
    i_id: int
    i_name: str
    model_config = ConfigDict(from_attributes=True)

class SchemeMenuOptionRead(BaseModel):
    op_id: int
    op_name: str
    op_price: int
    og_id: int
    model_config = ConfigDict(from_attributes=True)

class SchemeMenuOptionGroupRead(BaseModel):
    og_id: int
    og_name: str
    og_required: bool
    og_min: int
    og_max: int
    options: List[SchemeMenuOptionRead]  # 하위 옵션 배열 중첩
    model_config = ConfigDict(from_attributes=True)


# --- 메인 Menus 스키마 ---
class SchemeMenusBase(BaseModel):
    c_id: int
    m_name: str
    m_price: int
    m_description: Optional[str] = None

class SchemeMenusCreate(SchemeMenusBase):
    pass

# 1. 메뉴 기본 조회용 (/menus Response)
class SchemeMenusRead(SchemeMenusBase):
    m_id: int


# 1. 메뉴 상세 조회용 (/menus/{m_id} Response)
class SchemeMenuDetailRead(BaseModel):
    m_id: int
    m_name: str
    m_price: int
    m_description: Optional[str] = None
    
    # 명세서의 중첩 Array 구조 그대로 매핑
    allergies: List[SchemeMenuAllergyRead]
    ingredients: List[SchemeMenuIngredientRead]
    option_groups: List[SchemeMenuOptionGroupRead]

    model_config = ConfigDict(from_attributes=True)