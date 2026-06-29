from app.memory.session.session import Session
from app.memory.session.sessionCrud import SessionCrud


class CartController:

    @staticmethod
    async def add_cart_item_controllers_cartController(
        session: Session,
    ) -> None:
        """현재 OrderItem을 Cart에 추가"""

        # --------------------------------------------------------------
        # OrderItem 존재 여부 확인
        # --------------------------------------------------------------
        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        # --------------------------------------------------------------
        # Cart 추가
        # --------------------------------------------------------------
        await SessionCrud.add_cart_item_session_sessionCrud(
            session=session,
            pending_item=session.order_item,
        )

        # --------------------------------------------------------------
        # OrderItem 제거
        # --------------------------------------------------------------
        session.order_item = None