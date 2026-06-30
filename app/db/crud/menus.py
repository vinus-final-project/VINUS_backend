from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.db.models.menus import Menus as MenusModel
from app.db.models.menuAllergies import MenuAllergies
from app.db.models.menuIngredients import MenuIngredients
from app.db.models.optionGroups import OptionGroups


class Menus:
    @staticmethod
    async def get_menus_by_category_crud_menus(db: AsyncSession, c_id: int):
        query = (
            select(MenusModel)
            .where(MenusModel.c_id == c_id)
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_menu_detail_crud_menus(db: AsyncSession, m_id: int):
        query = (
            select(MenusModel)
            .options(
                joinedload(MenusModel.menu_allergies).joinedload(MenuAllergies.allergy),
                joinedload(MenusModel.menu_ingredients).joinedload(MenuIngredients.ingredient),
                joinedload(MenusModel.option_groups).joinedload(OptionGroups.options),
            )
            .where(MenusModel.m_id == m_id)
        )
        result = await db.execute(query)
        return result.scalars().first()