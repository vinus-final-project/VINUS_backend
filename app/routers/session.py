from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_db
from app.memory.session.enums import OrderType
from app.memory.session.sessionCrud import SessionCrud
from app.fsm.event import Event, FSMEvent
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.interface.dto.sessionResponse import SessionResponse

router = APIRouter(prefix="/sessions", tags=["Sessions"])


# 요청 스키마 (매장/포장)
class SessionCreateRequest(BaseModel):
    order_type: OrderType


# C - 세션 생성 (SELECT_ORDER_TYPE 이벤트로 EventExecutor 경유)
@router.post(
    "",
    response_model=SessionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_session_routers_session(
    body: SessionCreateRequest,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    event = FSMEvent(
        type=Event.SELECT_ORDER_TYPE,
        parameters={"order_type": body.order_type.value},
    )
    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db,
        session=None,
        events=[event],
    )


# R - 세션 조회 (빈 이벤트로 현재 상태 SessionResponse 반환)
@router.get(
    "/{session_id}",
    response_model=SessionResponse,
    status_code=status.HTTP_200_OK,
)
async def get_session_routers_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
) -> SessionResponse:
    try:
        session = await SessionCrud.get_session_session_sessionCrud(session_id)
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="세션을 찾을 수 없습니다.",
        )

    return await EventExecutor.execute_ruleEngine_eventExecutor(
        db=db,
        session=session,
        events=[],
    )