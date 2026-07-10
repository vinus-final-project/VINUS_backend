import base64
import httpx
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.settings import settings
from app.db.crud.order import Order as OrderCrud      # ← crud.order (crud.payment 아님)
from app.db.models.orders import OdState
from app.db.scheme.payment import PaymentConfirmResponse
from app.memory.session.sessionCrud import SessionCrud
from app.fsm.event import Event, FSMEvent
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.interface.websocket.manager import manager

class Payment:

    # C - 결제 승인 요청 처리 (토스 API 연동 및 상태 변경)
    @staticmethod
    async def confirm_services_payment(
        db: AsyncSession,
        session_id: str,
        order_id: str,
        payment_key: str,
        amount: int,
    ):
        # 1) 메모리 세션 조회 (없으면 만료/오류)
        try:
            session = await SessionCrud.get_session_session_sessionCrud(session_id)
        except KeyError:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="해당 세션을 찾을 수 없습니다. (만료되었을 수 있음)",
            )

        # 2) 카트 비었는지 확인
        if not session.cart:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="장바구니가 비어 있습니다.",
            )

        # 3) 위변조 검증 — 요청 금액 == 메모리 카트 총액
        total_price = sum(ci.unit_price * ci.quantity for ci in session.cart)
        if amount != total_price:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="결제 요청 금액이 실제 주문 금액과 일치하지 않습니다. (위변조 위험)",
            )

        # 4) 토스 결제 승인 API 호출
        encoded = base64.b64encode(f"{settings.toss_secret_key}:".encode()).decode()
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "https://api.tosspayments.com/v1/payments/confirm",
                    headers={
                        "Authorization": f"Basic {encoded}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "paymentKey": payment_key,
                        "orderId": order_id,       # 프론트가 쓴 orderId 그대로
                        "amount": amount,
                    },
                    timeout=10.0,
                )
            except httpx.RequestError:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="토스 결제 서버와 통신할 수 없습니다.",
                )

        # 5) 승인 실패 → 세션 유지(재시도 가능), 에러 반환
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=response.json().get("message", "결제 승인 실패"),
            )

        # 6) 승인 성공 → 그 순간 메모리 카트를 DB에 저장(PAID)
        od_id = await OrderCrud.save_paid_order_crud_order(
            db=db,
            session=session,
            payment_key=payment_key,
            total_price=total_price,
        )

        # 7) PAYMENT_SUCCESS 이벤트 발행 → FSM COMPLETE 전이 + 세션 완료(메모리 삭제)
        #    (결제/DB 저장은 이미 끝났으므로 실패해도 응답은 성공 유지)
        session_response = await EventExecutor.execute_ruleEngine_eventExecutor(
            db=db,
            session=session,
            events=[FSMEvent(type=Event.PAYMENT_SUCCESS)],
            message="결제가 완료되었습니다. 감사합니다.",
        )

        # 8) WS 연결이 있으면 결제 완료 SessionResponse push (없으면 무시)
        try:
            await manager.send_json_websocket_manager(
                session_id, session_response.model_dump(mode="json"),
            )
        except Exception:
            pass

        # 9) 응답
        return PaymentConfirmResponse(
            success=True,
            od_id=od_id,
            od_state=OdState.PAID.value,
            od_no=0,  # 필요 시 저장함수에서 od_no도 반환하도록 확장 가능
        )