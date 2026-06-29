from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.db.models.menus import Menus
from app.db.models.menuAllergies import MenuAllergies
from app.db.models.menuIngredients import MenuIngredients
from app.db.models.optionGroups import OptionGroups

class Menus:
    @staticmethod
    async def get_menus_by_category_crud_menuCrud(db: AsyncSession, c_id: int):
        # [수정] 모델 변수명 규칙에 맞춰서 category_id ➔ c_id로 변경했습니다.
        query = (
            select(Menus)
            # .options(joinedload(ModelsMenus.sold_outs)) 이거 품절테이블 빼서 같이 뺍니다 거기에 조인로드도 안써서 임포트 같이 뻅니다
            .where(Menus.c_id == c_id)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    @staticmethod # services/Menus.py에서 get_single_menu_detail에서 호출하는데 여기에 없어서 추가함
    async def get_menu_detail_crud_menuCrud(db: AsyncSession, m_id: int):
        query = (
            select(Menus)
            .options(
            joinedload(ModelsMenus.menu_allergies).joinedload(MenuAllergies.allergy),
            joinedload(Menus.menu_ingredients).joinedload(MenuIngredients.ingredient),
            joinedload(Menus.option_groups).joinedload(OptionGroups.options),
            )
            .where(Menus.m_id == m_id)
        )
        result = await db.execute(query)
        return result.scalars().first()
    #땅땅땅