import base64
import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.paymentCrud import CrudPaymentCrud
from app.core.settings import settings

class ServicesPayment:

    @staticmethod
    async def confirm_services_payment(db: AsyncSession, payment_key: str, order_id: int, amount: int):
        # 1. 주문 존재 여부 확인
        order = await CrudPaymentCrud.get_crud_paymentCrud(db, order_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 주문을 찾을 수 없습니다."
            )

        # 2. 토스 결제 승인 API 호출
        encoded = base64.b64encode(f"{settings.toss_secret_key}:".encode()).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.tosspayments.com/v1/payments/confirm",
                headers={
                    "Authorization": f"Basic {encoded}",
                    "Content-Type": "application/json"
                },
                json={
                    "paymentKey": payment_key,
                    "orderId": str(order_id),
                    "amount": amount
                }
            )

        # 3. 토스 응답 처리
        if response.status_code == 200:
            await CrudPaymentCrud.update_crud_paymentCrud(db, order_id, "PAID")
            return {"success": True, "od_id": order_id, "od_state": "PAID"}
        else:
            await CrudPaymentCrud.update_crud_paymentCrud(db, order_id, "CANCELLED")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.json().get("message", "결제 승인 실패")
            )