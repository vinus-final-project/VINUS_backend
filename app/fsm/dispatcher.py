"""FSM Dispatcher.

FSM Event를 받아 Controller를 실행하고 상태를 전이합니다.

동작 순서
1. 현재 FSM 상태 확인
2. Transition(허용 이벤트) 확인
3. 비-DB 선행조건 검증(validator)
4. Event → Controller 실행
5. 성공 시 FSM 상태 전이
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.fsm.event import Event, FSMEvent
from app.fsm.FSMstate import FSMState
from app.fsm.transition import TRANSITIONS
from app.fsm.validator import Validator
from app.memory.session.enums import OrderType
from app.memory.session.session import Session
from app.controllers.orderController import OrderController
from app.controllers.cartController import CartController
from app.controllers.systemController import SystemController
from app.controllers.paymentController import PaymentController


class Dispatcher:

    @staticmethod
    async def dispatch_fsm_dispatcher(
        db: AsyncSession,
        session: Optional[Session],
        fsm_event: FSMEvent,
    ) -> Optional[Session]:
        event = fsm_event.type
        params = fsm_event.parameters

        # 1. 현재 상태 (세션 없으면 INIT = SELECT_ORDER_TYPE 진입)
        current_state = (
            FSMState.INIT if session is None else session.fsm_state
        )

        # 2. 전이 허용 확인
        transitions = TRANSITIONS[current_state]
        if event not in transitions:
            raise ValueError(
                f"Invalid transition : {current_state} -> {event}"
            )
        next_state = transitions[event]

        # 3. 비-DB 선행조건 검증
        Validator.validate_fsm_validator(session, fsm_event)

        # 4. Event → Controller 실행 (세션 새로 생성되면 반환 세션 사용)
        session = await Dispatcher._execute_fsm_dispatcher(
            db=db,
            session=session,
            event=event,
            params=params,
        )

        # 5. 상태 전이
        if session is not None and next_state is not None:
            session.fsm_state = next_state

        return session

    @staticmethod
    async def _execute_fsm_dispatcher(
        db: AsyncSession,
        session: Optional[Session],
        event: Event,
        params: dict,
    ) -> Optional[Session]:
        match event:

            # ---------- 주문 유형 (B: 세션 생성 + 유형 설정) ----------
            case Event.SELECT_ORDER_TYPE:
                return await SystemController.create_session_controllers_systemController(
                    order_type=OrderType(params["order_type"]),
                )

            # ---------- 메뉴 / 수량 / 취소 ----------
            case Event.SELECT_MENU:
                await OrderController.create_order_item_controllers_orderController(
                    db=db, session=session, menu_id=params["menu_id"],
                )
            case Event.SET_QUANTITY:
                await OrderController.set_quantity_controllers_orderController(
                    session=session, quantity=params["quantity"],
                )
            case Event.CANCEL_ORDER_ITEM:
                await OrderController.cancel_order_item_controllers_orderController(
                    session,
                )

            # ---------- 옵션 추가 / 감소 (누적) ----------
            case Event.SELECT_OPTION:
                await OrderController.select_option_controllers_orderController(
                    session=session, option_id=params["option_id"],
                )
            case Event.DESELECT_OPTION:
                await OrderController.deselect_option_controllers_orderController(
                    session=session, option_id=params["option_id"],
                )

            # ---------- 옵션 종료(완료) → 카트 이동 ----------
            case Event.SKIP_OPTIONAL_OPTION:
                # 완료 검증(스냅샷 사용) → 카트로 이동(order_item 제거)
                await OrderController.complete_order_item_controllers_orderController(
                    session,
                )
                await CartController.add_to_cart_controllers_cartController(
                    session=session, order_item=session.order_item,
                )

            # ---------- 장바구니 ----------
            case Event.SHOW_CART:
                await CartController.get_cart_controllers_cartController(session)
            case Event.REMOVE_CART_ITEM:
                await CartController.remove_cart_item_controllers_cartController(
                    session=session, cart_item_id=params["cart_item_id"],
                )
            case Event.CLEAR_CART:
                await CartController.clear_cart_controllers_cartController(session)
            case Event.INCREASE_CART_ITEM:
                await CartController.increase_quantity_controllers_cartController(
                    session=session, cart_item_id=params["cart_item_id"],
                )
            case Event.DECREASE_CART_ITEM:
                await CartController.decrease_quantity_controllers_cartController(
                    session=session, cart_item_id=params["cart_item_id"],
                )

            # ---------- 메뉴 정보 ----------
            case Event.REQUEST_MENU_INFO:
                await SystemController.get_menu_info_controllers_systemController(
                    db=db, menu_id=params["menu_id"],
                )

            # ---------- 결제 시작 ----------
            case Event.START_PAYMENT:
                await PaymentController.start_payment_controllers_paymentController(
                    session,
                )

            # ---------- 결제 취소 ----------
            case Event.PAYMENT_CANCEL:
                await PaymentController.cancel_payment_controllers_paymentController(
                    session,
                )

            # ---------- 세션 종료 ----------
            case Event.CANCEL_SESSION:
                await SystemController.cancel_session_controllers_systemController(
                    session,
                )
            case Event.EXPIRE_SESSION:
                await SystemController.expire_session_controllers_systemController(
                    session,
                )

            # ---------- 결제완료/취소 · 추천: 타 담당 (미배선) ----------
            case _:
                raise NotImplementedError(f"Event not wired: {event}")

        return session