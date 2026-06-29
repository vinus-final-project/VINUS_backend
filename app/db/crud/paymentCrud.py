from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.orders import ModelsOrders
from app.db.models.orders import ModelsOrders, OdState

class CrudPaymentCrud:

    @staticmethod
    async def get_crud_paymentCrud(db: AsyncSession, od_id: int):
        query = select(ModelsOrders).where(ModelsOrders.od_id == od_id)
        result = await db.execute(query)
        return result.scalars().first()

    @staticmethod
    async def update_crud_paymentCrud(db: AsyncSession, od_id: int, od_state: OdState):
        query = select(ModelsOrders).where(ModelsOrders.od_id == od_id)
        result = await db.execute(query)
        order = result.scalars().first()

        if order:
            order.od_state = od_state
            await db.commit()
            await db.refresh(order)

        return order