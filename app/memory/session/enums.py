"""세션 도메인 Enum 모음.

- OrderType         : 매장/포장 구분
- OrderItemStatus   : 작성 중인 주문 항목 상태
- SpeakerType       : 로그 발화 주체

NOTE: FSMState 는 본 파일이 아닌 `app/fsm/state.py` 에 분리되어 있습니다.
"""

from enum import Enum


# 매장/포장 구분
class OrderType(str, Enum):
    STORE = "STORE"      # 매장
    TAKEOUT = "TAKEOUT"  # 포장


class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"
    

# 현재 작성 중인 주문 항목(OrderItem)의 상태
class OrderItemStatus(str, Enum):
    SELECTING_REQUIRED_OPTION = "SELECTING_REQUIRED_OPTION"  # 필수 옵션 선택 중
    ASKING_OPTIONAL_OPTION = "ASKING_OPTIONAL_OPTION"        # 추가 옵션 확인 중
    COMPLETE = "COMPLETE"                                    # 작성 완료


# 로그 발화 주체
class SpeakerType(str, Enum):
    USER = "USER"      # 사용자
    AI = "AI"          # AI 응답
    SYSTEM = "SYSTEM"  # 시스템 메시지