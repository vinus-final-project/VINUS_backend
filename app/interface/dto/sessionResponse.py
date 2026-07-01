from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field

from app.fsm.FSMstate import FSMState
from app.memory.session.enums import OrderType
from app.memory.session.orderItem import OrderItem
from app.memory.session.cartItem import CartItem


class ResponseType(str, Enum):
    NORMAL = "NORMAL"
    ERROR = "ERROR"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_CANCEL = "PAYMENT_CANCEL"
    SESSION_END = "SESSION_END"


class SessionResponse(BaseModel):
    response_type: ResponseType                                     # 응답 종류
    session_id: str                                                 # 세션 식별자
    success: bool                                                   # 처리 성공 여부
    message: Optional[str] = None                                   # TTS/UI 안내 문구
    fsm_state: FSMState                                             # 현재 FSM 상태
    order_type: Optional[OrderType] = None                         # 매장/포장
    order_item: Optional[OrderItem] = None                         # 현재 작성 중 주문
    cart: list[CartItem] = Field(default_factory=list)             # 장바구니
    recommendation_list: list[int] = Field(default_factory=list)   # 추천 메뉴
    error_code: Optional[str] = None                               # 오류 코드
    session_end: bool = False                                       # 세션 종료 여부