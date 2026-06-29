from app.memory.session.orderItem import OrderItem
from app.memory.session.session import Session
from app.repository.menu.menuCrud import MenuCrud


class OrderController:

    @staticmethod
    async def create_order_item(
        session: Session,
        menu_id: int,
    ) -> None:
        """현재 주문(OrderItem) 생성"""

        # 메뉴 존재 여부 확인
        menu = await MenuCrud.get_menu_menu_menuCrud(menu_id)

        if menu is None:
            raise ValueError(f"Menu not found : {menu_id}")

        # 현재 주문 생성
        session.order_item = OrderItem(
            menu_id=menu_id,
        )