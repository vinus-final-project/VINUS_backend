from unittest import result

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.db.models.menus import ModelsMenus
from app.db.models.menuAllergies import ModelsMenuAllergy
from app.db.models.menuIngredients import ModelsMenuIngredient
from app.db.models.optionGroups import ModelsOptionGroups

class CrudMenus:
    @staticmethod
    async def get_menus_by_category(db: AsyncSession, category_id: int):
        # 특정 카테고리의 메뉴들을 가져오면서 품절 테이블(sold_outs) 상태 정보를 조인합니다.
        query = (
            select(ModelsMenus)
            # .options(joinedload(ModelsMenus.sold_outs)) 이거 품절테이블 빼서 같이 뺍니다 거기에 조인로드도 안써서 임포트 같이 뻅니다
            .where(ModelsMenus.category_id == category_id)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod # services/Menus.py에서 get_single_menu_detail에서 호출하는데 여기에 없어서 추가함
    async def get_menu_detail(db: AsyncSession, menu_id: int):
        query = (
            select(ModelsMenus)
            .options(
            joinedload(ModelsMenus.menu_allergies).joinedload(ModelsMenuAllergy.allergy),
            joinedload(ModelsMenus.menu_ingredients).joinedload(ModelsMenuIngredient.ingredient),
            joinedload(ModelsMenus.option_groups).joinedload(ModelsOptionGroups.options),
            )
            .where(ModelsMenus.m_id == menu_id)
        )
        result = await db.execute(query)
        return result.scalars().first()