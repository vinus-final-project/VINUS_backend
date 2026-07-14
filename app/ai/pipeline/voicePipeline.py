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
from app.fsm.event import Event, FSMEvent
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
    ) -> Optional[SessionResponse]:
        """PCM → SessionResponse. 환각 필터로 폐기된 발화는 None 반환."""
        session_id = session.session_id if session else None

        # STT → RapidFuzz (폴백 시 LLM 에 넘길 보정 텍스트 확보)
        text = await WhisperService.transcribe_stt_whisper(pcm_bytes, sample_rate)

        # 환각 필터로 폐기된(빈) 발화 — 응답 없이 조용히 무시
        if not text.strip():
            return None

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

            # 화면 이동 발화 ("돌아가/메뉴 더") — FSM 이벤트 없이 SHOW_MENU 응답
            #   (상태 변화가 없어 프론트가 구분할 수 없으므로 응답 타입으로 전달)
            if parse_result.intent == "NAVIGATE":
                # 결제창 진행 ("카드로 할게요" / "현금으로")
                if parse_result.entities.get("target") == "PAY":
                    return await VoicePipeline._handle_pay_pipeline_voicePipeline(
                        db, session, parse_result.entities.get("method"),
                    )

                # 작성 중 주문이 있으면 취소하고 이동
                #   (터치 orderDetail '취소' 버튼과 동일 — "뒤로 갈래" 후
                #    다른 메뉴 선택 시 ORDER_ITEM_EXISTS 로 막히는 문제 방지)
                if session is not None and session.order_item is not None:
                    await EventExecutor.execute_ruleEngine_eventExecutor(
                        db=db,
                        session=session,
                        events=[FSMEvent(type=Event.CANCEL_ORDER_ITEM)],
                    )
                return VoicePipeline._build_navigate_pipeline_voicePipeline(
                    session,
                    parse_result.entities.get("category"),
                    parse_result.entities.get("page"),
                )

            # 합계 질문 ("총 얼마야/합계") — 상태 변경 없이 총액 안내
            if (
                parse_result.intent == "INFO"
                and parse_result.entities.get("type") == "TOTAL"
            ):
                if session is None or not session.cart:
                    return VoicePipeline._build_guidance_pipeline_voicePipeline(
                        session, "아직 담으신 메뉴가 없어요.",
                    )
                total = sum(
                    ci.unit_price * ci.quantity for ci in session.cart
                )
                return VoicePipeline._build_guidance_pipeline_voicePipeline(
                    session, f"현재 주문 금액은 {total:,}원입니다.",
                )

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
    # 결제수단 발화 처리 ("카드로 할게요")
    #   - 현금        → 미지원 안내
    #   - PAYMENT 상태 → SHOW_PAY (결제창으로)
    #   - ORDERING    → START_PAYMENT 실행 후 SHOW_PAY
    #                   (카트에서 "카드로 결제할게" 한 마디에 결제창 직행.
    #                    빈 카트/작성 중 주문 검증은 START_PAYMENT 이 처리)
    # ------------------------------------------------------------------
    @staticmethod
    async def _handle_pay_pipeline_voicePipeline(
        db: AsyncSession,
        session: Optional[Session],
        method: Optional[str],
    ) -> SessionResponse:
        if session is None:
            return VoicePipeline._build_guidance_pipeline_voicePipeline(
                session, "먼저 매장 또는 포장을 선택해 주세요.",
            )
        if method == "CASH":
            return VoicePipeline._build_guidance_pipeline_voicePipeline(
                session, "죄송해요, 카드 결제만 가능합니다.",
            )

        # 이미 결제방법 화면(PAYMENT) → 상태 그대로 결제창으로
        if session.fsm_state == FSMState.PAYMENT:
            response = VoicePipeline._build_guidance_pipeline_voicePipeline(
                session, "결제를 진행할게요.",
            )
            response.response_type = ResponseType.SHOW_PAY
            return response

        # 주문 중(ORDERING) → 결제 시작 후 결제창으로
        #   (빈 카트 EMPTY_CART / 작성 중 주문 ORDER_ITEM_EXISTS 는
        #    START_PAYMENT 검증이 에러 응답으로 안내)
        response = await EventExecutor.execute_ruleEngine_eventExecutor(
            db=db,
            session=session,
            events=[FSMEvent(type=Event.START_PAYMENT)],
            message="결제를 진행할게요.",
        )
        if response.success:
            response.response_type = ResponseType.SHOW_PAY
        return response

    # ------------------------------------------------------------------
    # 화면 이동 응답 : 전체 메뉴 화면 복귀 (상태 변경 없음)
    #   category 지정 시 프론트가 해당 카테고리 탭으로 전환
    #   세션 없으면(주문 시작 전) 안내 문구로 대체
    # ------------------------------------------------------------------
    @staticmethod
    def _build_navigate_pipeline_voicePipeline(
        session: Optional[Session],
        category: Optional[str] = None,
        page: Optional[str] = None,
    ) -> SessionResponse:
        if session is None:
            return VoicePipeline._build_guidance_pipeline_voicePipeline(
                session, "먼저 매장 또는 포장을 선택해 주세요.",
            )
        if page:
            message = (
                "다음 메뉴를 보여드릴게요." if page == "NEXT"
                else "이전 메뉴를 보여드릴게요."
            )
        elif category:
            message = f"{category} 메뉴를 보여드릴게요."
        else:
            # 확인 + 다음 행동 안내 컨벤션 (페이지 입장 안내 PageGuide 는
            # message 있는 전이를 skip 하므로, 이동 message 가 안내까지 담당)
            message = (
                "메뉴 화면으로 돌아갈게요. "
                "주문하실 메뉴를 말씀하시거나 화면에서 선택해주세요."
            )
        return SessionResponse(
            response_type=ResponseType.SHOW_MENU,
            session_id=session.session_id,
            success=True,
            message=message,
            category=category,
            page_move=page,
            fsm_state=session.fsm_state,
            order_type=session.order_type,
            order_item=session.order_item,
            current_menu=session.current_menu,
            cart=session.cart,
            total_price=sum(
                ci.unit_price * ci.quantity for ci in session.cart
            ),
            recommendation_list=session.recommendation_list,
            error_code=None,
            session_end=False,
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
            current_menu=session.current_menu if session else None,
            cart=session.cart if session else [],
            total_price=(
                sum(ci.unit_price * ci.quantity for ci in session.cart)
                if session else 0
            ),
            recommendation_list=session.recommendation_list if session else [],
            error_code=None,
            session_end=False,
        )