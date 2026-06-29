from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.db.models.menus import ModelsMenus
from app.db.models.menuAllergies import ModelsMenuAllergies
from app.db.models.menuIngredients import ModelsMenuIngredients
from app.db.models.optionGroups import ModelsOptionGroups

class CrudMenus:
    @staticmethod
    async def get_menus_by_category(db: AsyncSession, c_id: int):
        # [수정] 모델 변수명 규칙에 맞춰서 category_id ➔ c_id로 변경했습니다.
        query = (
            select(ModelsMenus)
            # .options(joinedload(ModelsMenus.sold_outs)) 이거 품절테이블 빼서 같이 뺍니다 거기에 조인로드도 안써서 임포트 같이 뻅니다
            .where(ModelsMenus.c_id == c_id)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod # services/Menus.py에서 get_single_menu_detail에서 호출하는데 여기에 없어서 추가함
    async def get_menu_detail(db: AsyncSession, m_id: int):
        query = (
            select(ModelsMenus)
            .options(
            joinedload(ModelsMenus.menu_allergies).joinedload(ModelsMenuAllergies.allergy),
            joinedload(ModelsMenus.menu_ingredients).joinedload(ModelsMenuIngredients.ingredient),
            joinedload(ModelsMenus.option_groups).joinedload(ModelsOptionGroups.options),
            )
            .where(ModelsMenus.m_id == m_id)
        )
        result = await db.execute(query)
        return result.scalars().first()