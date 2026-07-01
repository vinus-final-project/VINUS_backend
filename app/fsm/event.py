"""FSM Event 정의.

Rule Engine 또는 LLM이 생성하여 EventExecutor를 통해
FSM.dispatch()로 전달되는 이벤트입니다.
"""

from enum import Enum
from pydantic import BaseModel, Field

class Event(str, Enum):
    # ------------------------------------------------------------------
    # 주문 유형
    # ------------------------------------------------------------------
    SELECT_ORDER_TYPE = "SELECT_ORDER_TYPE"

    # ------------------------------------------------------------------
    # 주문
    # ------------------------------------------------------------------
    SELECT_MENU = "SELECT_MENU"
    SET_QUANTITY = "SET_QUANTITY"
    CANCEL_ORDER_ITEM = "CANCEL_ORDER_ITEM"

    # ------------------------------------------------------------------
    # 옵션
    # ------------------------------------------------------------------
    SELECT_REQUIRED_OPTION = "SELECT_REQUIRED_OPTION"
    SELECT_OPTIONAL_OPTION = "SELECT_OPTIONAL_OPTION"
    SKIP_OPTIONAL_OPTION = "SKIP_OPTIONAL_OPTION"

    # ------------------------------------------------------------------
    # 장바구니
    # ------------------------------------------------------------------
    SHOW_CART = "SHOW_CART"
    REMOVE_CART_ITEM = "REMOVE_CART_ITEM"
    CLEAR_CART = "CLEAR_CART"
    INCREASE_CART_ITEM = "INCREASE_CART_ITEM"
    DECREASE_CART_ITEM = "DECREASE_CART_ITEM"

    # ------------------------------------------------------------------
    # 추천
    # ------------------------------------------------------------------
    REQUEST_RECOMMENDATION = "REQUEST_RECOMMENDATION"
    ACCEPT_RECOMMENDATION = "ACCEPT_RECOMMENDATION"

    # ------------------------------------------------------------------
    # 메뉴 정보
    # ------------------------------------------------------------------
    REQUEST_MENU_INFO = "REQUEST_MENU_INFO"

    # ------------------------------------------------------------------
    # 결제
    # ------------------------------------------------------------------
    START_PAYMENT = "START_PAYMENT"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_CANCEL = "PAYMENT_CANCEL"

    # ------------------------------------------------------------------
    # 세션
    # ------------------------------------------------------------------
    CANCEL_SESSION = "CANCEL_SESSION"
    EXPIRE_SESSION = "EXPIRE_SESSION"

class FSMEvent(BaseModel):
    """Rule Engine/LLM 이 생성하는 단일 이벤트 (타입 + 파라미터)."""
    type: Event
    parameters: dict = Field(default_factory=dict)