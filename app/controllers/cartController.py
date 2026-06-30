from app.memory.session.session import Session
from app.memory.session.cartItem import CartItem
from app.memory.session.orderItem import OrderItem
from app.memory.session.sessionCrud import SessionCrud


class CartController:

    # 장바구니 조회 (Query)
    @staticmethod
    async def get_cart_controllers_cartController(
        session: Session,
    ) -> list[CartItem]:
        return session.cart

    # 현재 OrderItem을 장바구니에 추가 + order_item 제거
    @staticmethod
    async def add_to_cart_controllers_cartController(
        session: Session,
        order_item: OrderItem,
    ) -> None:
        if order_item is None:
            raise ValueError("OrderItem not found.")

        # 카트 저장 규칙(COMPLETE 확인 / 동일메뉴+옵션 병합)은 sessionCrud가 담당
        await SessionCrud.add_cart_item_session_sessionCrud(
            session=session,
            pending_item=order_item,
        )
        session.order_item = None

    # 장바구니 항목 삭제 (없으면 CART_ITEM_NOT_FOUND)
    @staticmethod
    async def remove_cart_item_controllers_cartController(
        session: Session,
        cart_item_id: int,
    ) -> None:
        await SessionCrud.remove_cart_item_session_sessionCrud(
            session=session,
            cart_item_id=cart_item_id,
        )

    # 장바구니 전체 삭제
    @staticmethod
    async def clear_cart_controllers_cartController(
        session: Session,
    ) -> None:
        await SessionCrud.clear_cart_session_sessionCrud(session)

    # 수량 증가 (+1)
    @staticmethod
    async def increase_quantity_controllers_cartController(
        session: Session,
        cart_item_id: int,
    ) -> None:
        await SessionCrud.increase_cart_item_quantity_session_sessionCrud(
            session=session,
            cart_item_id=cart_item_id,
        )

    # 수량 감소 (-1, 0이면 삭제)
    @staticmethod
    async def decrease_quantity_controllers_cartController(
        session: Session,
        cart_item_id: int,
    ) -> None:
        await SessionCrud.decrease_cart_item_quantity_session_sessionCrud(
            session=session,
            cart_item_id=cart_item_id,
        )