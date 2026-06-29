from sqlalchemy.ext.asyncio import AsyncSession

from app.services.menus import ServicesMenus
from app.memory.session.enums import OrderItemStatus
from app.memory.session.orderItem import OrderItem
from app.memory.session.session import Session


class OrderController:

    @staticmethod
    async def create_order_item_controllers_orderController(
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
        await ServicesMenus.get_single_menu_detail_services_menus(
            db=db,
            m_id=menu_id,
        )

        # --------------------------------------------------------------
        # OrderItem 생성
        # --------------------------------------------------------------
        session.order_item = OrderItem(
            menu_id=menu_id,
            status=OrderItemStatus.SELECTING_REQUIRED_OPTION,
        )

    @staticmethod
    async def set_quantity_controllers_orderController(
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



    @staticmethod
    async def select_required_option_controllers_orderController(
        db: AsyncSession,
        session: Session,
        og_id: int,
        op_id: int,
    ) -> None:
        """필수 옵션 선택"""

        # --------------------------------------------------------------
        # OrderItem 존재 여부 확인
        # --------------------------------------------------------------
        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        # --------------------------------------------------------------
        # 메뉴 조회
        # --------------------------------------------------------------
        menu = await ServicesMenus.get_single_menu_detail_services_menus(
            db=db,
            m_id=session.order_item.menu_id,
        )

        # --------------------------------------------------------------
        # 옵션 그룹 조회
        # --------------------------------------------------------------
        option_group = None

        for group in menu["option_groups"]:
            if group["og_id"] == og_id:
                option_group = group
                break

        if option_group is None:
            raise ValueError("OptionGroup not found.")

        # --------------------------------------------------------------
        # 필수 옵션 여부 확인
        # --------------------------------------------------------------
        if not option_group["og_required"]:
            raise ValueError("OptionGroup is not required.")

        # --------------------------------------------------------------
        # 옵션 존재 여부 확인
        # --------------------------------------------------------------
        option_exists = False

        for option in option_group["options"]:
            if option["op_id"] == op_id:
                option_exists = True
                break

        if not option_exists:
            raise ValueError("Option not found.")

        # --------------------------------------------------------------
        # 옵션 저장
        # --------------------------------------------------------------
        session.order_item.selected_options[og_id] = [op_id]

        # --------------------------------------------------------------
        # 모든 필수 옵션 선택 여부 확인
        # --------------------------------------------------------------
        completed = True

        for group in menu["option_groups"]:

            if not group["og_required"]:
                continue

            if group["og_id"] not in session.order_item.selected_options:
                completed = False
                break

        # --------------------------------------------------------------
        # 상태 변경
        # --------------------------------------------------------------
        if completed:
            session.order_item.status = (
                OrderItemStatus.ASKING_OPTIONAL_OPTION
            )

    @staticmethod
    async def select_optional_option_controllers_orderController(
        db: AsyncSession,
        session: Session,
        og_id: int,
        op_id: int,
    ) -> None:
        """선택 옵션 선택"""

        # --------------------------------------------------------------
        # OrderItem 존재 여부 확인
        # --------------------------------------------------------------
        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        # --------------------------------------------------------------
        # 메뉴 조회
        # --------------------------------------------------------------
        menu = await ServicesMenus.get_single_menu_detail_services_menus(
            db=db,
            m_id=session.order_item.menu_id,
        )

        # --------------------------------------------------------------
        # 옵션 그룹 조회
        # --------------------------------------------------------------
        option_group = None

        for group in menu["option_groups"]:
            if group["og_id"] == og_id:
                option_group = group
                break

        if option_group is None:
            raise ValueError("OptionGroup not found.")

        # --------------------------------------------------------------
        # 선택 옵션 여부 확인
        # --------------------------------------------------------------
        if option_group["og_required"]:
            raise ValueError("OptionGroup is required.")

        # --------------------------------------------------------------
        # 옵션 존재 여부 확인
        # --------------------------------------------------------------
        option_exists = False

        for option in option_group["options"]:
            if option["op_id"] == op_id:
                option_exists = True
                break

        if not option_exists:
            raise ValueError("Option not found.")

        # --------------------------------------------------------------
        # 선택 옵션 저장
        # --------------------------------------------------------------
        selected_options = session.order_item.selected_options.setdefault(
            og_id,
            [],
        )

        if op_id in selected_options:
            raise ValueError("Option already selected.")

        if len(selected_options) >= option_group["og_max"]:
            raise ValueError("Maximum selectable options exceeded.")

        selected_options.append(op_id)

    @staticmethod
    async def complete_order_item_controllers_orderController(
        session: Session,
    ) -> None:
        """현재 주문(OrderItem) 작성 완료"""

        # --------------------------------------------------------------
        # OrderItem 존재 여부 확인
        # --------------------------------------------------------------
        if session.order_item is None:
            raise ValueError("OrderItem not found.")
        
        # --------------------------------------------------------------
        # 필수 옵션 선택 여부 확인
        # --------------------------------------------------------------
        for option_group in ServicesMenus["option_groups"]:

            if not option_group["og_required"]:
                continue

            if (
                option_group["og_id"]
                not in session.order_item.selected_options
            ):
                raise ValueError(
                    f"Required option group not selected : {option_group['og_name']}"
                )


        # --------------------------------------------------------------
        # 주문 수량 확인
        # --------------------------------------------------------------
        if session.order_item.quantity is None:
            raise ValueError("Quantity not selected.")

        # --------------------------------------------------------------
        # 작성 완료 처리
        # --------------------------------------------------------------
        session.order_item.status = OrderItemStatus.COMPLETE

    @staticmethod
    async def cancel_order_item_controllers_orderController(
        session: Session,
    ) -> None:
        """현재 주문(OrderItem) 취소"""

        # --------------------------------------------------------------
        # OrderItem 존재 여부 확인
        # --------------------------------------------------------------
        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        # --------------------------------------------------------------
        # OrderItem 삭제
        # --------------------------------------------------------------
        session.order_item = None