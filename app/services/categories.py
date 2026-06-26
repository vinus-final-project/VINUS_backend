from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.categories import CrudCategories

class ServicesCategories:
    @staticmethod
    async def get_category_list(db: AsyncSession):
        db_categories = await CrudCategories.get_all_categories(db)
    
        return {
        "categories": [
            {"c_id": c.c_id, "c_name": c.c_name}
            for c in db_categories
        ]
    }