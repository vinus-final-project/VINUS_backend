"""OrderItem : 현재 작성 중인 주문 항목 (pending item).

세션 안에서 사용자가 지금 만들고 있는 메뉴 한 건을 표현합니다.
status 가 COMPLETE 가 되어야만 cart 로 옮길 수 있습니다.
"""

from typing import Any, Dict

from pydantic import BaseModel, Field

from app.memory.session.enums import OrderItemStatus


class OrderItem(BaseModel):
    # -- 변수 선언 ----------------------------------------------------------
    menu_id: int                                                    # 메뉴 ID
    quantity: int = Field(default=1, ge=1)                                              # 주문 수량
    selected_options: Dict[int, int] = Field(default_factory=dict)  # 선택된 옵션
    status: OrderItemStatus = OrderItemStatus.SELECTING_REQUIRED_OPTION  # 작성 상태