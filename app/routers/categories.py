from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from app.db.database import get_db
from app.db.scheme.categories import CategoriesRead
from app.services.categories import Categories  # 새 서비스 임포트

router = APIRouter(prefix="/categories", tags=["Categories"])

# 명세서의 categories: Array 구조를 맞추기 위한 래퍼 스키마 (기존 구조 유지)
class RoutersCategoriesListResponse(BaseModel):
    categories: List[CategoriesRead]

@router.get("", response_model=RoutersCategoriesListResponse, status_code=status.HTTP_200_OK)
async def read_categories_routers_categories(db: AsyncSession = Depends(get_db)):
    # 서비스를 호출해서 결과만 깔끔하게 넘겨받음!
    return await Categories.get_category_list_services_categories(db)