# app/ai/ruleEngine/ruleParser.py
"""Rule Parser : NormalizeResult → ParseResult.

시스템 정책: 메뉴 1개 / Intent 1개 / 행동 1개.
다중 메뉴·해석 불가는 예외로 위임 → 안내 문구 또는 LLM.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from app.interface.dto.normalizeResult import NormalizeResult
from app.interface.dto.parseResult import ParseResult
from app.ai.ruleEngine import rules


class RuleParser:

    @staticmethod
    def parse_ruleEngine_ruleParser(
        normalize_result: NormalizeResult,
    ) -> ParseResult:
        session_id = normalize_result.session_id
        text = (normalize_result.text or "").strip()

        if not text:
            raise rules.ParseFailedError(rules.MSG_PARSE_FAILED, reason="EMPTY_TEXT")

        # 1) 메뉴 감지 — 다중 메뉴 차단
        menu_ids = RuleParser._find_menus_ruleEngine_ruleParser(text)
        if len(menu_ids) >= 2:
            raise rules.MultipleMenuError(rules.MSG_MULTIPLE_MENU, reason="MULTIPLE_MENU")

        # 2) Intent + Entity
        intent, entities = RuleParser._resolve_intent_ruleEngine_ruleParser(text, menu_ids)
        return ParseResult(
            session_id=session_id, intent=intent, entities=entities, source="RULE",
        )

    # 메뉴 감지 : 긴 이름 우선 + 스팬 제외
    @staticmethod
    def _find_menus_ruleEngine_ruleParser(text: str) -> List[int]:
        matched: List[Tuple[int, int]] = []
        occupied: List[Tuple[int, int]] = []
        for name in rules.MENU_NAMES_BY_LEN:
            start = 0
            while True:
                idx = text.find(name, start)
                if idx == -1:
                    break
                end = idx + len(name)
                if not any(idx < oe and os_ < end for (os_, oe) in occupied):
                    matched.append((idx, rules.MENU_DICTIONARY[name]))
                    occupied.append((idx, end))
                start = idx + 1
        matched.sort(key=lambda x: x[0])
        return [m_id for (_, m_id) in matched]

    # Intent 판별 (구체적 → 일반)
    @staticmethod
    def _resolve_intent_ruleEngine_ruleParser(
        text: str, menu_ids: List[int],
    ) -> Tuple[str, Dict[str, Any]]:

        if not menu_ids and any(k in text for k in rules.SESSION_CANCEL_KEYWORDS):
            return "SESSION", {"action": "CANCEL"}
        for keyword, order_type in rules.ORDER_TYPE_KEYWORDS.items():
            if keyword in text:
                return "SESSION", {"order_type": order_type}

        if any(k in text for k in rules.PAYMENT_KEYWORDS):
            return "PAYMENT", {"action": "START"}

        if not menu_ids:
            if any(k in text for k in rules.CART_CLEAR_KEYWORDS):
                return "CART", {"action": "CLEAR"}
            if any(k in text for k in rules.CART_INCREASE_KEYWORDS):
                return "CART", {"action": "INCREASE"}
            if any(k in text for k in rules.CART_DECREASE_KEYWORDS):
                return "CART", {"action": "DECREASE"}
            if any(k in text for k in rules.CART_REMOVE_KEYWORDS):
                return "CART", {"action": "REMOVE"}
            if any(k in text for k in rules.CART_SHOW_KEYWORDS):
                return "CART", {"action": "SHOW"}

        if any(k in text for k in rules.RECOMMEND_ACCEPT_KEYWORDS):
            return "RECOMMEND", {"action": "ACCEPT"}
        if any(k in text for k in rules.RECOMMEND_REQUEST_KEYWORDS):
            return "RECOMMEND", {"action": "REQUEST", "condition": text}

        if any(k in text for k in rules.INFO_KEYWORDS):
            entities: Dict[str, Any] = {"type": "MENU"}
            if menu_ids:
                entities["menu"] = menu_ids[0]
            return "INFO", entities

        if not menu_ids and any(k in text for k in rules.SKIP_OPTIONAL_KEYWORDS):
            return "ORDER", {"skip_optional": True}

        if menu_ids:
            entities = {"menu": menu_ids[0]}
            q = RuleParser._extract_quantity_ruleEngine_ruleParser(text)
            if q is not None:
                entities["quantity"] = q
            req = [v for k, v in rules.REQUIRED_OPTION_KEYWORDS.items() if k in text]
            if req:
                entities["required_option"] = req
            opt = [v for k, v in rules.OPTIONAL_OPTION_KEYWORDS.items() if k in text]
            if opt:
                entities["optional_option"] = opt
            return "ORDER", entities

        # 메뉴 없이 옵션/수량만 (필수옵션 답변 흐름)
        req = [v for k, v in rules.REQUIRED_OPTION_KEYWORDS.items() if k in text]
        if req:
            return "ORDER", {"required_option": req}
        q = RuleParser._extract_quantity_ruleEngine_ruleParser(text)
        if q is not None:
            return "ORDER", {"quantity": q}

        raise rules.ParseFailedError(rules.MSG_PARSE_FAILED, reason="NO_RULE_MATCHED")

    @staticmethod
    def _extract_quantity_ruleEngine_ruleParser(text: str) -> Optional[int]:
        for word, value in rules.KOREAN_NUMBER.items():
            if word in text:
                return value
        m = re.search(r"(\d+)\s*(잔|개|컵)", text)  # '개/잔/컵' 붙은 숫자만 수량
        if m:
            return int(m.group(1))
        return None