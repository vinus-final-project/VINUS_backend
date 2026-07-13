from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.db.models.menus import Menus as MenusModel
from app.db.models.menuAllergies import MenuAllergies
from app.db.models.menuIngredients import MenuIngredients
from app.db.models.optionGroups import OptionGroups


class Menus:

    # R - 카테고리로 메뉴 조회
    @staticmethod
    async def get_menus_by_category_crud_menus(db: AsyncSession, c_id: int):
        query = (
            select(MenusModel)
            .where(MenusModel.c_id == c_id)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    # R - 전체 메뉴 조회 (부트스트랩 일괄 응답용)
    @staticmethod
    async def get_all_menus_crud_menus(db: AsyncSession):
        result = await db.execute(select(MenusModel))
        return result.scalars().all()

    # R - 추천 후보 메뉴 조회 (설명 키워드 매칭, keyword 없으면 상위 limit개)
    @staticmethod
    async def search_menus_by_keyword_crud_menus(
        db: AsyncSession, keyword: str | None = None, limit: int = 3
    ):
        query = select(MenusModel)
        if keyword:
            query = query.where(MenusModel.m_description.like(f"%{keyword}%"))
        query = query.limit(limit)
        result = await db.execute(query)
        return result.scalars().all()

    # R - 메뉴 상세 조회
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