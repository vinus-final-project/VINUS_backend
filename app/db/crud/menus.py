from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.db.models.menus import ModelsMenus

class CrudMenus:
    @staticmethod
    async def get_menus_by_category(db: AsyncSession, category_id: int):
        # [수정] 모델 변수명 규칙에 맞춰서 category_id ➔ c_id로 변경했습니다.
        query = (
            select(ModelsMenus)
            .options(joinedload(ModelsMenus.sold_outs))
            .where(ModelsMenus.c_id == category_id)  
        )
        result = await db.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_menu_detail(db: AsyncSession, menu_id: int):
        # [추가] 상세 페이지용 복잡한 조인(알레르기, 성분, 옵션)들을 여기서 한 번에 처리합니다.
        # [수정] 모델 변수명 규칙에 맞춰서 menu_id ➔ m_id로 매칭했습니다.
        query = (
            select(ModelsMenus)
            .options(
                joinedload(ModelsMenus.menu_allergies).joinedload(ModelsMenus.menu_allergies.allergy),
                joinedload(ModelsMenus.menu_ingredients).joinedload(ModelsMenus.menu_ingredients.ingredient),
                joinedload(ModelsMenus.option_groups).joinedload(ModelsMenus.option_groups.options)
            )
            .where(ModelsMenus.m_id == menu_id)  
        )
        result = await db.execute(query)
        return result.scalars().first()  # 단건 조회의 경우 .first()를 사용합니다.