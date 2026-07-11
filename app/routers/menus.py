from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.services.menus import Menus

# 분리한 스키마들을 파일 상단에서 import
from app.db.scheme.menus import MenusListResponse, MenusDetailResponse

router = APIRouter(prefix="/menus", tags=["Menus"])

# R - 특정 카테고리의 메뉴 목록 조회
@router.get("", response_model=MenusListResponse, status_code=status.HTTP_200_OK)
async def read_menus_routers_menus(c_id: int, db: AsyncSession = Depends(get_db)):
    return await Menus.get_menus_list_by_category_services_menus(c_id, db)

# R - 부트스트랩: 카테고리 + 전체 메뉴 일괄 조회
#   초기 렌더 API 호출 6회(카테고리 1 + 카테고리별 메뉴 5) → 1회 축소용.
#   ⚠ "/{m_id}" 보다 먼저 선언해야 "all" 이 int 파라미터로 해석되지 않음.
@router.get("/all", status_code=status.HTTP_200_OK)
async def read_all_menus_routers_menus(db: AsyncSession = Depends(get_db)):
    return await Menus.get_bootstrap_services_menus(db)

# R - 메뉴 단일 상세 조회
@router.get("/{m_id}", response_model=MenusDetailResponse, status_code=status.HTTP_200_OK)
async def read_menu_detail_routers_menus(m_id: int, db: AsyncSession = Depends(get_db)):
    return await Menus.get_single_menu_detail_services_menus(m_id, db)