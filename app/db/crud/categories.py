from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.categories import Categories as CategoriesModel


class Categories:
    @staticmethod
    async def get_all_categories_crud_categories(db: AsyncSession):
        query = select(CategoriesModel)
        result = await db.execute(query)
        return result.scalars().all()