# app/ai/ruleEngine/ruleParser.py
"""Rule Parser : NormalizeResult → ParseResult.

규칙 기반으로 Intent 와 Entity 를 추출한다.
- 시스템 정책: 한 번에 메뉴 1개 / Intent 1개 / 행동 1개.
- 규칙으로 확정 불가(다중 메뉴/해석 불가)는 예외로 위임
  → 상위 파이프라인이 LLM 전달 또는 안내 문구로 처리.

메서드명 규칙 : 행위명_폴더명(ruleEngine)_파일명(ruleParser)
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from app.interface.dto.normalizeResult import NormalizeResult
from app.interface.dto.parseResult import ParseResult
from app.ai.ruleEngine import rules


class RuleParser:

    # ------------------------------------------------------------------
    # 진입점 : NormalizeResult → ParseResult
    # ------------------------------------------------------------------
    @staticmethod
    def parse_ruleEngine_ruleParser(
        normalize_result: NormalizeResult,
    ) -> ParseResult:
        session_id = normalize_result.session_id
        text = (normalize_result.text or "").strip()

        if not text:
            raise rules.ParseFailedError("다시 한 번 말씀해 주세요.", reason="EMPTY_TEXT")

        # 1) 메뉴 감지 — 여기서 다중 메뉴 차단
        menu_ids = RuleParser._find_menus_ruleEngine_ruleParser(text)
        if len(menu_ids) >= 2:
            raise rules.MultipleMenuError(
                "한 번에 한 메뉴씩 주문해 주세요.", reason="MULTIPLE_MENU",
            )

        # 2) Intent 판별 + Entity 추출
        intent, entities = RuleParser._resolve_intent_ruleEngine_ruleParser(
            text=text, menu_ids=menu_ids,
        )

        return ParseResult(
            session_id=session_id,
            intent=intent,
            entities=entities,
            source="RULE",
        )

    # ------------------------------------------------------------------
    # 메뉴 감지 : 긴 이름 우선 + 스팬 제외로 부분문자열 중복/오탐 방지
    #   반환: 감지된 m_id 리스트 (텍스트 등장 순서)
    # ------------------------------------------------------------------
    @staticmethod
    def _find_menus_ruleEngine_ruleParser(text: str) -> List[int]:
        matched: List[Tuple[int, int]] = []    # (시작위치, m_id)
        occupied: List[Tuple[int, int]] = []    # 이미 매칭된 (start, end)

        for name in rules.MENU_NAMES_BY_LEN:
            start = 0
            while True:
                idx = text.find(name, start)
                if idx == -1:
                    break
                end = idx + len(name)
                # 더 긴 이름이 이미 차지한 구간과 겹치면 스킵
                if not any(idx < oe and os_ < end for (os_, oe) in occupied):
                    matched.append((idx, rules.MENU_DICTIONARY[name]))
                    occupied.append((idx, end))
                start = idx + 1

        matched.sort(key=lambda x: x[0])
        return [m_id for (_, m_id) in matched]

    # ------------------------------------------------------------------
    # Intent 판별 + Entity 추출 (우선순위: 구체적 → 일반)
    # ------------------------------------------------------------------
    @staticmethod
    def _resolve_intent_ruleEngine_ruleParser(
        text: str, menu_ids: List[int],
    ) -> Tuple[str, Dict[str, Any]]:

        # SESSION : 취소 / 주문유형 (R016, R015)
        if not menu_ids and any(k in text for k in rules.SESSION_CANCEL_KEYWORDS):
            return "SESSION", {"action": "CANCEL"}
        for keyword, order_type in rules.ORDER_TYPE_KEYWORDS.items():
            if keyword in text:
                return "SESSION", {"order_type": order_type}

        # PAYMENT (R011)
        if any(k in text for k in rules.PAYMENT_KEYWORDS):
            return "PAYMENT", {"action": "START"}

        # CART (R006~R010) : 메뉴가 없을 때
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

        # RECOMMEND (R012, R013)
        if any(k in text for k in rules.RECOMMEND_ACCEPT_KEYWORDS):
            return "RECOMMEND", {"action": "ACCEPT"}
        if any(k in text for k in rules.RECOMMEND_REQUEST_KEYWORDS):
            return "RECOMMEND", {"action": "REQUEST", "condition": text}

        # INFO (R014)
        if any(k in text for k in rules.INFO_KEYWORDS):
            entities: Dict[str, Any] = {"type": "MENU"}
            if menu_ids:
                entities["menu"] = menu_ids[0]
            return "INFO", entities

        # SKIP 선택옵션 (R005) : 메뉴 없이 온 경우
        if not menu_ids and any(k in text for k in rules.SKIP_OPTIONAL_KEYWORDS):
            return "ORDER", {"skip_optional": True}

        # ORDER (R001~R004) : 메뉴 있음
        if menu_ids:
            entities = {"menu": menu_ids[0]}
            quantity = RuleParser._extract_quantity_ruleEngine_ruleParser(text)
            if quantity is not None:
                entities["quantity"] = quantity
            required = [v for k, v in rules.REQUIRED_OPTION_KEYWORDS.items() if k in text]
            if required:
                entities["required_option"] = required
            optional = [v for k, v in rules.OPTIONAL_OPTION_KEYWORDS.items() if k in text]
            if optional:
                entities["optional_option"] = optional
            return "ORDER", entities

        # 옵션/수량만 단독으로 온 경우 (필수옵션 답변 흐름)
        required = [v for k, v in rules.REQUIRED_OPTION_KEYWORDS.items() if k in text]
        if required:
            return "ORDER", {"required_option": required}
        quantity = RuleParser._extract_quantity_ruleEngine_ruleParser(text)
        if quantity is not None:
            return "ORDER", {"quantity": quantity}

        # 어떤 규칙에도 안 걸림 → LLM 전달 (L001/L002/L004)
        raise rules.ParseFailedError("무엇을 도와드릴까요?", reason="NO_RULE_MATCHED")

    # ------------------------------------------------------------------
    # 수량 추출 (R002) : 한글 수사 우선 → 아라비아 숫자
    # ------------------------------------------------------------------
    @staticmethod
    def _extract_quantity_ruleEngine_ruleParser(text: str) -> Optional[int]:
        for word, value in rules.KOREAN_NUMBER.items():
            if word in text:
                return value
        m = re.search(r"(\d+)\s*(잔|개|컵)", text)   # '개/잔/컵' 붙은 숫자만 수량으로
        if m:
            return int(m.group(1))
        return None