from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.categories import Categories

class Categories:
    @staticmethod
    async def get_category_list_services_categories(db: AsyncSession):
        db_categories = await Categories.get_all_categories_crud_categories(db)

        return {
        "categories": [
            {"c_id": c.c_id, "c_name": c.c_name}
            for c in db_categories
        ]
    }