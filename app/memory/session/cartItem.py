"""CartItem : 장바구니에 확정 등록된 주문 항목.

카트에 담길 때 메뉴/옵션 이름·가격을 스냅샷해서 보관한다
(카트 화면 표시 + 총액 계산용).
누적 옵션(샷 2개 등)은 CartItemOption.qty 로 개수를 표현한다.
"""

from pydantic import BaseModel, Field


class CartItemOption(BaseModel):
    """카트 항목에 스냅샷된 선택 옵션 상세."""
    op_id: int          # 옵션 ID
    op_name: str        # 옵션 이름
    op_price: int       # 옵션 1개당 추가금
    qty: int            # 개수 (누적 옵션 — 샷 2개면 qty=2)


class CartItem(BaseModel):
    # -- 변수 선언 ----------------------------------------------------------
    cart_item_id: int                                                     # 카트 아이템 ID (세션 내 Auto Increment)
    menu_id: int                                                          # 메뉴 ID
    menu_name: str                                                        # 메뉴명 스냅샷 (표시용)
    quantity: int = Field(ge=1)                                           # 주문 수량 (메뉴 잔 수)
    unit_price: int                                                       # 1개당 가격 (메뉴가 + 옵션가×개수 합)
    selected_options: dict[int, list[int]] = Field(default_factory=dict)  # 선택 옵션 (og_id -> [op_id...], 중복=개수, 병합 비교용)
    options: list[CartItemOption] = Field(default_factory=list)           # 선택 옵션 상세 (표시/가격용, qty 압축)