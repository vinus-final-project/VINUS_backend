from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.memory.session.sessionCrud import SessionCrud
from app.fsm.event import Event, FSMEvent
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.interface.dto.sessionResponse import SessionResponse

router = APIRouter(prefix="/orders", tags=["Orders"])


# ------------------------------------------------------------------
# 공통 헬퍼 : session_id 로 메모리 세션 조회 (없으면 404)
# ------------------------------------------------------------------
async def _get_session_or_404(session_id: str):
    try:
        return await SessionCrud.get_session_session_sessionCrud(session_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다.",
        )


# ------------------------------------------------------------------
# 요청 스키마
# ------------------------------------------------------------------
class OrderCreateRequest(BaseModel):
    session_id: str   # 대상 세션 UUID
    menu_id: int      # 선택한 메뉴 ID

class QuantityRequest(BaseModel):
    session_id: str   # 대상 세션 UUID
    quantity: int     # 지정할 수량 (1 이상)

class OptionRequest(BaseModel):
    session_id: str   # 대상 세션 UUID
    option_id: int    # 추가/감소할 옵션 ID

class CancelRequest(BaseModel):
    session_id: str   # 대상 세션 UUID

class CompleteRequest(BaseModel):
    session_id: str   # 대상 세션 UUID


# ------------------------------------------------------------------
# C - 주문 항목 생성 (메뉴 선택) → SELECT_MENU
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# U - 수량 지정 → SET_QUANTITY
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# U - 옵션 추가 (+1) → SELECT_OPTION
#     누적 옵션은 여러 번 호출하면 개수 증가 (단일선택 그룹은 교체)
# ------------------------------------------------------------------
@router.post("/option", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def select_option_routers_order(
    body: OptionRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await _get_session_or_404(body.session_id)
    event = FSMEvent(type=Event.SELECT_OPTION, parameters={"option_id": body.option_id})
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# ------------------------------------------------------------------
# U - 옵션 감소 (-1) → DESELECT_OPTION
#     해당 옵션 개수 하나 제거
# ------------------------------------------------------------------
@router.post("/option/remove", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def deselect_option_routers_order(
    body: OptionRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    session = await _get_session_or_404(body.session_id)
    event = FSMEvent(type=Event.DESELECT_OPTION, parameters={"option_id": body.option_id})
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# ------------------------------------------------------------------
# D - 현재 주문 취소 → CANCEL_ORDER_ITEM
# ------------------------------------------------------------------
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


# ------------------------------------------------------------------
# U - 주문 완료(장바구니 담기) → SKIP_OPTIONAL_OPTION
#     완료 검증 후 cart 로 이동 (order_item 제거)
# ------------------------------------------------------------------
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