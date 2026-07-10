"""Event Executor.

Rule Engine/LLM 이 생성한 Event List 를 FIFO 로 실행하고
최종 SessionResponse 를 생성한다.

- 각 이벤트 → FSM.dispatch (validator + controller + 상태전이)
- 실패 시 즉시 중단 + ERROR SessionResponse 반환
- Rollback 없음
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.fsm.dispatcher import Dispatcher
from app.fsm.event import FSMEvent
from app.fsm.FSMstate import FSMState
from app.memory.session.enums import SessionStatus
from app.memory.session.session import Session
from app.interface.dto.sessionResponse import ResponseType, SessionResponse
from app.interface.dto.errorMessage import get_error_message_error_message


class EventExecutor:

    @staticmethod
    async def execute_ruleEngine_eventExecutor(
        db: AsyncSession,
        session: Optional[Session],
        events: list[FSMEvent],
        message: Optional[str] = None,          # ← 추가: 정상 안내 문구 (RuleEngine/LLM)
    ) -> SessionResponse:
        """Event List FIFO 실행 → SessionResponse"""

        # FIFO 순차 실행
        for fsm_event in events:
            try:
                session = await Dispatcher.dispatch_fsm_dispatcher(
                    db=db,
                    session=session,
                    fsm_event=fsm_event,
                )
            except Exception as exc:
                # 실패 → 즉시 중단 + 에러 응답 (message 무시, error_code 맵 우선)
                return EventExecutor._build_error_ruleEngine_eventExecutor(
                    session=session,
                    exc=exc,
                )

        # 성공 → 정상 안내 문구 세팅
        #   매 실행마다 세팅(문구 없으면 None) → 이전 턴 문구 잔류 방지
        if session is not None:
            session.message = message

        # 모든 이벤트 성공 (Event 없음도 여기로) → 정상 응답
        return EventExecutor._build_success_ruleEngine_eventExecutor(session)

    # ------------------------------------------------------------------
    # 정상 응답 조립
    # ------------------------------------------------------------------
    @staticmethod
    def _build_success_ruleEngine_eventExecutor(
        session: Session,
    ) -> SessionResponse:
        ended = session.session_status != SessionStatus.ACTIVE
        return SessionResponse(
            response_type=(
                ResponseType.SESSION_END if ended else ResponseType.NORMAL
            ),
            session_id=session.session_id,
            success=True,
            message=session.message,
            fsm_state=session.fsm_state,
            order_type=session.order_type,
            order_item=session.order_item,
            current_menu=session.current_menu,
            cart=session.cart,
            total_price=sum(ci.unit_price * ci.quantity for ci in session.cart),
            recommendation_list=session.recommendation_list,
            error_code=None,
            session_end=ended,
        )

    # ------------------------------------------------------------------
    # 에러 응답 조립
    # ------------------------------------------------------------------
    @staticmethod
    def _build_error_ruleEngine_eventExecutor(
        session: Optional[Session],
        exc: Exception,
    ) -> SessionResponse:
        return SessionResponse(
            response_type=ResponseType.ERROR,
            session_id=session.session_id if session else "",
            success=False,
            message=get_error_message_error_message(str(exc)),
            fsm_state=session.fsm_state if session else FSMState.INIT,
            order_type=session.order_type if session else None,
            order_item=session.order_item if session else None,
            current_menu=session.current_menu if session else None,
            cart=session.cart if session else [],
            total_price=(
                sum(ci.unit_price * ci.quantity for ci in session.cart) if session else 0
            ),
            recommendation_list=(
                session.recommendation_list if session else []
            ),
            error_code=str(exc),
            session_end=False,
        )