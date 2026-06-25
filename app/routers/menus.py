from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
from pydantic import BaseModel
from app.db.database import get_db
from app.services.menus import ServicesMenus

router = APIRouter(prefix="/menus", tags=["Menus"])

# --- 1. [메뉴 조회]용 Pydantic 스키마 정의 ---
class SchemeMenuSimple(BaseModel):
    m_id: int
    c_id: int
    m_name: str
    m_price: int

    class Config:
        from_attributes = True

class RoutersMenuListResponse(BaseModel):
    menus: List[SchemeMenuSimple]


# --- 2. [메뉴 상세 조회]용 중첩 Pydantic 스키마 정의 ---
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


# --- 3. API 엔드포인트 라우터 정의 ---

@router.get("", response_model=RoutersMenuListResponse, status_code=status.HTTP_200_OK)
async def read_menus(c_id: int, db: AsyncSession = Depends(get_db)):
    # 서비스를 호출하여 정제된 카테고리별 메뉴 목록 반환
    return await ServicesMenus.get_menu_list_by_category(c_id, db)


@router.get("/{m_id}", response_model=RoutersMenuDetailResponse, status_code=status.HTTP_200_OK)
async def read_menu_detail(m_id: int, db: AsyncSession = Depends(get_db)):
    # 서비스를 호출하여 구조화된 상세 정보를 반환
    return await ServicesMenus.get_single_menu_detail(m_id, db)