from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from pydantic import BaseModel
from app.db.database import get_db
from app.db.scheme.categories import SchemeCategoriesRead
from app.db.crud.categories import CrudCategories

router = APIRouter(prefix="/categories", tags=["Categories"])

# 명세서의 categories: Array 구조를 맞추기 위한 래퍼 스키마
class CategoryListResponse(BaseModel):
    categories: List[SchemeCategoriesRead]

@router.get("", response_model=CategoryListResponse, status_code=status.HTTP_200_OK)
async def read_categories(db: AsyncSession = Depends(get_db)):
    db_categories = await CrudCategories.get_all_categories(db)
    # {'categories': [...]} 형태로 반환하여 명세서 구조와 100% 일치시킵니다.
    return {"categories": db_categories}