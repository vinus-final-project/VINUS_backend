from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.memory.session.sessionCrud import SessionCrud
from app.fsm.event import Event, FSMEvent
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.interface.dto.sessionResponse import SessionResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


# 세션 조회 (없으면 404)
async def _get_session_or_404(session_id: str):
    try:
        return await SessionCrud.get_session_session_sessionCrud(session_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다.",
        )


# -- 요청 스키마 --
class OrderCreateRequest(BaseModel):
    session_id: str
    menu_id: int

class QuantityRequest(BaseModel):
    session_id: str
    quantity: int

class OptionRequest(BaseModel):
    session_id: str
    option_id: int

class CompleteRequest(BaseModel):
    session_id: str

class CancelRequest(BaseModel):
    session_id: str


# 메뉴 선택 → SELECT_MENU
@router.post("", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def create_order_routers_order(
    body: OrderCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await _get_session_or_404(body.session_id)
    event = FSMEvent(type=Event.SELECT_MENU, parameters={"menu_id": body.menu_id})
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# 수량 지정 → SET_QUANTITY
@router.post("/quantity", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def set_quantity_routers_order(
    body: QuantityRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await _get_session_or_404(body.session_id)
    event = FSMEvent(type=Event.SET_QUANTITY, parameters={"quantity": body.quantity})
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# 옵션 선택 → 통합 핸들러(교체/토글). 이벤트 종류는 무관
@router.post("/option", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def select_option_routers_order(
    body: OptionRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await _get_session_or_404(body.session_id)

    if session.order_item is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ORDER_ITEM_NOT_FOUND",
        )

    event = FSMEvent(
        type=Event.SELECT_REQUIRED_OPTION,  # dispatcher가 통합 처리
        parameters={"option_id": body.option_id},
    )
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# 현재 주문 취소 → CANCEL_ORDER_ITEM
@router.post("/cancel", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def cancel_order_routers_order(
    body: CancelRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await _get_session_or_404(body.session_id)
    event = FSMEvent(type=Event.CANCEL_ORDER_ITEM, parameters={})
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# 주문 완료(카트 담기) → SKIP_OPTIONAL_OPTION
@router.post("/complete", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def complete_order_routers_order(
    body: CompleteRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await _get_session_or_404(body.session_id)
    event = FSMEvent(type=Event.SKIP_OPTIONAL_OPTION, parameters={})
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )