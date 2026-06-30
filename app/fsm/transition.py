"""FSM 상태 전이 정의.

현재 FSM 상태에서 허용되는 Event와
Event 처리 후 변경될 다음 상태를 정의합니다.

조건 검증은 validator.py,
Controller 호출은 dispatcher.py에서 수행합니다.
"""

from app.fsm.event import Event
from app.fsm.FSMstate import FSMState


TRANSITIONS = {
    # ------------------------------------------------------------------
    # INIT
    # ------------------------------------------------------------------
    FSMState.INIT: {
        Event.SELECT_ORDER_TYPE: FSMState.ORDERING,
        Event.CANCEL_SESSION: None,
        Event.EXPIRE_SESSION: None,
    },

    # ------------------------------------------------------------------
    # ORDERING
    # ------------------------------------------------------------------
    FSMState.ORDERING: {
        Event.SELECT_MENU: FSMState.ORDERING,
        Event.SET_QUANTITY: FSMState.ORDERING,
        Event.CANCEL_ORDER_ITEM: FSMState.ORDERING,

        Event.SELECT_REQUIRED_OPTION: FSMState.ORDERING,
        Event.SELECT_OPTIONAL_OPTION: FSMState.ORDERING,
        Event.SKIP_OPTIONAL_OPTION: FSMState.ORDERING,

        Event.SHOW_CART: FSMState.ORDERING,
        Event.REMOVE_CART_ITEM: FSMState.ORDERING,
        Event.CLEAR_CART: FSMState.ORDERING,
        Event.INCREASE_CART_ITEM: FSMState.ORDERING,
        Event.DECREASE_CART_ITEM: FSMState.ORDERING,

        Event.REQUEST_RECOMMENDATION: FSMState.ORDERING,
        Event.ACCEPT_RECOMMENDATION: FSMState.ORDERING,

        Event.REQUEST_MENU_INFO: FSMState.ORDERING,

        Event.START_PAYMENT: FSMState.PAYMENT,

        Event.CANCEL_SESSION: None,
        Event.EXPIRE_SESSION: None,
    },

    # ------------------------------------------------------------------
    # PAYMENT
    # ------------------------------------------------------------------
    FSMState.PAYMENT: {
        Event.PAYMENT_SUCCESS: FSMState.COMPLETE,
        Event.PAYMENT_CANCEL: FSMState.ORDERING,

        Event.CANCEL_SESSION: None,
        Event.EXPIRE_SESSION: None,
    },

    # ------------------------------------------------------------------
    # COMPLETE
    # ------------------------------------------------------------------
    FSMState.COMPLETE: {},
}