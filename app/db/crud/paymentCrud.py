from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.db.models.orders import ModelsOrders

class PaymentCrud:
    """결제 관련 DB 조작"""
    
    @staticmethod
    async def get_order_by_session_id_crud_paymentCrud(db: AsyncSession, se_id: str):
        """
        세션 ID로 주문 찾기
        결제 콜백에서 사용 (PG사 → 어떤 주문인지 찾기)
        """
        query = select(ModelsOrders).where(ModelsOrders.se_id == se_id)
        result = await db.execute(query)
        return result.scalars().first()
    
    
    @staticmethod
    async def update_order_status_crud_paymentCrud(db: AsyncSession, od_id: int, od_state: str):
        """
        주문 상태 업데이트
        pending → paid (결제 성공)
        pending → cancelled (결제 실패)
        """
        query = select(ModelsOrders).where(ModelsOrders.od_id == od_id)
        result = await db.execute(query)
        order = result.scalars().first()
        
        if order:
            order.od_state = od_state
            await db.commit()
            await db.refresh(order)
        
        return order