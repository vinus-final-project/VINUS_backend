"""Event Executor.

Rule Engine/LLM 이 생성한 Event List 를 FIFO 로 실행하고
최종 SessionResponse 를 생성한다.

- 각 이벤트 → FSM.dispatch (validator + controller + 상태전이)
- 실패 시 즉시 중단 + ERROR SessionResponse 반환
- Rollback 없음
"""

from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.fsm.dispatcher import Dispatcher
from app.fsm.event import Event, FSMEvent
from app.fsm.FSMstate import FSMState
from app.memory.session.enums import SessionStatus, SpeakerType
from app.memory.session.session import Session
from app.memory.session.sessionCrud import SessionCrud
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

        # 이전 턴 문구 잔류 방지 — 실행 시작 시 초기화
        #   (Controller 가 실행 중 안내 문구를 세팅할 수 있음: 추천 등)
        if session is not None:
            session.message = None

        # 롤백용 스냅샷 — 부분 실행 실패 시 실행 전 상태로 복원(원자성).
        #   세션이 이번 실행 중 생성되는 경우(snapshot=None)는 복원 대상 아님.
        snapshot = session.model_copy(deep=True) if session is not None else None

        # FIFO 순차 실행
        for fsm_event in events:
            try:
                session = await Dispatcher.dispatch_fsm_dispatcher(
                    db=db,
                    session=session,
                    fsm_event=fsm_event,
                )
            except Exception as exc:
                # 실패 → 즉시 중단. 이미 실행된 앞 이벤트를 스냅샷으로 롤백
                if snapshot is not None:
                    await SessionCrud.update_session_session_sessionCrud(snapshot)
                    session = snapshot
                # 에러 응답 (message 무시, error_code 맵 우선)
                response = EventExecutor._build_error_ruleEngine_eventExecutor(
                    session=session,
                    exc=exc,
                )
                await EventExecutor._touch_and_log_ruleEngine_eventExecutor(
                    session, response.message,
                )
                return response

        # 성공 → 호출자(RuleEngine/LLM) 문구가 있으면 우선 적용
        #   (없으면 Controller 가 세팅한 문구 유지 — 시작 시 이미 초기화됨)
        if session is not None and message is not None:
            session.message = message

        # 모든 이벤트 성공 (Event 없음도 여기로) → 정상 응답
        response = EventExecutor._build_success_ruleEngine_eventExecutor(session)

        # 특정 이벤트가 처리된 턴은 응답 종류를 화면 이동 힌트로 표기
        #   (프론트 fsmRoute 가 라우팅에 사용)
        if any(e.type == Event.PAYMENT_CANCEL for e in events):
            # 결제 취소 → /cart 복귀 (음성 취소 대응)
            response.response_type = ResponseType.PAYMENT_CANCEL
        elif any(
            e.type in (
                Event.SHOW_CART,
                Event.REMOVE_CART_ITEM,
                Event.CLEAR_CART,
                Event.INCREASE_CART_ITEM,
                Event.DECREASE_CART_ITEM,
            )
            for e in events
        ):
            # 장바구니 조회/조작 → /cart 유지
            #   ("담아줘"와 상태가 같아 이벤트 종류로 구분 — 카트 조작 후
            #    음성 라우팅이 /order 로 튕기지 않도록)
            response.response_type = ResponseType.SHOW_CART

        await EventExecutor._touch_and_log_ruleEngine_eventExecutor(
            session, response.message,
        )
        return response

    # ------------------------------------------------------------------
    # 활동 시간 갱신(TTL) + AI 안내 문구 세션 로그 적재
    # ------------------------------------------------------------------
    @staticmethod
    async def _touch_and_log_ruleEngine_eventExecutor(
        session: Optional[Session],
        message: Optional[str],
    ) -> None:
        if session is None:
            return
        session.last_active_at = datetime.now()
        if message:
            session.last_message = message  # "다시 들려줘"(REPEAT) 재낭독용
            await SessionCrud.create_log_session_sessionCrud(
                session=session,
                speaker=SpeakerType.AI,
                message=message,
            )

    # ------------------------------------------------------------------
    # 정상 응답 조립
    # ------------------------------------------------------------------
    @staticmethod
    def _build_success_ruleEngine_eventExecutor(
        session: Session,
    ) -> SessionResponse:
        ended = session.session_status != SessionStatus.ACTIVE
        # 응답 종류: 결제 완료(COMPLETE) > 세션 종료 > 정상
        if session.fsm_state == FSMState.COMPLETE:
            response_type = ResponseType.PAYMENT_SUCCESS
        elif ended:
            response_type = ResponseType.SESSION_END
        else:
            response_type = ResponseType.NORMAL
        return SessionResponse(
            response_type=response_type,
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
        error_code = str(exc)
        message = get_error_message_error_message(error_code)
        # 필수 옵션 미충족 → 빠진 그룹을 지목해 구체 안내 (계산 불가 시 generic 유지)
        if error_code == "REQUIRED_OPTION_MISSING":
            specific = EventExecutor._required_missing_msg_ruleEngine_eventExecutor(session)
            if specific:
                message = specific
        return SessionResponse(
            response_type=ResponseType.ERROR,
            session_id=session.session_id if session else "",
            success=False,
            message=message,
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
            error_code=error_code,
            session_end=False,
        )

    # ------------------------------------------------------------------
    # 필수 옵션 미충족 시 빠진 그룹명 안내 문구 (없으면 None)
    # ------------------------------------------------------------------
    @staticmethod
    def _required_missing_msg_ruleEngine_eventExecutor(
        session: Optional[Session],
    ) -> Optional[str]:
        if session is None:
            return None
        menu = session.current_menu
        item = session.order_item
        if not isinstance(menu, dict) or item is None:
            return None
        selected = item.selected_options or {}
        missing = [
            g.get("og_name")
            for g in menu.get("option_groups", [])
            if g.get("og_required")
            and not selected.get(g.get("og_id"))
            and g.get("og_name")
        ]
        if not missing:
            return None
        return f"{', '.join(missing)}를 아직 안 고르셨어요. 먼저 골라주세요."