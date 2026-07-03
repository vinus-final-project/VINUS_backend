from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.orders import Orders, OdState

class Payment:
    """결제 관련 DB 조작"""

    # R - 결제 조회
    @staticmethod
    async def get_crud_payment(db: AsyncSession, od_id: int):
        query = select(Orders).where(Orders.od_id == od_id)
        result = await db.execute(query)
        return result.scalars().first()

    # U - 결제 상태 변경
    @staticmethod
    async def update_crud_payment(db: AsyncSession, od_id: int, od_state: OdState):
        query = select(Orders).where(Orders.od_id == od_id)
        result = await db.execute(query)
        order = result.scalars().first()

        if order:
            order.od_state = od_state
            await db.commit()
            await db.refresh(order)

        return order