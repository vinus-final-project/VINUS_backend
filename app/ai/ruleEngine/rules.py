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
# 명시적 전체 취소(세션) — 단독 "취소" 는 CANCEL_KEYWORDS 로 분리 (문맥 해석)
SESSION_CANCEL_KEYWORDS = ("처음부터", "처음으로", "전부 취소", "다 취소", "그만할", "그만둘")
# 제네릭 취소 — RuleEngine 이 세션 문맥으로 결제취소/주문취소/세션취소 결정
CANCEL_KEYWORDS = ("취소",)
ORDER_TYPE_KEYWORDS = {"매장": "STORE", "먹고": "STORE", "마시고": "STORE",
                       "포장": "TAKEOUT", "테이크아웃": "TAKEOUT", "가져갈": "TAKEOUT", "갖고": "TAKEOUT", "들고": "TAKEOUT"}
PAYMENT_KEYWORDS = ("결제", "계산", "지불")
# 결제수단 발화 — 카드: 결제창(/pay) 진행, 현금: 미지원 안내
PAY_CARD_KEYWORDS = ("카드",)          # "신용카드/체크카드" 포함 (substring)
PAY_CASH_KEYWORDS = ("현금",)
CART_CLEAR_KEYWORDS = ("전체 삭제", "다 빼", "비워", "다 지워")
CART_INCREASE_KEYWORDS = ("하나 더", "더 담", "증가", "늘려", "추가")
# 발화 별칭 — 파싱 전 치환 (관용 표현 + STT 상습 오인식 정규화)
SPEECH_ALIASES = {
    "투샷": "샷 2개", "투 샷": "샷 2개", "더블샷": "샷 2개", "더블 샷": "샷 2개",
    "쓰리샷": "샷 3개", "쓰리 샷": "샷 3개", "원샷": "샷 1개",
    # STT 가 "샷 추가"를 잘못 받아쓰는 변형들 (실측 기반)
    "샷투가": "샷 추가", "샷 투가": "샷 추가",
    "샷2가": "샷 추가", "샷 2가": "샷 추가", "샤추가": "샷 추가",
}
CART_DECREASE_KEYWORDS = ("하나 빼", "감소", "줄여")
CART_REMOVE_KEYWORDS = ("삭제", "빼줘", "빼 줘", "빼죠", "빼 죠", "빼주",
                        "제거", "취소", "지워", "없애")
#   "아메리카노 취소" = 카트에서 제거, "빼주"=빼주세요 커버
#   "다 지워"(전체 삭제)는 CLEAR 가 먼저 검사돼서 충돌 없음
CART_SHOW_KEYWORDS = ("장바구니", "담은", "카트")
# 화면 이동: 전체 메뉴(주문) 화면 복귀 — FSM 이벤트 없음 (voicePipeline 이 SHOW_MENU 응답)
NAVIGATE_MENU_KEYWORDS = ("돌아가", "뒤로", "메뉴 더", "다른 메뉴", "메뉴 보여",
                          "메뉴판", "더 주문", "주문 더", "계속 주문")
# 카테고리 전환 ("커피 메뉴 보여줘") — 값 = DB c_name (프론트 탭 이름과 동일)
#   ⚠ "차"는 단음절이라 복합 표현만 등록 ("차갑게" 오매칭 방지)
#   메뉴명이 감지된 발화("요거트 스무디 주세요")는 이 분기를 타지 않음
CATEGORY_KEYWORDS = {
    "전체 메뉴": "전체", "전체 보여": "전체", "모든 메뉴": "전체", "메뉴 전체": "전체",
    "커피": "커피/라떼", "라떼 종류": "커피/라떼", "라떼 메뉴": "커피/라떼",
    "음료": "음료/에이드/스무디", "에이드": "음료/에이드/스무디", "스무디": "음료/에이드/스무디",
    "차 메뉴": "차", "차 종류": "차", "차 보여": "차", "티 메뉴": "차",
    "요거트": "요거트",
    "디저트": "디저트/베이커리", "베이커리": "디저트/베이커리", "빵": "디저트/베이커리",
}
# 페이지 넘김 — 방향만 전달, 범위 클램프는 프론트(페이지 수를 아는 쪽)가 담당
#   STT 붙여쓰기 변형 포함 ("다음장", "다음페이지")
PAGE_NEXT_KEYWORDS = ("다음 페이지", "다음페이지", "다음 장", "다음장",
                      "넘겨", "다음 메뉴 보여")
PAGE_PREV_KEYWORDS = ("이전 페이지", "이전페이지", "이전 장", "이전장",
                      "앞 페이지", "앞페이지", "전 페이지", "앞 장", "앞장")
# 합계 질문 — 명시적 표현만 (단독 "얼마"는 INFO→현재 메뉴 가격 질문으로 처리)
TOTAL_PRICE_KEYWORDS = ("합계", "총액", "총 얼마", "총 금액", "다 해서", "전부 얼마", "얼마 나왔")
# 추천 수락 서수 ("두 번째 걸로")
ORDINAL_KEYWORDS = {
    "첫 번째": 1, "첫번째": 1, "1번": 1,
    "두 번째": 2, "두번째": 2, "2번": 2,
    "세 번째": 3, "세번째": 3, "3번": 3,
    "네 번째": 4, "네번째": 4, "4번": 4,
    "다섯 번째": 5, "다섯번째": 5, "5번": 5,
}
# 옵션 전량 제거 수식어 (옵션 키워드 뒤 window 안, REMOVE 키워드와 함께 쓰일 때)
OPTION_REMOVE_ALL_KEYWORDS = ("전부", "모두", "다 ")
RECOMMEND_ACCEPT_KEYWORDS = ("그걸로", "그거로", "추천 메뉴")
RECOMMEND_REQUEST_KEYWORDS = ("추천",)
INFO_KEYWORDS = ("뭐 있어", "메뉴 알려", "무슨 메뉴", "설명",
                 "얼마", "가격", "뭐야", "들어가", "알레르기", "성분")
SKIP_OPTIONAL_KEYWORDS = (
    "안 할게", "안할래", "그대로", "없어요", "괜찮아요", "그거면",
    "완료", "담아", "다 골랐", "이대로", "이걸로",   # 주문/선택 완료 발화
    "그렇게", "그걸로 주", "됐어요", "충분해",       # "그렇게 주세요" 등
)

# --- 옵션: 단일선택(교체) 그룹 — 값=표준 op_name ---
#   긴 키워드부터 매칭 후 스팬 소비 ("얼음 적게"가 "얼음"→ICE 에 잡히지 않도록)
#   해당 메뉴에 없는 옵션 값은 RuleEngine 이 조용히 무시 (스무디에 "아이스" 등)
REQUIRED_OPTION_KEYWORDS = {
    # 온도
    "아이스": "ICE", "차갑": "ICE", "시원": "ICE", "차가": "ICE","얼음": "ICE",
    "핫": "HOT", "뜨겁": "HOT","뜨거": "HOT", "따뜻": "HOT", "따숩": "HOT", "따신": "HOT",
    # 사이즈
    "라지": "라지", "큰": "라지",
    "레귤러": "레귤러", "작은": "레귤러", "보통": "레귤러", "기본": "레귤러",
    # 얼음량 (음료/에이드/스무디) — "얼음량 X" 발화 변형 포함
    "얼음 적게": "적게", "얼음 조금": "적게", "얼음 없이": "적게", "얼음 빼": "적게",
    "얼음량 적게": "적게", "얼음량 조금": "적게",
    "얼음 보통": "보통", "얼음량 보통": "보통",
    "얼음 많이": "많이", "얼음 가득": "많이", "얼음량 많이": "많이",
    # 당도 (STT 는 "퍼센트"를 "프로"로 받아쓰는 경우가 많음 — 변형 포함)
    "당도 0": "0%", "0%": "0%", "0퍼": "0%", "0프로": "0%", "0 프로": "0%",
    "무설탕": "0%", "안 달게": "0%", "설탕 빼": "0%",
    "당도 50": "50%", "50%": "50%", "50퍼": "50%", "50프로": "50%", "50 프로": "50%",
    "오십프로": "50%", "오십 프로": "50%", "덜 달게": "50%", "반만 달게": "50%",
    "당도 100": "100%", "100%": "100%", "100퍼": "100%", "100프로": "100%",
    "100 프로": "100%", "백프로": "100%", "백 프로": "100%", "달게": "100%",
}
# --- 옵션: 선택(누적 +/-) — 값=표준 op 토큰 (op_id 해석은 RuleEngine) ---
OPTIONAL_OPTION_KEYWORDS = {
    "샷": "샷", "바닐라": "바닐라 시럽", "헤이즐넛": "헤이즐넛 시럽",
    "카라멜": "카라멜 시럽", "시럽": "시럽", "휘핑": "휘핑 추가",
}
OPTION_REMOVE_KEYWORDS = ("빼", "제거", "말고", "없이", "취소")

# --- 수량/개수 한글 수사 ---
# 완전형 — 단독 매칭 허용 ("둘", "다섯")
KOREAN_NUMBER_FULL = {"하나": 1, "둘": 2, "셋": 3, "넷": 4, "다섯": 5,
                      "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9, "열": 10}
# 관형형 단음절 — 단위(잔/컵/개)가 붙을 때만 인정
#   ("주세요"의 '세', "따뜻한"의 '한' 오인식 방지)
KOREAN_NUMBER_MODIFIER = {"한": 1, "두": 2, "세": 3, "네": 4}
# (하위 호환) 통합 사전
KOREAN_NUMBER = {**KOREAN_NUMBER_FULL, **KOREAN_NUMBER_MODIFIER}

MSG_MULTIPLE_MENU = "한 번에 한 메뉴씩 주문해 주세요."
MSG_PARSE_FAILED = "죄송해요, 다시 한 번 말씀해 주세요."


class RuleParseError(Exception):
    def __init__(self, message: str, reason: str):
        super().__init__(message)
        self.message = message
        self.reason = reason


class MultipleMenuError(RuleParseError): ...
class ParseFailedError(RuleParseError): ...