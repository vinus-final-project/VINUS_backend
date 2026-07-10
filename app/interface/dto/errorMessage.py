"""에러코드 → 사용자 음성 안내 문구 매핑.

EventExecutor 가 에러 응답을 만들 때 error_code 로 문구를 조회한다.
코드 집합은 FSM 명세서 '실패 코드 정의서' 카탈로그와 1:1 대응.
(음성안내 명세서 기준, 숫자 치환 없는 1차 버전)
"""

# 에러코드 → 음성/UI 안내 문구 (FSM 명세 실패 코드 카탈로그)
ERROR_MESSAGES: dict[str, str] = {
    "INVALID_STATE": "지금은 그 요청을 처리할 수 없어요.",
    "ORDER_ITEM_EXISTS": "현재 주문중인 메뉴부터 마무리해주세요.",
    "ORDER_ITEM_NOT_FOUND": "메뉴를 먼저 선택해주세요.",
    "INVALID_ORDER_ITEM_STATE": "지금은 처리할 수 있는 단계가 아니에요.",
    "REQUIRED_OPTION_MISSING": "필수 옵션을 아직 선택하지 않으셨어요.",
    "EMPTY_CART": "장바구니가 비어있어요. 먼저 메뉴를 담아주세요.",
    "CART_ITEM_NOT_FOUND": "장바구니에서 해당 메뉴를 찾을 수 없어요.",
    "RECOMMENDATION_NOT_FOUND": "추천해드린 메뉴가 없어요. 먼저 추천을 요청해주세요.",
    "MENU_NOT_FOUND": "죄송해요, 그 메뉴는 저희 매장에 없어요.",
    "OPTION_NOT_FOUND": "그 옵션은 없어요. 다시 말씀해주세요.",
    "INVALID_OPTION": "이 메뉴에는 없는 옵션이에요.",
    "INVALID_QUANTITY": "수량은 1개 이상으로 말씀해주세요.",
    "SOLD_OUT_MENU": "죄송해요, 지금은 품절된 메뉴예요.",
    "SOLD_OUT_MENU_EXISTS": "장바구니에 품절된 메뉴가 있어요. 삭제하거나 변경해주세요.",
    "OPTION_MIN_NOT_MET": "옵션을 최소 개수 이상 선택해주세요.",
    "OPTION_LIMIT_EXCEEDED": "선택 가능한 개수를 넘었어요.",
    "SESSION_NOT_FOUND": "세션을 찾을 수 없어요.",
}

# 매핑에 없는 코드(예상치 못한 내부 오류)용 기본 문구
DEFAULT_ERROR_MESSAGE = "요청을 처리할 수 없어요. 다시 시도해주세요."


def get_error_message_error_message(error_code: str | None) -> str:
    """에러코드로 안내 문구 조회 (카탈로그에 없으면 기본 문구)."""
    if error_code is None:
        return DEFAULT_ERROR_MESSAGE
    return ERROR_MESSAGES.get(error_code, DEFAULT_ERROR_MESSAGE)