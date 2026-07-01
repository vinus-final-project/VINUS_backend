"""장바구니(터치) 라우터.

세션에 담긴 장바구니(cart)에 대한 조회/삭제/수량증감 요청을
FSM 이벤트로 변환해 EventExecutor 로 처리한다.
경로는 세션 하위(/sessions/{session_id}/cart)로 구성.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.memory.session.sessionCrud import SessionCrud
from app.fsm.event import Event, FSMEvent
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.interface.dto.sessionResponse import SessionResponse

# prefix=/sessions : 카트 경로가 /sessions/{session_id}/cart 형태라 세션 하위에 둠
router = APIRouter(prefix="/sessions", tags=["Cart"])


# ---------------------------------------------------------------------------
# 공통 헬퍼 : session_id 로 메모리 세션 조회 (없으면 404)
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
# 요청 스키마 : 카트 수량 증감
#   delta > 0 → 증가, delta < 0 → 감소 (크기만큼 반복 적용)
# ---------------------------------------------------------------------------
class CartQuantityPatchRequest(BaseModel):
    delta: int   # +1 증가 / -1 감소


# ---------------------------------------------------------------------------
# R - 장바구니 조회
#     터치 "장바구니 보기" → SHOW_CART 이벤트
#     (응답 SessionResponse.cart 에 현재 카트가 담겨 반환됨)
# ---------------------------------------------------------------------------
@router.get("/{session_id}/cart", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def get_cart_routers_cart(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    # 1) 세션 조회
    session = await _get_session_or_404(session_id)

    # 2) 장바구니 조회 이벤트 (파라미터 없음)
    event = FSMEvent(type=Event.SHOW_CART, parameters={})

    # 3) 실행 → SessionResponse(cart 포함) 반환
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# ---------------------------------------------------------------------------
# D - 장바구니 항목 삭제
#     터치 "항목 삭제" → REMOVE_CART_ITEM 이벤트
#     → CartController.remove_cart_item (해당 cart_item 제거)
# ---------------------------------------------------------------------------
@router.delete("/{session_id}/cart/{cart_item_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def remove_cart_item_routers_cart(
    session_id: str,
    cart_item_id: int,   # 삭제할 카트 아이템 ID (세션 내 식별자)
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    # 1) 세션 조회
    session = await _get_session_or_404(session_id)

    # 2) 삭제 이벤트 생성 (cart_item_id 전달)
    event = FSMEvent(
        type=Event.REMOVE_CART_ITEM,
        parameters={"cart_item_id": cart_item_id},
    )

    # 3) 실행
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=[event],
    )


# ---------------------------------------------------------------------------
# U - 장바구니 항목 수량 증감
#     터치 "수량 +/-" → delta 부호로 방향 결정
#       delta > 0 → INCREASE_CART_ITEM
#       delta < 0 → DECREASE_CART_ITEM (수량 0이면 항목 삭제)
#     |delta| 만큼 이벤트를 반복 생성해 순차 적용.
# ---------------------------------------------------------------------------
@router.patch("/{session_id}/cart/{cart_item_id}", response_model=SessionResponse, status_code=status.HTTP_200_OK)
async def update_cart_item_routers_cart(
    session_id: str,
    cart_item_id: int,   # 대상 카트 아이템 ID
    body: CartQuantityPatchRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    # 1) 세션 조회
    session = await _get_session_or_404(session_id)

    # 2) delta 부호로 증가/감소 이벤트 종류 결정
    event_type = (
        Event.INCREASE_CART_ITEM if body.delta > 0 else Event.DECREASE_CART_ITEM
    )

    # 3) |delta| 만큼 이벤트 반복 생성 (delta=0 이면 빈 리스트 → 상태 그대로 반환)
    events = [
        FSMEvent(type=event_type, parameters={"cart_item_id": cart_item_id})
        for _ in range(abs(body.delta))
    ]

    # 4) 실행
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db, session=session, events=events,
    )