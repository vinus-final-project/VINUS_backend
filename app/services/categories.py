from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.categories import Categories as CategoriesCrud   # 2번 줄

class Categories:
    @staticmethod
    async def get_category_list_services_categories(db: AsyncSession):
        db_categories = await CategoriesCrud.get_all_categories_crud_categories(db)

        return {
        "categories": [
            {"c_id": c.c_id, "c_name": c.c_name}
            for c in db_categories
        ]
    }