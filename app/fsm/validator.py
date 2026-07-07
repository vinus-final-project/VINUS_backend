"""FSM Event Validator (비-DB 검증).

transition 표(상태 전이)와 별개로, 세션 데이터/파라미터 수준의
선행 조건을 검사합니다. 메뉴/옵션/품절 등 DB 의존 검증은 Controller 담당.
실패 시 ValueError(에러코드 문자열) 발생.
"""

from typing import Optional

from app.fsm.event import Event, FSMEvent
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

            # 주문 유형: 세션 데이터 선행조건 없음 (상태는 transition 표)
            case Event.SELECT_ORDER_TYPE:
                return

            # 메뉴 선택: order_item 이 비어 있어야 함
            case Event.SELECT_MENU:
                if session.order_item is not None:
                    raise ValueError("ORDER_ITEM_EXISTS")

            # 수량: order_item 존재 + quantity > 0
            case Event.SET_QUANTITY:
                if session.order_item is None:
                    raise ValueError("ORDER_ITEM_NOT_FOUND")
                if params.get("quantity", 0) <= 0:
                    raise ValueError("INVALID_QUANTITY")

            # 현재 주문 취소: order_item 존재
            case Event.CANCEL_ORDER_ITEM:
                if session.order_item is None:
                    raise ValueError("ORDER_ITEM_NOT_FOUND")

            # 옵션 추가/감소: order_item 만 있으면 자유선택 (필수/선택 구분 없음)
            case Event.SELECT_OPTION | Event.DESELECT_OPTION:
                if session.order_item is None:
                    raise ValueError("ORDER_ITEM_NOT_FOUND")

            # 옵션 종료(완료): order_item 존재만 확인
            #   - 필수 미완료 검증은 complete_order_item 에서 REQUIRED_OPTION_MISSING 처리
            case Event.SKIP_OPTIONAL_OPTION:
                if session.order_item is None:
                    raise ValueError("ORDER_ITEM_NOT_FOUND")

            # 장바구니 조회 / 비우기: 선행조건 없음
            case Event.SHOW_CART | Event.CLEAR_CART:
                return

            # 장바구니 항목 조작: cart_item 존재
            case (
                Event.REMOVE_CART_ITEM
                | Event.INCREASE_CART_ITEM
                | Event.DECREASE_CART_ITEM
            ):
                if not Validator._cart_item_exists_fsm_validator(
                    session, params.get("cart_item_id")
                ):
                    raise ValueError("CART_ITEM_NOT_FOUND")

            # 메뉴 정보 조회: 메뉴 존재는 Controller 검증
            case Event.REQUEST_MENU_INFO:
                return

            # 세션 취소: 조건 없음
            case Event.CANCEL_SESSION:
                return

            # 세션 만료: session 존재
            case Event.EXPIRE_SESSION:
                if session is None:
                    raise ValueError("SESSION_NOT_FOUND")

            # 결제 / 추천 등: 타 담당 (미검증 통과)
            case _:
                return

    # ------------------------------------------------------------------
    # 내부 헬퍼 : cart_item_id 가 카트에 존재하는지
    # ------------------------------------------------------------------
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