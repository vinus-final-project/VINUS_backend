from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.menus import ServicesMenus

# 분리한 스키마들을 파일 상단에서 import
from app.db.scheme.menus import RoutersMenusListResponse, RoutersMenusDetailResponse

router = APIRouter(prefix="/menus", tags=["Menus"])

@router.get("", response_model=RoutersMenusListResponse, status_code=status.HTTP_200_OK)
async def read_menus_routers_menus(c_id: int, db: AsyncSession = Depends(get_db)):
    return await ServicesMenus.get_menus_list_by_category_services_menus(c_id, db)

@router.get("/{m_id}", response_model=RoutersMenusDetailResponse, status_code=status.HTTP_200_OK)
async def read_menu_detail_routers_menus(m_id: int, db: AsyncSession = Depends(get_db)):
    return await ServicesMenus.get_single_menu_detail_services_menus(m_id, db)