import base64
import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.crud.payment import Payment as PaymentCrud
from app.core.settings import settings
from app.db.models.orders import OdState
from app.db.scheme.payment import PaymentConfirmResponse

class Payment:

    @staticmethod
    async def confirm_services_payment(db: AsyncSession, session_id: str, amount: int):
        # 1. session_id를 기반으로 DB에서 주문 존재 여부 확인
        order = await PaymentCrud.get_crud_payment_by_session(db, session_id)
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 세션의 주문을 찾을 수 없습니다."
            )

        # 2. DB 내부에 토스 영수증 키(pa_key)가 정상적으로 들어가 있는지 검증
        # (프론트가 결제 성공 시점에 우리 DB에 pa_key를 등록해 둔 상태여야 꺼내올 수 있습니다)
        toss_payment_key = getattr(order, "pa_key", None)
        if not toss_payment_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="해당 주문에 등록된 결제 영수증 키(paymentKey)가 누락되었습니다."
            )

        # 🛡️ 보안 금액 위변조 검증 (원래 DB 가격과 요청 금액 대조)
        # ※ 실제 모델의 주문금액 필드명(예: total_price 등)에 맞게 매핑하세요.
        if getattr(order, "total_price", amount) != amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="결제 요청 금액이 실제 주문 금액과 일치하지 않습니다. (위변조 위험)"
            )

        # 3. 토스 결제 승인 API 호출 준비
        encoded = base64.b64encode(f"{settings.toss_secret_key}:".encode()).decode()

        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.tosspayments.com/v1/payments/confirm",
                    headers={
                        "Authorization": f"Basic {encoded}",
                        "Content-Type": "application/json"
                    },
                    json={
                        # DB에서 꺼내온 진짜 영수증 키와 주문 ID(od_id)를 자동으로 가공해 전송합니다.
                        "paymentKey": toss_payment_key,
                        "orderId": str(order.od_id),
                        "amount": amount
                    },
                    timeout=10.0
                )
            except httpx.RequestError:
                await PaymentCrud.update_crud_payment(db, order.od_id, OdState.CANCELLED)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="토스 결제 서버와 통신할 수 없습니다."
                )

        # 4. 토스 응답 처리 및 DB 반영
        if response.status_code == 200:
            updated_order = await PaymentCrud.update_crud_payment(db, order.od_id, OdState.PAID)
            return PaymentConfirmResponse(
                success=True, 
                od_id=order.od_id, 
                od_state=updated_order.od_state.value if hasattr(updated_order.od_state, 'value') else str(updated_order.od_state)
            )
        else:
            await PaymentCrud.update_crud_payment(db, order.od_id, OdState.CANCELLED)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.json().get("message", "결제 승인 실패")
            )