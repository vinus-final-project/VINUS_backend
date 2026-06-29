from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.categories import ModelsCategories

class CrudCategories:
    @staticmethod
    async def get_all_categories(db: AsyncSession):
        # 모든 카테고리 리스트를 조회합니다.
        query = select(ModelsCategories)
        result = await db.execute(query)
        return result.scalars().all()