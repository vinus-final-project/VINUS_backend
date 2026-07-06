"""FSM Event Validator (비-DB 검증).

transition 표(상태 전이)와 별개로, 세션 데이터/파라미터 수준의
선행 조건을 검사합니다. 메뉴/옵션/품절 등 DB 의존 검증은 Controller 담당.
실패 시 ValueError(에러코드 문자열) 발생.
"""

from typing import Optional

from app.fsm.event import Event, FSMEvent
from app.memory.session.enums import OrderItemStatus
from app.memory.session.session import Session


class Validator:

    @staticmethod
    def validate_fsm_validator(
        session: Optional[Session],
        fsm_event: FSMEvent,
    ) -> None:
        """이벤트 실행 전 비-DB 선행조건 검증"""

        event = fsm_event.type
        params = fsm_event.parameters

        match event:

            case Event.SELECT_ORDER_TYPE:
                return

            case Event.SELECT_MENU:
                if session.order_item is not None:
                    raise ValueError("ORDER_ITEM_EXISTS")

            case Event.SET_QUANTITY:
                if session.order_item is None:
                    raise ValueError("ORDER_ITEM_NOT_FOUND")
                if params.get("quantity", 0) <= 0:
                    raise ValueError("INVALID_QUANTITY")

            case Event.CANCEL_ORDER_ITEM:
                if session.order_item is None:
                    raise ValueError("ORDER_ITEM_NOT_FOUND")

            # 옵션 (필수/선택 통합: order_item만 있으면 자유선택)
            case Event.SELECT_REQUIRED_OPTION | Event.SELECT_OPTIONAL_OPTION:
                if session.order_item is None:
                    raise ValueError("ORDER_ITEM_NOT_FOUND")

            case Event.SKIP_OPTIONAL_OPTION:
                if session.order_item is None:
                    raise ValueError("ORDER_ITEM_NOT_FOUND")
                if session.order_item.status != OrderItemStatus.ASKING_OPTIONAL_OPTION:
                    raise ValueError("INVALID_ORDER_ITEM_STATE")

            case Event.SHOW_CART | Event.CLEAR_CART:
                return

            case (
                Event.REMOVE_CART_ITEM
                | Event.INCREASE_CART_ITEM
                | Event.DECREASE_CART_ITEM
            ):
                if not Validator._cart_item_exists_fsm_validator(
                    session, params.get("cart_item_id")
                ):
                    raise ValueError("CART_ITEM_NOT_FOUND")

            case Event.REQUEST_MENU_INFO:
                return

            case Event.CANCEL_SESSION:
                return

            case Event.EXPIRE_SESSION:
                if session is None:
                    raise ValueError("SESSION_NOT_FOUND")

            case _:
                return

    @staticmethod
    def _cart_item_exists_fsm_validator(
        session: Session,
        cart_item_id: Optional[int],
    ) -> bool:
        if cart_item_id is None:
            return False
        return any(
            cart_item.cart_item_id == cart_item_id
            for cart_item in session.cart
        )