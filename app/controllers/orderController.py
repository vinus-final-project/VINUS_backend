from sqlalchemy.ext.asyncio import AsyncSession

from app.db.crud.menuCrud import CrudMenus
from app.memory.session.enums import OrderItemStatus
from app.memory.session.orderItem import OrderItem
from app.memory.session.session import Session


class OrderController:

    @staticmethod
    async def create_order_item(
        db: AsyncSession,
        session: Session,
        menu_id: int,
    ) -> None:
        """현재 주문(OrderItem) 생성"""

        # --------------------------------------------------------------
        # 이미 작성 중인 주문이 있는지 확인
        # --------------------------------------------------------------
        if session.order_item is not None:
            raise ValueError("OrderItem already exists.")

        # --------------------------------------------------------------
        # 메뉴 조회
        # --------------------------------------------------------------
        menu = await CrudMenus.get_menu_detail_crud_menuCrud(
            db=db,
            m_id=menu_id,
        )

        # --------------------------------------------------------------
        # 메뉴 존재 여부 확인
        # --------------------------------------------------------------
        if menu is None:
            raise ValueError(f"Menu not found: {menu_id}")

        # --------------------------------------------------------------
        # OrderItem 생성
        # --------------------------------------------------------------
        session.order_item = OrderItem(
            menu_id=menu_id,
            status=OrderItemStatus.SELECTING_REQUIRED_OPTION,
        )

    @staticmethod
    async def set_quantity(
        session: Session,
        quantity: int,
    ) -> None:
        """주문 수량 설정"""

        # --------------------------------------------------------------
        # OrderItem 존재 확인
        # --------------------------------------------------------------
        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        # --------------------------------------------------------------
        # 수량 유효성 확인
        # --------------------------------------------------------------
        if quantity < 1:
            raise ValueError("Quantity must be greater than 0.")

        # --------------------------------------------------------------
        # 수량 설정
        # --------------------------------------------------------------
        session.order_item.quantity = quantity