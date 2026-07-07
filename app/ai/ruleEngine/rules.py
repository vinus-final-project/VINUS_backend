# app/ai/ruleEngine/rules.py
"""Rule 정의 : Rule Parser 가 사용하는 사전/키워드 테이블 및 예외.

- 메뉴 사전은 RapidFuzz 와 동일한 menus.csv 에서 로드한다.
- Intent/Entity 키워드는 Rule ENGINE 명세서 R001~R016 을 따른다.
- 파서가 규칙으로 확정 못하는 경우(다중 메뉴/다중 Intent/해석 불가)는
  예외로 상위(파이프라인)에 위임 → LLM 전달 또는 안내 문구.
"""

import csv
import os
from typing import Dict, List

# --- CSV 경로 (RapidFuzz 파일 재사용) ---------------------------------------
_BASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "rapidfuzz")
_MENUS_CSV = os.path.join(_BASE_DIR, "menus.csv")


def _load_menu_dictionary() -> Dict[str, int]:
    """menus.csv → {표준 메뉴명: m_id}"""
    result: Dict[str, int] = {}
    if not os.path.exists(_MENUS_CSV):
        return result
    with open(_MENUS_CSV, "r", encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            name = (row.get("m_name") or "").strip()
            if name:
                result[name] = int(row["m_id"])
    return result


# {메뉴명: m_id} — import 시 1회 로드
MENU_DICTIONARY: Dict[str, int] = _load_menu_dictionary()
# 길이 내림차순 (긴 이름 우선 매칭 → 부분문자열 오탐 방지)
MENU_NAMES_BY_LEN: List[str] = sorted(MENU_DICTIONARY.keys(), key=len, reverse=True)


# --- Intent 키워드 (R006~R016) ---------------------------------------------
SESSION_CANCEL_KEYWORDS = ("취소", "처음부터", "그만할")           # R016
ORDER_TYPE_KEYWORDS = {                                          # R015
    "매장": "STORE", "먹고": "STORE",
    "포장": "TAKEOUT", "테이크아웃": "TAKEOUT", "가져갈": "TAKEOUT",
}
PAYMENT_KEYWORDS = ("결제", "계산", "지불")                       # R011
CART_CLEAR_KEYWORDS = ("전체 삭제", "다 빼", "비워", "다 지워")    # R008
CART_INCREASE_KEYWORDS = ("하나 더", "더 추가", "증가", "늘려")    # R009
CART_DECREASE_KEYWORDS = ("하나 빼", "감소", "줄여")              # R010
CART_REMOVE_KEYWORDS = ("삭제", "빼줘", "제거")                   # R007
CART_SHOW_KEYWORDS = ("장바구니", "담은", "카트")                 # R006
RECOMMEND_ACCEPT_KEYWORDS = ("그걸로", "그거로", "추천 메뉴")      # R013
RECOMMEND_REQUEST_KEYWORDS = ("추천",)                          # R012
INFO_KEYWORDS = ("뭐 있어", "메뉴 알려", "무슨 메뉴", "설명")       # R014
SKIP_OPTIONAL_KEYWORDS = ("안 할게", "안할래", "그대로", "없어요", "괜찮아요")  # R005

# --- 옵션 키워드 (R003 필수 / R004 선택) — 값은 표준값(명세 예시 수준) -------
# 실제 option_id 매핑은 RuleEngine/Controller(DB) 단계에서 수행.
REQUIRED_OPTION_KEYWORDS = {
    "아이스": "ICE", "차갑게": "ICE", "시원하게": "ICE",
    "핫": "HOT", "뜨겁게": "HOT", "따뜻하게": "HOT", "따숩게": "HOT",
    "라지": "라지", "큰거": "라지",
    "레귤러": "레귤러", "작은": "레귤러",
}
OPTIONAL_OPTION_KEYWORDS = {
    "샷 두": "샷 2개 추가", "샷 2": "샷 2개 추가",
    "샷 추가": "샷 1개 추가", "샷추가": "샷 1개 추가", "샷 하나": "샷 1개 추가",
    "바닐라 시럽": "바닐라 시럽", "헤이즐넛 시럽": "헤이즐넛 시럽", "카라멜 시럽": "카라멜 시럽",
    "휘핑": "휘핑 추가",
}

# --- 수량 표현 (R002) -------------------------------------------------------
KOREAN_NUMBER = {
    "하나": 1, "한잔": 1, "한 잔": 1,
    "둘": 2, "두잔": 2, "두 잔": 2, "두개": 2, "두 개": 2,
    "셋": 3, "세잔": 3, "세 잔": 3, "네잔": 4, "넷": 4,
    "다섯": 5,
}


# --- 파서 예외 : 규칙으로 확정 불가 → 상위(LLM/안내)로 위임 ------------------
class RuleParseError(Exception):
    """규칙으로 확정할 수 없는 경우의 기반 예외."""
    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.message = message   # 사용자 안내 문구(TTS/UI)
        self.reason = reason     # 내부 사유 코드 (로그/분기용)


class MultipleMenuError(RuleParseError):
    """여러 메뉴가 동시에 감지됨 (시스템 정책: 한 번에 1개)."""


class MultipleIntentError(RuleParseError):
    """여러 Intent 가 동시에 감지됨 (L006)."""


class ParseFailedError(RuleParseError):
    """Intent/메뉴를 규칙으로 해석하지 못함 → LLM 전달 (L001/L002/L004)."""