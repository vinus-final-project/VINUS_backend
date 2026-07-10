# app/ai/ruleEngine/ruleParser.py
"""Rule Parser : NormalizeResult → ParseResult. (옵션 +/- 누적 모델 대응)

entities(ORDER):
  menu            : m_id
  quantity        : int (메뉴 잔 수)
  required_option : [ "ICE", "라지" ]              # 단일선택(교체)
  optional_option : [ {"value","count","action"} ] # 누적 +/- (ADD/REMOVE)
  skip_optional   : True
op_id 해석·이벤트(SELECT_OPTION/DESELECT_OPTION) 매핑은 RuleEngine 담당.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

from app.interface.dto.normalizeResult import NormalizeResult
from app.interface.dto.parseResult import ParseResult
from app.ai.ruleEngine import rules


class RuleParser:

    @staticmethod
    def parse_ruleEngine_ruleParser(nr: NormalizeResult) -> ParseResult:
        session_id = nr.session_id
        text = (nr.text or "").strip()
        if not text:
            raise rules.ParseFailedError(rules.MSG_PARSE_FAILED, reason="EMPTY_TEXT")

        # 1) 메뉴 감지 — 다중 메뉴 차단
        menu_spans = RuleParser._find_menus(text)
        menu_ids = [mid for (_, _, mid) in menu_spans]
        if len(menu_ids) >= 2:
            raise rules.MultipleMenuError(rules.MSG_MULTIPLE_MENU, reason="MULTIPLE_MENU")

        # 2) Intent + Entity
        intent, entities = RuleParser._resolve_intent(text, menu_ids, menu_spans)
        return ParseResult(session_id=session_id, intent=intent,
                           entities=entities, source="RULE")

    # 메뉴 감지: 긴 이름 우선 + 스팬 제외 → [(start, end, m_id)]
    @staticmethod
    def _find_menus(text: str) -> List[Tuple[int, int, int]]:
        found: List[Tuple[int, int, int]] = []
        occupied: List[Tuple[int, int]] = []
        for name in rules.MENU_NAMES_BY_LEN:
            start = 0
            while True:
                idx = text.find(name, start)
                if idx == -1:
                    break
                end = idx + len(name)
                if not any(idx < oe and os_ < end for (os_, oe) in occupied):
                    found.append((idx, end, rules.MENU_DICTIONARY[name]))
                    occupied.append((idx, end))
                start = idx + 1
        found.sort(key=lambda x: x[0])
        return found

    # Intent 판별
    @staticmethod
    def _resolve_intent(
        text: str, menu_ids: List[int], menu_spans: List[Tuple[int, int, int]],
    ) -> Tuple[str, Dict[str, Any]]:

        # 옵션 단어(샷/휘핑/아이스 등) 포함 여부 — 카트/취소 분기와 옵션 조작 구분용
        #   ("휘핑 빼줘"/"샷 취소"는 카트 조작·세션 취소가 아니라 옵션 감소)
        has_option_word = any(
            k in text for k in rules.OPTIONAL_OPTION_KEYWORDS
        ) or any(k in text for k in rules.REQUIRED_OPTION_KEYWORDS)

        # 1) 명시적 전체 취소 ("처음부터", "전부 취소" 등) → 세션 취소
        if not menu_ids and any(k in text for k in rules.SESSION_CANCEL_KEYWORDS):
            return "SESSION", {"action": "CANCEL"}

        # 2) 제네릭 "취소" (메뉴/옵션 단어 없음) → 문맥 해석은 RuleEngine
        #    (PAYMENT 상태→결제취소, 주문 작성 중→주문취소, 그 외→세션취소)
        if not menu_ids and not has_option_word and any(
            k in text for k in rules.CANCEL_KEYWORDS
        ):
            return "CANCEL", {}

        for kw, ot in rules.ORDER_TYPE_KEYWORDS.items():
            if kw in text:
                return "SESSION", {"order_type": ot}

        if any(k in text for k in rules.PAYMENT_KEYWORDS):
            return "PAYMENT", {"action": "START"}

        # 3) 카트 조작 — 메뉴 지정 허용 ("아메리카노 빼줘")
        #    옵션 단어가 있으면 옵션 증감이므로 ORDER 경로로 넘긴다.
        if not has_option_word:
            cart_action = None
            if any(k in text for k in rules.CART_CLEAR_KEYWORDS):
                cart_action = "CLEAR"
            elif any(k in text for k in rules.CART_INCREASE_KEYWORDS):
                cart_action = "INCREASE"
            elif any(k in text for k in rules.CART_DECREASE_KEYWORDS):
                cart_action = "DECREASE"
            elif any(k in text for k in rules.CART_REMOVE_KEYWORDS):
                cart_action = "REMOVE"
            elif not menu_ids and any(k in text for k in rules.CART_SHOW_KEYWORDS):
                cart_action = "SHOW"
            if cart_action:
                e: Dict[str, Any] = {"action": cart_action}
                if menu_ids and cart_action in ("REMOVE", "INCREASE", "DECREASE"):
                    e["menu"] = menu_ids[0]
                return "CART", e

        # 4) 화면 이동: 전체 메뉴(주문) 화면 복귀 — "돌아가/뒤로/메뉴 더"
        #    (상태 변경 없음 — voicePipeline 이 SHOW_MENU 응답으로 처리)
        if not menu_ids and any(k in text for k in rules.NAVIGATE_MENU_KEYWORDS):
            return "NAVIGATE", {"target": "MENU"}

        if any(k in text for k in rules.RECOMMEND_ACCEPT_KEYWORDS):
            return "RECOMMEND", {"action": "ACCEPT"}
        if any(k in text for k in rules.RECOMMEND_REQUEST_KEYWORDS):
            return "RECOMMEND", {"action": "REQUEST", "condition": text}

        if any(k in text for k in rules.INFO_KEYWORDS):
            e: Dict[str, Any] = {"type": "MENU"}
            if menu_ids:
                e["menu"] = menu_ids[0]
            return "INFO", e

        if not menu_ids and any(k in text for k in rules.SKIP_OPTIONAL_KEYWORDS):
            return "ORDER", {"skip_optional": True}

        # --- ORDER : 옵션/수량 흐름 ---
        # 메뉴 스팬을 지운 작업용 텍스트(옵션·수량 오검출 방지)
        work = RuleParser._blank_spans(text, [(s, e) for (s, e, _) in menu_spans])

        entities: Dict[str, Any] = {}
        if menu_ids:
            entities["menu"] = menu_ids[0]

        required = RuleParser._extract_required(work)
        if required:
            entities["required_option"] = required

        optional, work = RuleParser._extract_optional(work)
        if optional:
            entities["optional_option"] = optional

        quantity = RuleParser._extract_quantity(work)
        if quantity is not None:
            entities["quantity"] = quantity

        if entities:
            return "ORDER", entities

        raise rules.ParseFailedError(rules.MSG_PARSE_FAILED, reason="NO_RULE_MATCHED")

    # 필수 옵션(단일, 교체) → 값 리스트
    @staticmethod
    def _extract_required(work: str) -> List[str]:
        out: List[str] = []
        for kw, val in rules.REQUIRED_OPTION_KEYWORDS.items():
            if kw in work and val not in out:
                out.append(val)
        return out

    # 선택 옵션(누적 +/-) → [{value, count, action}], 처리한 스팬은 blank
    @staticmethod
    def _extract_optional(work: str) -> Tuple[List[Dict[str, Any]], str]:
        out: List[Dict[str, Any]] = []
        seen = set()
        for kw, val in rules.OPTIONAL_OPTION_KEYWORDS.items():
            idx = work.find(kw)
            if idx == -1 or val in seen:
                continue
            window = work[idx: idx + 8]                 # 키워드 뒤 짧은 구간
            action = ("REMOVE" if any(r in window for r in rules.OPTION_REMOVE_KEYWORDS)
                      else "ADD")
            count = RuleParser._number_in(window) or 1
            out.append({"value": val, "count": count, "action": action})
            seen.add(val)
            work = work[:idx] + " " * (idx + 8 - idx) + work[idx + 8:]  # 스팬 blank
        return out, work

    # 메뉴 수량: 숫자+단위 → 관형형 수사+단위 → 완전형 수사 순
    #   관형형(한/두/세/네)은 단위 필수 — "주세요"의 '세' 오인식 방지
    @staticmethod
    def _extract_quantity(work: str) -> Optional[int]:
        m = re.search(r"(\d+)\s*(잔|컵|개)", work)
        if m:
            return int(m.group(1))
        m = re.search(r"(한|두|세|네)\s*(잔|컵|개)", work)
        if m:
            return rules.KOREAN_NUMBER_MODIFIER[m.group(1)]
        for word, v in rules.KOREAN_NUMBER_FULL.items():
            if word in work:
                return v
        return None

    # 구간(윈도우) 안 숫자(아라비아/한글수사) → int
    #   관형형 수사는 단위가 붙을 때만 ("샷 추가해 주세요"의 '세' 방지)
    @staticmethod
    def _number_in(s: str) -> Optional[int]:
        m = re.search(r"(\d+)", s)
        if m:
            return int(m.group(1))
        m = re.search(r"(한|두|세|네)\s*(잔|컵|개|번)", s)
        if m:
            return rules.KOREAN_NUMBER_MODIFIER[m.group(1)]
        for word, v in rules.KOREAN_NUMBER_FULL.items():
            if word in s:
                return v
        return None

    @staticmethod
    def _blank_spans(text: str, spans: List[Tuple[int, int]]) -> str:
        chars = list(text)
        for (s, e) in spans:
            for i in range(s, min(e, len(chars))):
                chars[i] = " "
        return "".join(chars)