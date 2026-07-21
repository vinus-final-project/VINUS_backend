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
from app.services.menus import Menus


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

            # 메뉴 낭독 이어듣기 컨텍스트 정리 — 낭독 요청/"다음"/"이전" 외의
            # 발화가 오면 초기화 (이후 "다음/이전"은 조용한 페이지 넘김으로 복귀)
            if session is not None and session.menu_browse is not None:
                is_browse_page = (
                    parse_result.intent == "NAVIGATE"
                    and parse_result.entities.get("page") in ("NEXT", "PREV")
                )
                is_menu_list = (
                    parse_result.intent == "INFO"
                    and parse_result.entities.get("type") == "MENU_LIST"
                )
                if not is_browse_page and not is_menu_list:
                    session.menu_browse = None

            # 메뉴 낭독 ("메뉴 알려줘"/"커피 뭐 있어") — 음성 메뉴판
            #   (상태 변경 없음 — 화면을 볼 수 없는 사용자용)
            if (
                parse_result.intent == "INFO"
                and parse_result.entities.get("type") == "MENU_LIST"
            ):
                return await VoicePipeline._handle_menu_list_pipeline_voicePipeline(
                    db, session, parse_result.entities.get("category"),
                )

            # 화면 이동 발화 ("돌아가/메뉴 더") — FSM 이벤트 없이 SHOW_MENU 응답
            #   (상태 변화가 없어 프론트가 구분할 수 없으므로 응답 타입으로 전달)
            if parse_result.intent == "NAVIGATE":
                # 결제창 진행 ("카드로 할게요" / "현금으로")
                if parse_result.entities.get("target") == "PAY":
                    return await VoicePipeline._handle_pay_pipeline_voicePipeline(
                        db, session, parse_result.entities.get("method"),
                    )

                # 메뉴 낭독 진행 중의 "다음/이전" — 화면 페이지를 넘기면서
                # 새 페이지 메뉴를 함께 낭독 (페이지 동기화 낭독)
                if (
                    session is not None
                    and session.menu_browse is not None
                    and parse_result.entities.get("page") in ("NEXT", "PREV")
                ):
                    step = 1 if parse_result.entities.get("page") == "NEXT" else -1
                    return await VoicePipeline._handle_menu_list_pipeline_voicePipeline(
                        db,
                        session,
                        session.menu_browse.get("category"),
                        page=int(session.menu_browse.get("page", 0)) + step,
                    )

                # 작성 중 주문이 있으면 이동 차단 — 취소/주문 완료로만 이탈
                #   (기존 자동 취소 정책 폐기: 오인식 한 번에 고르던 옵션이
                #    날아가는 사고 방지. RuleEngine 카트/메뉴 차단과 동일 문구)
                if session is not None and session.order_item is not None:
                    return VoicePipeline._build_guidance_pipeline_voicePipeline(
                        session,
                        RuleEngine.composing_block_msg_ruleEngine_ruleEngine(session),
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

            # 음성 에코 요약 (ORDER) — "아메리카노 세잔"처럼 한 발화가
            # 이벤트 여러 개로 번역되면 컨트롤러 에코가 마지막 것만 남아
            # 발화 전체 요약으로 덮는다 (None 이면 컨트롤러 에코 유지)
            echo = None
            if parse_result.intent == "ORDER":
                echo = await RuleEngine.build_order_echo_ruleEngine_ruleEngine(
                    db=db, session=session, e=parse_result.entities,
                )
        except (rules.MultipleMenuError, rules.PolicyBlockedError) as exc:
            # 정책 위반 (한 번에 한 메뉴 / 작성 중 이탈 차단)
            #   — LLM 폴백 대상 아님, 바로 안내
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
            db=db, session=session, events=events, message=echo,
        )

    # ------------------------------------------------------------------
    # 메뉴 낭독 ("메뉴 알려줘" / "커피 뭐 있어") — 화면 페이지 동기화 낭독
    #   - 카테고리 미지정: 카테고리 목록만 안내 (화면 이동 없음)
    #   - 카테고리 지정: 화면을 그 카테고리 탭 + 해당 페이지로 전환하면서
    #     그 페이지에 보이는 메뉴(6개)를 낭독 — "보이는 것 = 들리는 것"
    #   - 낭독 진행 중 "다음/이전": 화면 페이지 이동 + 새 페이지 낭독
    #     (진행 상태는 session.menu_browse = {"category", "page"})
    #   - 터치 페이지 넘김에는 낭독을 붙이지 않는다 (음성 요청에만 음성 응답).
    #     터치로 페이지가 어긋나도 다음 발화의 page_index 가 화면을 재동기화.
    #   FSM 상태 변경 없음 (조회 전용 — 작성 중 주문 차단 정책과 무관)
    # ------------------------------------------------------------------
    MENU_PAGE_SIZE = 6  # ⚠ 프론트 order 페이지 PAGE_SIZE 와 반드시 동일하게 유지

    @staticmethod
    async def _handle_menu_list_pipeline_voicePipeline(
        db: AsyncSession,
        session: Optional[Session],
        category: Optional[str],
        page: Optional[int] = None,
    ) -> SessionResponse:
        if session is None:
            return VoicePipeline._build_guidance_pipeline_voicePipeline(
                session, "먼저 매장 또는 포장을 선택해 주세요.",
            )

        boot = await Menus.get_bootstrap_services_menus(db)
        speak = lambda name: name.replace("/", ", ")  # "커피/라떼" TTS 낭독용

        # 카테고리 미지정 → 카테고리 목록 안내 (화면 이동 없음)
        if not category:
            session.menu_browse = None
            names = ", ".join(speak(c["c_name"]) for c in boot["categories"])
            return VoicePipeline._build_guidance_pipeline_voicePipeline(
                session,
                f"{names} 종류가 있어요. 어떤 종류를 알려드릴까요?",
            )

        c_id = next(
            (c["c_id"] for c in boot["categories"] if c["c_name"] == category),
            None,
        )
        if c_id is None:
            session.menu_browse = None
            return VoicePipeline._build_guidance_pipeline_voicePipeline(
                session, "그 종류는 찾지 못했어요. 다시 말씀해주세요.",
            )

        items = [m["m_name"] for m in boot["menus"] if m["c_id"] == c_id]
        size = VoicePipeline.MENU_PAGE_SIZE
        total_pages = max(1, -(-len(items) // size))  # ceil

        # 대상 페이지 — 새 낭독은 1페이지, "다음/이전"은 ±1 (경계 클램프)
        target = 0 if page is None else page
        boundary_note = ""
        if target < 0:
            target = 0
            boundary_note = "첫 페이지예요. "
        elif target >= total_pages:
            target = total_pages - 1
            boundary_note = "마지막 페이지예요. "

        chunk = items[target * size:(target + 1) * size]
        listed = ", ".join(chunk)

        # 진행 상태 저장 — 다른 발화가 오면 process() 초입에서 해제됨
        session.menu_browse = {"category": category, "page": target}

        head = (
            f"{speak(category)} 메뉴는 모두 {len(items)}개, {total_pages}페이지예요. "
            if page is None else f"{target + 1}페이지. "
        )
        tail = (
            "주문하실 메뉴를 말씀해주세요."
            if target == total_pages - 1
            else "계속 보시려면 다음, 주문하시려면 메뉴 이름을 말씀해주세요."
        )
        message = f"{boundary_note}{head}{listed}. {tail}"

        # 화면 동기화 응답 — SHOW_MENU 로 해당 카테고리 탭 + 절대 페이지 지정
        return SessionResponse(
            response_type=ResponseType.SHOW_MENU,
            session_id=session.session_id,
            success=True,
            message=message,
            category=category,
            page_index=target,
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