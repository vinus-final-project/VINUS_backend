"""AiPipeline : LLM 폴백 파이프라인 (Rule 처리 실패 시).

흐름
  Rule 실패 발화(query) + 세션 상태
    → aiClient.call_llm_aiClient          (AI 서버 호출)
    → LLMResponse(events, response)
    → FSMEvent 변환 (알 수 없는 타입은 건너뜀)
    → EventExecutor (message = LLM 안내 문구)
    → SessionResponse

AI 서버 장애/타임아웃 예외는 그대로 전파한다.
(호출부 voicePipeline 이 잡아서 규칙 안내 문구로 2차 폴백)
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.client.aiClient import call_llm_aiClient
from app.ai.ruleEngine import rules
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.fsm.event import Event, FSMEvent
from app.fsm.FSMstate import FSMState
from app.interface.dto.sessionResponse import ResponseType, SessionResponse
from app.memory.session.session import Session


class AiPipeline:

    # ------------------------------------------------------------------
    # LLM 폴백 실행 : query(보정 텍스트) → SessionResponse
    # ------------------------------------------------------------------
    @staticmethod
    async def run_llm_pipeline_aiPipeline(
        db: AsyncSession,
        session: Optional[Session],
        query: str,
        extra_allergies: Optional[list] = None,   # 일회성 제외("우유 없는 추천")
    ) -> SessionResponse:
        # 세션 알레르기 + 이번 요청 일회성 제외 병합
        _allergies = list(session.allergies) if session else []
        for _a in (extra_allergies or []):
            if _a not in _allergies:
                _allergies.append(_a)
        # 1) AI 서버 호출 (세션 상태 동봉 — LLM 문맥용)
        llm = await call_llm_aiClient(
            se_id=session.session_id if session else "",
            query=query,
            fsm_state=session.fsm_state.value if session else None,
            order_type=(
                session.order_type.value
                if session and session.order_type
                else None
            ),
            order_item=(
                session.order_item.model_dump()
                if session and session.order_item
                else None
            ),
            cart=(
                [ci.model_dump() for ci in session.cart]
                if session
                else None
            ),
            allergies=(_allergies or None),
        )

        # 2) LLMResponse.events → FSMEvent 변환
        #    (Event enum 에 없는 타입은 건너뜀 — LLM 환각 방어)
        events: list[FSMEvent] = []
        for e in llm.events:
            try:
                events.append(
                    FSMEvent(type=Event(e.type), parameters=e.parameters or {})
                )
            except ValueError:
                continue

        # 3) 정책 방어 : 한 번에 한 메뉴 — LLM 이 SELECT_MENU 를
        #    2개 이상 반환하면 실행하지 않고 안내 문구만 반환
        select_menu_count = sum(
            1 for ev in events if ev.type == Event.SELECT_MENU
        )
        if select_menu_count >= 2:
            return SessionResponse(
                response_type=ResponseType.NORMAL,
                session_id=session.session_id if session else "",
                success=True,
                message=rules.MSG_MULTIPLE_MENU,
                fsm_state=session.fsm_state if session else FSMState.INIT,
                order_type=session.order_type if session else None,
                order_item=session.order_item if session else None,
                cart=session.cart if session else [],
                recommendation_list=(
                    session.recommendation_list if session else []
                ),
            )

        # 4) 세션 없음 + 이벤트 없음 → 안내-only 응답
        #    (EventExecutor 는 세션 필요 — INIT 안내 문구만 반환)
        if session is None and not events:
            return SessionResponse(
                response_type=ResponseType.NORMAL,
                session_id="",
                success=True,
                message=llm.response,
                fsm_state=FSMState.INIT,
            )

        # 5) 실행 — 이벤트 없으면 LLM 안내 문구만 담긴 정상 응답
        return await EventExecutor.execute_ruleEngine_eventExecutor(
            db=db,
            session=session,
            events=events,
            message=llm.response,
        )
