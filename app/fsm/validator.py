"""FSM Event Validator.

FSM Event 실행 가능 여부를 검증합니다.

- 현재 FSM 상태
- Session 상태
- Event별 실행 조건

을 검사하며, 실패 시 예외를 발생시킵니다.
"""

from app.fsm.event import Event
from app.memory.session.session import Session


class Validator:

    @staticmethod
    def validate_fsm_validator(
        session: Session,
        event: Event,
    ) -> None:
        """Event 실행 가능 여부 검증"""

        match event:

            case Event.SELECT_ORDER_TYPE:
                Validator._validate_select_order_type(session)

            case Event.SELECT_MENU:
                Validator._validate_select_menu(session)

            case Event.SET_QUANTITY:
                Validator._validate_set_quantity(session)

            case Event.CANCEL_ORDER_ITEM:
                Validator._validate_cancel_order_item(session)

            case Event.SELECT_REQUIRED_OPTION:
                Validator._validate_select_required_option(session)

            case Event.SELECT_OPTIONAL_OPTION:
                Validator._validate_select_optional_option(session)

            case Event.SKIP_OPTIONAL_OPTION:
                Validator._validate_skip_optional_option(session)

            case Event.SHOW_CART:
                Validator._validate_show_cart(session)

            case Event.REMOVE_CART_ITEM:
                Validator._validate_remove_cart_item(session)

            case Event.CLEAR_CART:
                Validator._validate_clear_cart(session)

            case Event.INCREASE_CART_ITEM:
                Validator._validate_increase_cart_item(session)

            case Event.DECREASE_CART_ITEM:
                Validator._validate_decrease_cart_item(session)

            case Event.REQUEST_RECOMMENDATION:
                Validator._validate_request_recommendation(session)

            case Event.ACCEPT_RECOMMENDATION:
                Validator._validate_accept_recommendation(session)

            case Event.REQUEST_MENU_INFO:
                Validator._validate_request_menu_info(session)

            case Event.START_PAYMENT:
                Validator._validate_start_payment(session)

            case Event.PAYMENT_SUCCESS:
                Validator._validate_payment_success(session)

            case Event.PAYMENT_CANCEL:
                Validator._validate_payment_cancel(session)

            case Event.CANCEL_SESSION:
                return

            case Event.EXPIRE_SESSION:
                return