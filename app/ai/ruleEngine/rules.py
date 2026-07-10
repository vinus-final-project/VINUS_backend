# app/ai/ruleEngine/rules.py
"""Rule Parser 사전·키워드·예외. (현재 코드 기준: 옵션 +/- 누적 모델)"""

import csv
import os
from typing import Dict, List

_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rapidfuzz")
_MENUS_CSV = os.path.join(_BASE_DIR, "menus.csv")


def _load_menu_dictionary() -> Dict[str, int]:
    result: Dict[str, int] = {}
    if not os.path.exists(_MENUS_CSV):
        return result
    with open(_MENUS_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = (row.get("m_name") or "").strip()
            if name:
                result[name] = int(row["m_id"])
    return result


MENU_DICTIONARY: Dict[str, int] = _load_menu_dictionary()
MENU_NAMES_BY_LEN: List[str] = sorted(MENU_DICTIONARY.keys(), key=len, reverse=True)

# --- Intent 키워드 ---
SESSION_CANCEL_KEYWORDS = ("취소", "처음부터", "그만할")
ORDER_TYPE_KEYWORDS = {"매장": "STORE", "먹고": "STORE", "마시고": "STORE",
                       "포장": "TAKEOUT", "테이크아웃": "TAKEOUT", "가져갈": "TAKEOUT", "갖고": "TAKEOUT", "들고": "TAKEOUT"}
PAYMENT_KEYWORDS = ("결제", "계산", "지불")
CART_CLEAR_KEYWORDS = ("전체 삭제", "다 빼", "비워", "다 지워")
CART_INCREASE_KEYWORDS = ("하나 더", "더 담", "증가", "늘려")
CART_DECREASE_KEYWORDS = ("하나 빼", "감소", "줄여")
CART_REMOVE_KEYWORDS = ("삭제", "빼줘", "제거")
CART_SHOW_KEYWORDS = ("장바구니", "담은", "카트")
RECOMMEND_ACCEPT_KEYWORDS = ("그걸로", "그거로", "추천 메뉴")
RECOMMEND_REQUEST_KEYWORDS = ("추천",)
INFO_KEYWORDS = ("뭐 있어", "메뉴 알려", "무슨 메뉴", "설명")
SKIP_OPTIONAL_KEYWORDS = ("안 할게", "안할래", "그대로", "없어요", "괜찮아요", "그거면")

# --- 옵션: 필수(단일선택, 교체) — 값=표준 op 토큰 ---
REQUIRED_OPTION_KEYWORDS = {
    "아이스": "ICE", "차갑": "ICE", "시원": "ICE", "얼음": "ICE",
    "핫": "HOT", "뜨겁": "HOT", "따뜻": "HOT", "따숩": "HOT", "따신": "HOT",
    "라지": "라지", "큰": "라지",
    "레귤러": "레귤러", "작은": "레귤러", "보통": "레귤러", "기본": "레귤러"
}
# --- 옵션: 선택(누적 +/-) — 값=표준 op 토큰 (op_id 해석은 RuleEngine) ---
OPTIONAL_OPTION_KEYWORDS = {
    "샷": "샷", "바닐라": "바닐라 시럽", "헤이즐넛": "헤이즐넛 시럽",
    "카라멜": "카라멜 시럽", "시럽": "시럽", "휘핑": "휘핑 추가",
}
OPTION_REMOVE_KEYWORDS = ("빼", "제거", "말고", "없이", "취소")

# --- 수량/개수 한글 수사 ---
KOREAN_NUMBER = {"하나": 1, "한": 1, "둘": 2, "두": 2, "셋": 3, "세": 3,
                 "넷": 4, "네": 4, "다섯": 5, "여섯": 6, "일곱":7, "여덟":8, "아홉":9, "열":10}

MSG_MULTIPLE_MENU = "한 번에 한 메뉴씩 주문해 주세요."
MSG_PARSE_FAILED = "죄송해요, 다시 한 번 말씀해 주세요."


class RuleParseError(Exception):
    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.message = message
        self.reason = reason


class MultipleMenuError(RuleParseError): ...
class ParseFailedError(RuleParseError): ...