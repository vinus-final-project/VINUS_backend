from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.db.models.menus import ModelsMenus

class CrudMenus:
    @staticmethod
    async def get_menus_by_category(db: AsyncSession, category_id: int):
        # 특정 카테고리의 메뉴들을 가져오면서 품절 테이블(sold_outs) 상태 정보를 조인합니다.
        query = (
            select(ModelsMenus)
            .options(joinedload(ModelsMenus.sold_outs))
            .where(ModelsMenus.category_id == category_id)
        )
        result = await db.execute(query)
        return result.scalars().all()