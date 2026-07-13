from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.db.scheme.payment import PaymentConfirmRequest, PaymentConfirmResponse
from app.db.crud.order import Order as OrderCrud
from app.services.payment import Payment
from app.services.receipt import Receipt
from app.memory.session.sessionCrud import SessionCrud
from app.fsm.event import Event, FSMEvent
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.interface.dto.sessionResponse import SessionResponse

router = APIRouter(prefix="/payments", tags=["Payments"])


# 결제 시작 요청
class PaymentRequest(BaseModel):
    session_id: str
 
 
# 영수증 재출력 요청/응답
class ReceiptReprintRequest(BaseModel):
    od_id: int
 
 
class ReceiptReprintResponse(BaseModel):
    success: bool
    od_id: int


# 세션 조회 (없으면 404)
async def _get_session_or_404(session_id: str):
    try:
        return await SessionCrud.get_session_session_sessionCrud(session_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다.",
        )


# 결제 시작 → START_PAYMENT (ORDERING→PAYMENT, total_price 반환)
@router.post("/start", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def start_payment_routers_payment(
    body: PaymentRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await _get_session_or_404(body.session_id)
    event = FSMEvent(type=Event.START_PAYMENT, parameters={})
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# 결제 승인 (토스 confirm)
@router.post("/confirm", response_model=PaymentConfirmResponse, status_code=status.HTTP_200_OK)
async def confirm_routers_payment(
    payment_data: PaymentConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    return await Payment.confirm_services_payment(
        db=db,
        session_id=payment_data.session_id,
        order_id=payment_data.order_id,
        payment_key=payment_data.payment_key,
        amount=payment_data.amount,
    )


# 결제 취소 → PAYMENT_CANCEL (PAYMENT → ORDERING)
@router.post("/cancel", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def cancel_payment_routers_payment(
    body: PaymentRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await _get_session_or_404(body.session_id)
    event = FSMEvent(type=Event.PAYMENT_CANCEL, parameters={})
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )

 
# 영수증 재출력 — 자동 출력 실패/고객 재발급 요청 대비
@router.post("/receipt", response_model=ReceiptReprintResponse, status_code=status.HTTP_200_OK)
async def reprint_receipt_routers_payment(
    body: ReceiptReprintRequest,
    db: AsyncSession = Depends(get_db),
) -> ReceiptReprintResponse:
    order = await OrderCrud.get_paid_order_crud_order(db=db, od_id=body.od_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="주문을 찾을 수 없습니다.",
        )
 
    receipt_data = Receipt.build_from_order_services_receipt(order)
    ok = await Receipt.print_services_receipt(receipt_data)
    if not ok:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="영수증 출력에 실패했습니다. 프린터 상태(전원/용지/연결)를 확인하세요.",
        )
    return ReceiptReprintResponse(success=True, od_id=body.od_id)
 