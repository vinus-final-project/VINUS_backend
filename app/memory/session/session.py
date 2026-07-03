"""Session : 세션 메모리 전체.

- 한 명의 사용자가 키오스크 앞에서 주문을 시작해서 끝낼 때까지의
  모든 진행 상태(현재 작성 중인 주문, 장바구니, 로그 등)를 담는 객체.
- 메모리(RAM)에만 존재하며 SessionMemory 가 Map 으로 보관합니다.
- 본 파일에는 Session 외에 같은 도메인에 속하는 Log 모델도 함께 둡니다.

데이터 구조만 정의합니다. CRUD 동작은 sessionCrud.py 에 모입니다.
"""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, PrivateAttr

from app.fsm.FSMstate import FSMState
from app.memory.session.cartItem import CartItem
from app.memory.session.enums import OrderType, SpeakerType, SessionStatus
from app.memory.session.orderItem import OrderItem


# ---------------------------------------------------------------------------
# Log : 세션 로그 한 줄 (USER/AI/SYSTEM 발화)
# ---------------------------------------------------------------------------
class Log(BaseModel):
    # -- 변수 선언 ----------------------------------------------------------
    speaker: SpeakerType                                        # 발화 주체
    message: str                                                # 발화 내용
    intent: Optional[str] = None                                # 분석된 의도(있으면)
    created_at: datetime = Field(default_factory=datetime.now)  # 생성 시간


# ---------------------------------------------------------------------------
# Session : 세션 전체 메모리
# ---------------------------------------------------------------------------
class Session(BaseModel):
    # -- 변수 선언 ----------------------------------------------------------
    session_id: str                                             # 세션 식별자 UUID
    created_at: datetime = Field(default_factory=datetime.now)  # 세션 생성 시간
    session_status : SessionStatus = SessionStatus.ACTIVE       # 세션 생명주기 (ACTIVE/COMPLETED/EXPIRED/CANCELED)

    fsm_state: FSMState = FSMState.INIT                # 현재 FSM 상태
    order_type: Optional[OrderType] = None             # 매장/포장 (선택 전엔 None)
    order_item: Optional[OrderItem] = None             # 현재 작성 중인 주문 항목
    current_menu: Optional[dict] = None                # 현재 주문 메뉴 상세 스냅샷
    cart: list[CartItem] = Field(default_factory=list) # 장바구니
    recommendation_list: list[int] = Field(default_factory=list)   # 추천 메뉴 리스트
    logs: list[Log] = Field(default_factory=list)      # 세션 로그 버퍼
    message: Optional[str] = None                # 사용자에게 보여줄 응답 텍스트(TTS와 동일)

    # 카트 아이템 ID 자동 증가용 내부 카운터 (sessionCrud 에서 사용, 직렬화 대상 아님)
    # PrivateAttr 은 이름이 underscore 로 시작해야 합니다.
    _next_cart_item_id: int = PrivateAttr(default=1) # 세션 내부 임시 ID