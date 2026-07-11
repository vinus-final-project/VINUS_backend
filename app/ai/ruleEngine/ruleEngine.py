# app/ai/ruleEngine/ruleEngine.py
"""Rule Engine : ParseResult → List[FSMEvent] (현재 코드/데이터 기준).

- Intent 1개 / 메뉴 1개 / 행동 1개.
- 옵션 값 → op_id 해석 (메뉴 상세):
    · 필수  : op_name == 값        (ICE/HOT/레귤러/라지)
    · 샷    : 데이터가 '샷 N개 추가' 디스크리트 → count 를 op_name 으로 변환 (1건)
    · 시럽/휘핑 : 값이 이미 op_name (바닐라 시럽 등) → 누적이면 count 만큼 반복
- 옵션 이벤트: action ADD → SELECT_OPTION, REMOVE → DESELECT_OPTION
- 이벤트 순서: SELECT_MENU → 옵션 → SET_QUANTITY (set_quantity 는 상태 무관)
- 세션 문맥 필요한데 없는 경우(장바구니 항목 지정 등)는 ParseFailedError 로 위임.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ruleEngine import rules
from app.fsm.event import Event, FSMEvent
from app.fsm.FSMstate import FSMState
from app.interface.dto.parseResult import ParseResult
from app.memory.session.session import Session
from app.services.menus import Menus


class RuleEngine:

    @staticmethod
    async def build_events_ruleEngine_ruleEngine(
        db: AsyncSession,
        session: Optional[Session],
        parse_result: ParseResult,
    ) -> List[FSMEvent]:
        intent = parse_result.intent
        entities = parse_result.entities

        if intent == "SESSION":
            return RuleEngine._session_events_ruleEngine_ruleEngine(entities)
        if intent == "CANCEL":
            return RuleEngine._cancel_events_ruleEngine_ruleEngine(session)
        if intent == "PAYMENT":
            return [FSMEvent(type=Event.START_PAYMENT)]
        if intent == "RECOMMEND":
            return RuleEngine._recommend_events_ruleEngine_ruleEngine(entities)
        if intent == "INFO":
            return RuleEngine._info_events_ruleEngine_ruleEngine(session, entities)
        if intent == "CART":
            return RuleEngine._cart_events_ruleEngine_ruleEngine(session, entities)
        if intent == "ORDER":
            return await RuleEngine._order_events_ruleEngine_ruleEngine(db, session, entities)

        raise rules.ParseFailedError(rules.MSG_PARSE_FAILED, reason="UNKNOWN_INTENT")

    # ---------------- SESSION (order_type / cancel) ----------------
    @staticmethod
    def _session_events_ruleEngine_ruleEngine(e: Dict[str, Any]) -> List[FSMEvent]:
        if e.get("action") == "CANCEL":
            return [FSMEvent(type=Event.CANCEL_SESSION)]
        order_type = e.get("order_type")
        if order_type:
            return [FSMEvent(type=Event.SELECT_ORDER_TYPE, parameters={"order_type": order_type})]
        raise rules.ParseFailedError("매장에서 드시나요, 포장이신가요?", reason="NO_ORDER_TYPE")

    # ---------------- CANCEL (제네릭 "취소" — 세션 문맥 해석) ----------------
    #   PAYMENT 상태      → 결제 취소
    #   주문 작성 중       → 현재 주문 취소
    #   그 외             → 세션 취소
    @staticmethod
    def _cancel_events_ruleEngine_ruleEngine(
        session: Optional[Session],
    ) -> List[FSMEvent]:
        if session is None:
            raise rules.ParseFailedError(
                "취소할 주문이 없어요.", reason="NO_SESSION_FOR_CANCEL")
        if session.fsm_state == FSMState.PAYMENT:
            return [FSMEvent(type=Event.PAYMENT_CANCEL)]
        if session.order_item is not None:
            return [FSMEvent(type=Event.CANCEL_ORDER_ITEM)]
        return [FSMEvent(type=Event.CANCEL_SESSION)]

    # ---------------- RECOMMEND ----------------
    @staticmethod
    def _recommend_events_ruleEngine_ruleEngine(e: Dict[str, Any]) -> List[FSMEvent]:
        if e.get("action") == "ACCEPT":
            # index: "두 번째 걸로" 서수 선택 (기본 1 = 첫 번째)
            return [FSMEvent(type=Event.ACCEPT_RECOMMENDATION,
                             parameters={"index": e.get("index", 1)})]
        return [FSMEvent(type=Event.REQUEST_RECOMMENDATION,
                         parameters={"condition": e.get("condition", "")})]

    # ---------------- INFO ----------------
    @staticmethod
    def _info_events_ruleEngine_ruleEngine(
        session: Optional[Session], e: Dict[str, Any],
    ) -> List[FSMEvent]:
        menu_id = e.get("menu")
        # "이거 뭐야/이거 얼마야" — 메뉴 미지정 시 현재 작성 중 메뉴로 폴백
        if menu_id is None and session is not None and session.current_menu:
            menu_id = session.current_menu.get("m_id")
        if menu_id is None:
            raise rules.ParseFailedError("어떤 메뉴가 궁금하세요?", reason="NO_MENU_FOR_INFO")
        return [FSMEvent(type=Event.REQUEST_MENU_INFO, parameters={"menu_id": menu_id})]

    # ---------------- CART ----------------
    @staticmethod
    def _cart_events_ruleEngine_ruleEngine(
        session: Optional[Session], e: Dict[str, Any],
    ) -> List[FSMEvent]:
        action = e.get("action")
        if action == "SHOW":
            return [FSMEvent(type=Event.SHOW_CART)]
        if action == "CLEAR":
            return [FSMEvent(type=Event.CLEAR_CART)]

        # REMOVE/INCREASE/DECREASE — cart_item 해석 필요
        menu_id = e.get("menu")

        # "아메리카노 취소/빼줘" 인데 그 메뉴가 지금 작성 중인 주문이면
        # 카트가 아니라 현재 주문 취소로 해석
        if (
            action == "REMOVE"
            and menu_id is not None
            and session is not None
            and session.order_item is not None
            and session.order_item.menu_id == menu_id
        ):
            return [FSMEvent(type=Event.CANCEL_ORDER_ITEM)]

        # "아메리카노 하나 추가" 인데 그 메뉴가 카트에 없으면 신규 주문으로 해석
        if (
            action == "INCREASE"
            and menu_id is not None
            and (
                session is None
                or not any(ci.menu_id == menu_id for ci in session.cart)
            )
        ):
            return [FSMEvent(type=Event.SELECT_MENU, parameters={"menu_id": menu_id})]

        # 메뉴 지정 없는 "추가/빼줘" 인데 주문 작성 중이면
        # 카트가 아니라 현재 주문(order_item) 수량 증감으로 해석
        #   ("옵션 고르는 중 '두 개 추가해줘'" = 잔 수 변경 의도)
        if (
            menu_id is None
            and session is not None
            and session.order_item is not None
            and action in ("INCREASE", "DECREASE")
        ):
            step = max(1, int(e.get("count", 1) or 1))
            base = session.order_item.quantity
            new_qty = base + step if action == "INCREASE" else max(1, base - step)
            return [FSMEvent(type=Event.SET_QUANTITY,
                             parameters={"quantity": new_qty})]

        cart_item_id = RuleEngine._resolve_cart_item_ruleEngine_ruleEngine(
            session, menu_id,
        )
        event_map = {
            "REMOVE": Event.REMOVE_CART_ITEM,
            "INCREASE": Event.INCREASE_CART_ITEM,
            "DECREASE": Event.DECREASE_CART_ITEM,
        }
        ev = event_map.get(action)
        if ev is None:
            raise rules.ParseFailedError(
                rules.MSG_PARSE_FAILED, reason="UNKNOWN_CART_ACTION")

        # 개수 반복 ("두 개 빼줘" → DECREASE ×2)
        count = max(1, int(e.get("count", 1) or 1))
        if action == "DECREASE" and session is not None:
            # 보유 수량으로 상한 — 초과 감소 시 항목 삭제 후 에러 방지
            item = next(
                (ci for ci in session.cart if ci.cart_item_id == cart_item_id),
                None,
            )
            if item is not None:
                count = min(count, item.quantity)
        if action == "REMOVE":
            count = 1  # 항목 삭제는 1회면 충분

        return [
            FSMEvent(type=ev, parameters={"cart_item_id": cart_item_id})
            for _ in range(count)
        ]

    # cart_item_id 해석 : 메뉴 지정 → 해당 메뉴 항목(복수면 마지막 담은 것),
    #                    미지정 → 카트에 1건이면 그것, 그 외 재질문
    @staticmethod
    def _resolve_cart_item_ruleEngine_ruleEngine(
        session: Optional[Session], menu_id: Optional[int],
    ) -> int:
        if session is None or not session.cart:
            raise rules.ParseFailedError(
                "장바구니가 비어 있어요.", reason="EMPTY_CART")
        if menu_id is not None:
            matches = [ci for ci in session.cart if ci.menu_id == menu_id]
            if not matches:
                raise rules.ParseFailedError(
                    "장바구니에 그 메뉴가 없어요.", reason="CART_ITEM_NOT_FOUND")
            return matches[-1].cart_item_id
        if len(session.cart) == 1:
            return session.cart[0].cart_item_id
        raise rules.ParseFailedError(
            "장바구니에서 어떤 메뉴를 말씀하시는지 알려주세요.",
            reason="CART_ITEM_UNRESOLVED")

    # ---------------- ORDER ----------------
    @staticmethod
    async def _order_events_ruleEngine_ruleEngine(
        db: AsyncSession, session: Optional[Session], e: Dict[str, Any],
    ) -> List[FSMEvent]:
        if e.get("skip_optional"):
            return [FSMEvent(type=Event.SKIP_OPTIONAL_OPTION)]

        events: List[FSMEvent] = []
        menu_id = e.get("menu")

        # 1) SELECT_MENU
        if menu_id is not None:
            events.append(FSMEvent(type=Event.SELECT_MENU, parameters={"menu_id": menu_id}))

        required = e.get("required_option", [])
        optional = e.get("optional_option", [])
        if required or optional:
            menu = await RuleEngine._load_menu_ruleEngine_ruleEngine(db, session, menu_id)

            # 2) 단일선택 옵션 → SELECT_OPTION
            #    메뉴에 없는 값은 조용히 무시 — "아이스 딸기 스무디"처럼
            #    (스무디엔 온도 그룹 없음) 원래 그 속성인 메뉴 대응
            for value in required:
                op_id = RuleEngine._find_op_id_ruleEngine_ruleEngine(menu, value)
                if op_id is None:
                    continue
                events.append(FSMEvent(type=Event.SELECT_OPTION, parameters={"option_id": op_id}))

            # 3) 선택 옵션 → SELECT_OPTION / DESELECT_OPTION
            for item in optional:
                events.extend(
                    RuleEngine._optional_events_ruleEngine_ruleEngine(
                        menu, item, session,
                    )
                )

        # 4) SET_QUANTITY (순서 무관)
        quantity = e.get("quantity")
        if quantity is not None:
            events.append(FSMEvent(type=Event.SET_QUANTITY, parameters={"quantity": quantity}))

        if not events:
            raise rules.ParseFailedError("무엇을 주문하시겠어요?", reason="EMPTY_ORDER")
        return events

    # 옵션 해석 기준 메뉴: 이번 발화 메뉴(DB) or 현재 작성 중 메뉴(current_menu 스냅샷)
    @staticmethod
    async def _load_menu_ruleEngine_ruleEngine(
        db: AsyncSession, session: Optional[Session], menu_id: Optional[int],
    ) -> Dict[str, Any]:
        if menu_id is not None:
            return await Menus.get_single_menu_detail_services_menus(m_id=menu_id, db=db)
        if session is not None and session.current_menu is not None:
            return session.current_menu
        raise rules.ParseFailedError("먼저 메뉴를 선택해 주세요.", reason="NO_MENU_FOR_OPTION")

    # op_name == value 인 op_id (없으면 None)
    @staticmethod
    def _find_op_id_ruleEngine_ruleEngine(menu: Dict[str, Any], op_name: str) -> Optional[int]:
        for group in menu["option_groups"]:
            for option in group["options"]:
                if option["op_name"] == op_name:
                    return option["op_id"]
        return None

    # 선택옵션 1건 → 이벤트 목록
    @staticmethod
    def _optional_events_ruleEngine_ruleEngine(
        menu: Dict[str, Any],
        item: Dict[str, Any],
        session: Optional[Session] = None,
    ) -> List[FSMEvent]:
        value = item["value"]
        count = item.get("count", 1)
        action = item.get("action", "ADD")

        # 전량 제거 ("샷 전부 빼줘") — 현재 선택된 개수만큼 DESELECT
        if action == "REMOVE_ALL":
            return RuleEngine._remove_all_option_events_ruleEngine_ruleEngine(
                menu, value, session,
            )

        ev = Event.DESELECT_OPTION if action == "REMOVE" else Event.SELECT_OPTION

        # 샷: 데이터 형태에 따라 두 가지 지원
        #   ① 디스크리트형 '샷 N개 추가' → 해당 이름 1건
        #   ② 누적형 '샷 추가' (현재 seed) → count 만큼 반복 (+/- 동일)
        if value == "샷":
            n = count if count >= 1 else 1
            # ① 디스크리트형 우선
            discrete_id = RuleEngine._find_op_id_ruleEngine_ruleEngine(
                menu, f"샷 {2 if n >= 2 else 1}개 추가",
            )
            if discrete_id is not None:
                return [FSMEvent(type=ev, parameters={"option_id": discrete_id})]
            # ② 누적형 — '샷'으로 시작하는 옵션 탐색
            shot_id = None
            for group in menu["option_groups"]:
                for option in group["options"]:
                    if option["op_name"].startswith("샷"):
                        shot_id = option["op_id"]
                        break
                if shot_id is not None:
                    break
            if shot_id is None:
                raise rules.ParseFailedError("샷 옵션을 찾을 수 없어요.", reason="OPTION_NOT_FOUND")
            return [FSMEvent(type=ev, parameters={"option_id": shot_id}) for _ in range(n)]

        # 시럽 종류 불명확 → 문맥/LLM 필요
        if value == "시럽":
            raise rules.ParseFailedError("어떤 시럽을 추가할까요?", reason="SYRUP_UNSPECIFIED")

        # 시럽 종류/휘핑 등: value 가 이미 op_name → 누적이면 count 만큼 반복
        op_id = RuleEngine._find_op_id_ruleEngine_ruleEngine(menu, value)
        if op_id is None:
            raise rules.ParseFailedError(f"'{value}' 옵션을 찾을 수 없어요.", reason="OPTION_NOT_FOUND")
        times = count if count >= 1 else 1
        return [FSMEvent(type=ev, parameters={"option_id": op_id}) for _ in range(times)]

    # 전량 제거: value 에 해당하는 op 가 현재 주문에 선택된 개수만큼 DESELECT 생성
    #   (샷은 '샷 N개 추가' 디스크리트 옵션이라 이름 접두 매칭)
    @staticmethod
    def _remove_all_option_events_ruleEngine_ruleEngine(
        menu: Dict[str, Any],
        value: str,
        session: Optional[Session],
    ) -> List[FSMEvent]:
        if session is None or session.order_item is None:
            raise rules.ParseFailedError(
                "빼실 옵션이 있는 주문이 없어요.", reason="NO_ORDER_ITEM_FOR_REMOVE")

        # value 에 해당하는 op_id 후보 수집
        candidates: set[int] = set()
        for group in menu["option_groups"]:
            for option in group["options"]:
                name = option["op_name"]
                if (value == "샷" and name.startswith("샷")) or name == value:
                    candidates.add(option["op_id"])
        if not candidates:
            raise rules.ParseFailedError(
                f"'{value}' 옵션을 찾을 수 없어요.", reason="OPTION_NOT_FOUND")

        # 현재 선택된 해당 옵션들을 전부 DESELECT (개수만큼 반복)
        events: List[FSMEvent] = []
        for op_ids in session.order_item.selected_options.values():
            for op_id in op_ids:
                if op_id in candidates:
                    events.append(
                        FSMEvent(type=Event.DESELECT_OPTION,
                                 parameters={"option_id": op_id})
                    )
        if not events:
            raise rules.ParseFailedError(
                f"선택하신 '{value}' 옵션이 없어요.", reason="OPTION_NOT_SELECTED")
        return events