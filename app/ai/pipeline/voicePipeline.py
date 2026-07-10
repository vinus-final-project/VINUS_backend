# app/ai/pipeline/voicePipeline.py
"""VoicePipeline : 음성/텍스트 → 처리 결과 오케스트레이션.

흐름
  PCM(+session_id)
    → WhisperService.transcribe_stt_whisper       (STT)       bytes → str
    → Normalizer.normalize_rapidfuzz_normalizer    (RapidFuzz) str → str
    → NormalizeResult(session_id, text)            (래핑)
    → RuleParser.parse_ruleEngine_ruleParser       (Parser)    → ParseResult
    → RuleEngine.build_events                      (Engine)    → List[FSMEvent]
    → EventExecutor.execute                        (Executor)  → SessionResponse

규칙 확정 불가(RuleParseError: 다중 메뉴/해석 불가)는
1차: AiPipeline(LLM 폴백) 시도,
2차: AI 서버 장애 시 규칙 안내 문구 SessionResponse 로 반환한다.
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.stt.whisperService import WhisperService
from app.ai.rapidfuzz.normalizer import Normalizer
from app.ai.ruleEngine import rules
from app.ai.ruleEngine.ruleParser import RuleParser
from app.ai.ruleEngine.ruleEngine import RuleEngine
from app.ai.ruleEngine.eventExecutor import EventExecutor
from app.ai.pipeline.aiPipeline import AiPipeline
from app.fsm.FSMstate import FSMState
from app.interface.dto.normalizeResult import NormalizeResult
from app.interface.dto.parseResult import ParseResult
from app.interface.dto.sessionResponse import ResponseType, SessionResponse
from app.memory.session.enums import SpeakerType
from app.memory.session.session import Session
from app.memory.session.sessionCrud import SessionCrud


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
    #   - RuleParseError(다중 메뉴/옵션 불명확 등) → 안내 문구 응답 (상태 변경 없음)
    #   - 성공 → RuleEngine(이벤트 생성) → EventExecutor(FIFO 실행)
    # ------------------------------------------------------------------
    @staticmethod
    async def process_pipeline_voicePipeline(
        db: AsyncSession,
        session: Optional[Session],
        pcm_bytes: bytes,
        sample_rate: int = 16000,
    ) -> SessionResponse:
        session_id = session.session_id if session else None

        # STT → RapidFuzz (폴백 시 LLM 에 넘길 보정 텍스트 확보)
        text = await WhisperService.transcribe_stt_whisper(pcm_bytes, sample_rate)
        normalized = await Normalizer.normalize_rapidfuzz_normalizer(text)

        # USER 발화 세션 로그 적재 (세션 생성 전 첫 발화는 제외)
        if session is not None and normalized:
            await SessionCrud.create_log_session_sessionCrud(
                session=session,
                speaker=SpeakerType.USER,
                message=normalized,
            )

        try:
            nr = NormalizeResult(session_id=session_id, text=normalized)
            parse_result = RuleParser.parse_ruleEngine_ruleParser(nr)
            # RuleEngine : ParseResult → List[FSMEvent]
            #   (옵션 op_id 해석 실패 등도 RuleParseError 로 폴백 처리)
            events = await RuleEngine.build_events_ruleEngine_ruleEngine(
                db=db, session=session, parse_result=parse_result,
            )
        except rules.MultipleMenuError as exc:
            # 정책 위반 (한 번에 한 메뉴) — LLM 폴백 대상 아님, 바로 안내
            return VoicePipeline._build_guidance_pipeline_voicePipeline(
                session, exc.message,
            )
        except rules.RuleParseError as exc:
            # 1차 폴백 : LLM (AI 서버) — 규칙으로 해석 못 한 발화 처리
            #   (능력 부족만 폴백 — 정책 위반은 위에서 차단)
            try:
                return await AiPipeline.run_llm_pipeline_aiPipeline(
                    db=db, session=session, query=normalized,
                )
            except Exception:
                # 2차 폴백 : AI 서버 장애/타임아웃 → 규칙 안내 문구 (상태 변경 없음)
                return VoicePipeline._build_guidance_pipeline_voicePipeline(
                    session, exc.message,
                )

        # EventExecutor : FIFO 실행 → SessionResponse (실패 시 내부에서 에러 응답 조립)
        return await EventExecutor.execute_ruleEngine_eventExecutor(
            db=db, session=session, events=events,
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