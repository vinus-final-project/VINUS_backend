from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.categories import CrudCategories

class ServicesCategories:
    @staticmethod
    async def get_category_list(db: AsyncSession):
        # 1. DB에서 카테고리 전체 목록 조회 (CRUD 호출)
        db_categories = await CrudCategories.get_all_categories(db)
        
        # 2. 명세서 구조인 {"categories": [...]} 모양으로 가공해서 반환
        return {"categories": db_categories}