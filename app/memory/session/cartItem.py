"""CartItem : 장바구니에 확정 등록된 주문 항목.

OrderItem 이 COMPLETE 가 되면 Session.create_session_cart_items 를 통해
CartItem 으로 변환되어 cart 에 적재됩니다.
"""

from typing import Any, Dict

from pydantic import BaseModel, Field


class CartItem(BaseModel):
    # -- 변수 선언 ----------------------------------------------------------
    cart_item_id: int                                               # 카트 아이템 ID (세션 내 Auto Increment)
    menu_id: int                                                    # 메뉴 ID
    quantity: int                                                   # 주문 수량
    selected_options: dict[int, int] = Field(default_factory=dict)  # 선택된 옵션