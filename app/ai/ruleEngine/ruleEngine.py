# app/ai/ruleEngine/ruleEngine.py
"""Rule Engine : ParseResult → List[FSMEvent] (E001~E016).

- Intent 1개 / 메뉴 1개 / 행동 1개.
- 옵션 값(ICE/라지/샷)은 메뉴 상세(DB)로 option_id 해석.
- 세션 문맥이 필요한 케이스(장바구니 항목 지정 등)는 ParseFailedError 로 위임.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.ruleEngine import rules
from app.fsm.event import Event, FSMEvent
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
            return RuleEngine._session_events(entities)
        if intent == "PAYMENT":
            return [FSMEvent(type=Event.START_PAYMENT)]
        if intent == "RECOMMEND":
            return RuleEngine._recommend_events(entities)
        if intent == "INFO":
            return RuleEngine._info_events(entities)
        if intent == "CART":
            return RuleEngine._cart_events(entities)
        if intent == "ORDER":
            return await RuleEngine._order_events(db, session, entities)

        raise rules.ParseFailedError(rules.MSG_PARSE_FAILED, reason="UNKNOWN_INTENT")

    # SESSION (E015, E016)
    @staticmethod
    def _session_events(entities: Dict[str, Any]) -> List[FSMEvent]:
        if entities.get("action") == "CANCEL":
            return [FSMEvent(type=Event.CANCEL_SESSION)]
        order_type = entities.get("order_type")
        if order_type:
            return [FSMEvent(type=Event.SELECT_ORDER_TYPE,
                             parameters={"order_type": order_type})]
        raise rules.ParseFailedError("매장에서 드시나요, 포장이신가요?", reason="NO_ORDER_TYPE")

    # RECOMMEND (E012, E013)
    @staticmethod
    def _recommend_events(entities: Dict[str, Any]) -> List[FSMEvent]:
        if entities.get("action") == "ACCEPT":
            return [FSMEvent(type=Event.ACCEPT_RECOMMENDATION)]
        return [FSMEvent(type=Event.REQUEST_RECOMMENDATION,
                         parameters={"condition": entities.get("condition", "")})]

    # INFO (E014)
    @staticmethod
    def _info_events(entities: Dict[str, Any]) -> List[FSMEvent]:
        menu_id = entities.get("menu")
        if menu_id is None:
            raise rules.ParseFailedError("어떤 메뉴가 궁금하세요?", reason="NO_MENU_FOR_INFO")
        return [FSMEvent(type=Event.REQUEST_MENU_INFO, parameters={"menu_id": menu_id})]

    # CART (E006~E010) : SHOW/CLEAR 만 규칙 확정
    @staticmethod
    def _cart_events(entities: Dict[str, Any]) -> List[FSMEvent]:
        action = entities.get("action")
        if action == "SHOW":
            return [FSMEvent(type=Event.SHOW_CART)]
        if action == "CLEAR":
            return [FSMEvent(type=Event.CLEAR_CART)]
        # REMOVE/INCREASE/DECREASE : 어떤 항목인지 세션 문맥 필요 → LLM/안내
        raise rules.ParseFailedError(
            "장바구니에서 어떤 메뉴를 말씀하시는지 알려주세요.", reason="CART_ITEM_UNRESOLVED")

    # ORDER (E001~E005) : 명세 순서 SELECT_MENU→SET_QUANTITY→REQUIRED→OPTIONAL
    @staticmethod
    async def _order_events(
        db: AsyncSession, session: Optional[Session], entities: Dict[str, Any],
    ) -> List[FSMEvent]:
        if entities.get("skip_optional"):
            return [FSMEvent(type=Event.SKIP_OPTIONAL_OPTION)]

        events: List[FSMEvent] = []
        menu_id = entities.get("menu")

        option_menu_id = menu_id
        if option_menu_id is None and session and session.order_item:
            option_menu_id = session.order_item.menu_id

        if menu_id is not None:
            events.append(FSMEvent(type=Event.SELECT_MENU, parameters={"menu_id": menu_id}))

        quantity = entities.get("quantity")
        if quantity is not None:
            events.append(FSMEvent(type=Event.SET_QUANTITY, parameters={"quantity": quantity}))

        required_values = entities.get("required_option", [])
        optional_values = entities.get("optional_option", [])

        if (required_values or optional_values):
            if option_menu_id is None:
                raise rules.ParseFailedError("먼저 메뉴를 선택해 주세요.", reason="NO_MENU_FOR_OPTION")
            menu = await Menus.get_single_menu_detail_services_menus(m_id=option_menu_id, db=db)
            for value in required_values:
                events.append(FSMEvent(
                    type=Event.SELECT_REQUIRED_OPTION,
                    parameters={"option_id": RuleEngine._resolve_option_id(menu, value, True)}))
            for value in optional_values:
                events.append(FSMEvent(
                    type=Event.SELECT_OPTIONAL_OPTION,
                    parameters={"option_id": RuleEngine._resolve_option_id(menu, value, False)}))

        if not events:
            raise rules.ParseFailedError("무엇을 주문하시겠어요?", reason="EMPTY_ORDER")
        return events

    @staticmethod
    def _resolve_option_id(menu: Dict[str, Any], value: str, required: bool) -> int:
        for group in menu["option_groups"]:
            if bool(group["og_required"]) != required:
                continue
            for option in group["options"]:
                if option["op_name"] == value:
                    return option["op_id"]
        raise rules.ParseFailedError(f"'{value}' 옵션을 찾을 수 없어요.", reason="OPTION_NOT_RESOLVED")