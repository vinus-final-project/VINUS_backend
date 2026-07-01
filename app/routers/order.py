"""주문(터치) 라우터.

Android 터치 주문 요청을 받아 FSM 이벤트로 변환하고,
EventExecutor 를 태워 SessionResponse 로 응답한다.
음성(WebSocket) 흐름과 동일한 파이프라인을 재사용한다.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.memory.session.sessionCrud import SessionCrud
from app.memory.session.enums import OrderItemStatus
from app.fsm.event import Event, FSMEvent
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.interface.dto.sessionResponse import SessionResponse

# prefix=/orders : 이 파일의 모든 엔드포인트는 /orders 하위
router = APIRouter(prefix="/orders", tags=["Orders"])


# ---------------------------------------------------------------------------
# 공통 헬퍼 : session_id 로 메모리 세션을 조회 (없으면 404)
#   - SessionCrud.get_session... 은 세션이 없으면 KeyError 를 던지므로
#     이를 HTTP 404 로 변환한다.
# ---------------------------------------------------------------------------
async def _get_session_or_404(session_id: str):
    try:
        return await SessionCrud.get_session_session_sessionCrud(session_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다.",
        )


# ---------------------------------------------------------------------------
# 요청 스키마 (Android → Server)
# ---------------------------------------------------------------------------
class OrderCreateRequest(BaseModel):
    session_id: str   # 대상 세션 UUID
    menu_id: int      # 선택한 메뉴 ID

class QuantityRequest(BaseModel):
    session_id: str   # 대상 세션 UUID
    quantity: int     # 지정할 수량 (1 이상)

class OptionRequest(BaseModel):
    session_id: str   # 대상 세션 UUID
    option_id: int    # 선택한 옵션 ID (필수/선택은 서버가 판별)

class CompleteRequest(BaseModel):
    session_id: str   # 대상 세션 UUID


# ---------------------------------------------------------------------------
# C - 주문 항목 생성 (메뉴 선택)
#     터치 "메뉴 선택" → SELECT_MENU 이벤트
#     → OrderController.create_order_item (order_item 생성)
# ---------------------------------------------------------------------------
@router.post("", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def create_order_routers_order(
    body: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    # 1) 세션 조회
    session = await _get_session_or_404(body.session_id)

    # 2) 메뉴 선택 이벤트 생성 (parameters 에 menu_id 실어 전달)
    event = FSMEvent(
        type=Event.SELECT_MENU,
        parameters={"menu_id": body.menu_id},
    )

    # 3) EventExecutor 실행 → SessionResponse 반환
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# ---------------------------------------------------------------------------
# U - 수량 지정
#     터치 "수량 입력" → SET_QUANTITY 이벤트
#     → OrderController.set_quantity (수량 저장 + status=ASKING_OPTIONAL_OPTION)
# ---------------------------------------------------------------------------
@router.post("/quantity", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def set_quantity_routers_order(
    body: QuantityRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    # 1) 세션 조회
    session = await _get_session_or_404(body.session_id)

    # 2) 수량 지정 이벤트 생성
    event = FSMEvent(
        type=Event.SET_QUANTITY,
        parameters={"quantity": body.quantity},
    )

    # 3) 실행
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# ---------------------------------------------------------------------------
# U - 옵션 선택 (필수/선택 자동 판별)
#     현재 order_item.status 로 어떤 옵션 단계인지 판단해
#     필수(SELECT_REQUIRED_OPTION) 또는 선택(SELECT_OPTIONAL_OPTION) 이벤트로 분기.
#     프론트는 option_id 만 보내면 되고, 구분은 서버가 처리.
# ---------------------------------------------------------------------------
@router.post("/option", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def select_option_routers_order(
    body: OptionRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    # 1) 세션 조회
    session = await _get_session_or_404(body.session_id)

    # 2) 작성 중인 주문(order_item)이 없으면 옵션 선택 불가
    if session.order_item is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ORDER_ITEM_NOT_FOUND",
        )

    # 3) 현재 상태로 필수/선택 옵션 단계 판별
    st = session.order_item.status
    if st == OrderItemStatus.SELECTING_REQUIRED_OPTION:
        # 필수 옵션 선택 중
        event_type = Event.SELECT_REQUIRED_OPTION
    elif st == OrderItemStatus.ASKING_OPTIONAL_OPTION:
        # 추가(선택) 옵션 확인 중
        event_type = Event.SELECT_OPTIONAL_OPTION
    else:
        # 그 외 상태(수량 선택 중 등)에선 옵션 선택 불가
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="INVALID_ORDER_ITEM_STATE",
        )

    # 4) 판별된 옵션 이벤트 생성 후 실행
    event = FSMEvent(
        type=event_type,
        parameters={"option_id": body.option_id},
    )
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# ---------------------------------------------------------------------------
# U - 주문 항목 완료 (장바구니 담기)
#     터치 "담기" → SKIP_OPTIONAL_OPTION 이벤트
#     → complete_order_item(완료 검증) + add_to_cart(카트 이동, order_item 제거)
# ---------------------------------------------------------------------------
@router.post("/complete", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def complete_order_routers_order(
    body: CompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    # 1) 세션 조회
    session = await _get_session_or_404(body.session_id)

    # 2) 완료 이벤트 생성 (파라미터 없음)
    event = FSMEvent(
        type=Event.SKIP_OPTIONAL_OPTION,
        parameters={},
    )

    # 3) 실행 (내부에서 카트 이동까지 처리)
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )