from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from app.db.models.stores import ModelsStores

class CrudStores:
    @staticmethod
    async def get_store_info(db: AsyncSession):
        # 가게 정보와 매칭되는 브랜드 정보를 한 번에 조인해서 가져옵니다.
        query = select(ModelsStores).options(joinedload(ModelsStores.brand))
        result = await db.execute(query)
        return result.scalars().first()