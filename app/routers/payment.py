from fastapi import APIRouter, Depends, status, HTTPException
from fastapi.responses import HTMLResponse
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


# ──────────────────────────────────────────────────────────────
# 토스 리다이렉트 수신 (Capacitor apk 전용 흐름)
#
# apk 에서는 토스 결제창이 "외부 크롬"에서 열리므로 successUrl 을
# https://localhost(앱)로 줄 수 없다 — 크롬에는 그 주소가 없어서
# ERR_CONNECTION_REFUSED. 대신 successUrl/failUrl 을 이 엔드포인트로
# 지정한다:
#   1) 토스가 크롬을 이리로 리다이렉트 (성공: paymentKey/orderId/amount,
#      실패: code/message 쿼리)
#   2) 성공이면 서버가 직접 confirm(승인+DB저장+WS push) 수행
#      — confirm 내부의 WS PAYMENT_SUCCESS push 가 살아있는 앱 화면을
#        즉시 전환시킨다 (앱 WebView 는 /pay 에서 대기 중)
#   3) 응답 HTML 이 voiceinus:// 딥링크로 앱을 전면 복귀시킨다
#
# session_id 는 orderId 접두(UUID 36자)에서 복원 —
# 프론트가 orderId = f"{session_id}-{timestamp}" 로 생성한다.
# ──────────────────────────────────────────────────────────────
DEEPLINK_SUCCESS = "voiceinus://payment-success"
DEEPLINK_FAIL = "voiceinus://payment-fail"


def _deeplink_page_routers_payment(target: str, text: str) -> HTMLResponse:
    """딥링크 자동 이동 페이지 (meta refresh + JS + 수동 링크 3중 폴백)."""
    html = (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<meta http-equiv='refresh' content='0;url={target}'></head>"
        "<body style='font-family:sans-serif;text-align:center;padding-top:40vh;font-size:20px'>"
        f"{text}<br><br><a href='{target}'>앱으로 돌아가기</a>"
        f"<script>location.href='{target}';</script></body></html>"
    )
    return HTMLResponse(html)


@router.get("/toss/return")
async def toss_return_routers_payment(
    orderId: str = "",
    paymentKey: str = "",
    amount: int = 0,
    code: str | None = None,       # 토스 failUrl 리다이렉트에 붙는 실패 코드
    db: AsyncSession = Depends(get_db),
):
    # 실패 리다이렉트 or 필수 파라미터 누락
    if code or not paymentKey or not orderId:
        return _deeplink_page_routers_payment(
            DEEPLINK_FAIL, "결제가 완료되지 않았습니다."
        )

    session_id = orderId[:36]  # UUID 접두 복원
    try:
        await Payment.confirm_services_payment(
            db=db,
            session_id=session_id,
            order_id=orderId,
            payment_key=paymentKey,
            amount=amount,
        )
    except HTTPException:
        return _deeplink_page_routers_payment(
            DEEPLINK_FAIL, "결제 승인에 실패했습니다."
        )
    return _deeplink_page_routers_payment(
        DEEPLINK_SUCCESS, "결제가 완료되었습니다."
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
 