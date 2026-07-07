# app/ai/pipeline/voicePipeline.py
"""VoicePipeline : 음성/텍스트 → 처리 결과 오케스트레이션.

흐름
  PCM(+session_id)
    → WhisperService.transcribe_stt_whisper       (STT)       bytes → str
    → Normalizer.normalize_rapidfuzz_normalizer    (RapidFuzz) str → str
    → NormalizeResult(session_id, text)            (래핑)
    → RuleParser.parse_ruleEngine_ruleParser       (Parser)    → ParseResult
    → RuleEngine → EventExecutor → SessionResponse (미배선: ruleEngine.py 비어있음)

규칙 확정 불가(RuleParseError: 다중 메뉴/해석 불가)는
안내 문구(message)를 담은 SessionResponse 로 반환한다.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.stt.whisperService import WhisperService
from app.ai.rapidfuzz.normalizer import Normalizer
from app.ai.ruleEngine import rules
from app.ai.ruleEngine.ruleParser import RuleParser
from app.fsm.FSMstate import FSMState
from app.interface.dto.normalizeResult import NormalizeResult
from app.interface.dto.parseResult import ParseResult
from app.interface.dto.sessionResponse import ResponseType, SessionResponse
from app.memory.session.session import Session


class VoicePipeline:

    # ------------------------------------------------------------------
    # STT → RapidFuzz → Parser : PCM → ParseResult
    # ------------------------------------------------------------------
    @staticmethod
    async def transcribe_and_parse_pipeline_voicePipeline(
        pcm_bytes: bytes,
        session_id: Optional[str] = None,
        sample_rate: int = 16000,
    ) -> ParseResult:
        text = await WhisperService.transcribe_stt_whisper(pcm_bytes, sample_rate)
        return await VoicePipeline.parse_text_pipeline_voicePipeline(text, session_id)

    # ------------------------------------------------------------------
    # RapidFuzz → Parser : text → ParseResult
    #   (STT 없이 텍스트로 바로 테스트할 때 사용)
    # ------------------------------------------------------------------
    @staticmethod
    async def parse_text_pipeline_voicePipeline(
        text: str,
        session_id: Optional[str] = None,
    ) -> ParseResult:
        normalized = await Normalizer.normalize_rapidfuzz_normalizer(text)
        nr = NormalizeResult(session_id=session_id, text=normalized)
        return RuleParser.parse_ruleEngine_ruleParser(nr)

    # ------------------------------------------------------------------
    # 전체 처리 : PCM → SessionResponse
    #   - RuleParseError(다중 메뉴 등) → 안내 문구 응답
    #   - 성공 → RuleEngine → EventExecutor (※ RuleEngine 미구현으로 미배선)
    # ------------------------------------------------------------------
    @staticmethod
    async def process_pipeline_voicePipeline(
        db: AsyncSession,
        session: Optional[Session],
        pcm_bytes: bytes,
        sample_rate: int = 16000,
    ) -> SessionResponse:
        session_id = session.session_id if session else None
        try:
            parse_result = await VoicePipeline.transcribe_and_parse_pipeline_voicePipeline(
                pcm_bytes, session_id, sample_rate,
            )
        except rules.RuleParseError as exc:
            # 다중 메뉴/해석 불가 → 안내 문구 SessionResponse ("한 번에 한 메뉴씩..." 등)
            return VoicePipeline._build_guidance_pipeline_voicePipeline(session, exc.message)

        # ---- 여기부터 다음 단계 (RuleEngine 채워지면 배선) ----
        # events = await RuleEngine.build_events_ruleEngine_ruleEngine(db, session, parse_result)
        # return await EventExecutor.execute_ruleEngine_eventExecutor(db, session, events)
        raise NotImplementedError(
            f"RuleEngine 미구현으로 미배선입니다. "
            f"parse_result: intent={parse_result.intent}, entities={parse_result.entities}"
        )

    # ------------------------------------------------------------------
    # 규칙 실패 시 재안내 응답 (상태 변경 없음)
    # ------------------------------------------------------------------
    @staticmethod
    def _build_guidance_pipeline_voicePipeline(
        session: Optional[Session],
        message: str,
    ) -> SessionResponse:
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