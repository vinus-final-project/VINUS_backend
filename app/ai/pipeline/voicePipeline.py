# app/ai/pipeline/voicePipeline.py
"""VoicePipeline : 텍스트 단계 오케스트레이션.

NormalizeResult → RuleParser → RuleEngine → EventExecutor → SessionResponse.
규칙 확정 불가(RuleParseError)는 안내 문구(message)를 담은 SessionResponse 로 즉시 반환.
(WebSocket 명세서 8~10단계의 '안내' 경로. RAG/LLM 대체 경로는 추후 배선.)
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ruleEngine import rules
from app.ai.ruleEngine.ruleParser import RuleParser
from app.ai.ruleEngine.ruleEngine import RuleEngine
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.fsm.FSMstate import FSMState
from app.interface.dto.normalizeResult import NormalizeResult
from app.interface.dto.sessionResponse import ResponseType, SessionResponse
from app.memory.session.session import Session


class VoicePipeline:

    @staticmethod
    async def process_pipeline_voicePipeline(
        db: AsyncSession,
        session: Optional[Session],
        normalize_result: NormalizeResult,
    ) -> SessionResponse:
        try:
            parse_result = RuleParser.parse_ruleEngine_ruleParser(normalize_result)
            events = await RuleEngine.build_events_ruleEngine_ruleEngine(
                db=db, session=session, parse_result=parse_result,
            )
        except rules.RuleParseError as exc:
            # 다중 메뉴/해석 불가 → 안내 문구 응답 (여기가 "한 메뉴씩" TTS 지점)
            return VoicePipeline._build_guidance_pipeline_voicePipeline(session, exc.message)

        return await EventExecutor.execute_ruleEngine_eventExecutor(
            db=db, session=session, events=events,
        )

    @staticmethod
    def _build_guidance_pipeline_voicePipeline(
        session: Optional[Session], message: str,
    ) -> SessionResponse:
        """규칙 실패 시 재안내 응답 (상태 변경 없음)."""
        return SessionResponse(
            response_type=ResponseType.NORMAL,
            session_id=session.session_id if session else "",
            success=True,
            message=message,
            fsm_state=session.fsm_state if session else FSMState.INIT,
            order_type=session.order_type if session else None,
            order_item=session.order_item if session else None,
            cart=session.cart if session else [],
            recommendation_list=session.recommendation_list if session else [],
            error_code=None,
            session_end=False,
        )