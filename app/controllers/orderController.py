from sqlalchemy.ext.asyncio import AsyncSession

from app.services.menus import ServicesMenus
from app.memory.session.enums import OrderItemStatus
from app.memory.session.orderItem import OrderItem
from app.memory.session.session import Session


class OrderController:

    # ------------------------------------------------------------------
    # 내부 헬퍼 : option_id 가 속한 옵션 그룹을 메뉴 상세에서 역추적
    # ------------------------------------------------------------------
    @staticmethod
    def _find_group_by_option(menu: dict, option_id: int) -> dict | None:
        for group in menu["option_groups"]:
            for option in group["options"]:
                if option["op_id"] == option_id:
                    return group
        return None

    # ------------------------------------------------------------------
    # create_order_item : 현재 주문(OrderItem) 생성
    #   - 수량은 미지정(None) → set_quantity 에서 반드시 입력
    #   - 필수옵션 유무로 시작 상태 분기
    # ------------------------------------------------------------------
    @staticmethod
    async def create_order_item_controllers_orderController(
        db: AsyncSession,
        session: Session,
        menu_id: int,
    ) -> None:
        """OrderItem 생성 (수량 미지정 / 필수옵션 유무로 시작 상태 분기)"""

        # 이미 작성 중인 주문이 있으면 차단
        if session.order_item is not None:
            raise ValueError("OrderItem already exists.")

        # 메뉴 조회 (존재 확인 + 필수옵션 유무 판단)
        menu = await ServicesMenus.get_single_menu_detail_services_menus(
            db=db,
            m_id=menu_id,
        )

        # 필수 옵션 그룹이 하나라도 있으면 필수옵션 단계,
        # 없으면 바로 수량 단계로 시작
        has_required = any(
            group["og_required"] for group in menu["option_groups"]
        )
        initial_status = (
            OrderItemStatus.SELECTING_REQUIRED_OPTION
            if has_required
            else OrderItemStatus.SELECTING_QUANTITY
        )

        # OrderItem 생성
        session.order_item = OrderItem(
            menu_id=menu_id,
            status=initial_status,
        )

    # ------------------------------------------------------------------
    # select_required_option : 필수 옵션 선택
    #   → 모든 필수 그룹이 채워지면 status=SELECTING_QUANTITY
    # ------------------------------------------------------------------
    @staticmethod
    async def select_required_option_controllers_orderController(
        db: AsyncSession,
        session: Session,
        option_id: int,
    ) -> None:
        """필수 옵션 선택"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        menu = await ServicesMenus.get_single_menu_detail_services_menus(
            db=db,
            m_id=session.order_item.menu_id,
        )

        # 옵션이 속한 그룹 역추적
        group = OrderController._find_group_by_option(menu, option_id)
        if group is None:
            raise ValueError("Option not found.")

        # 필수 그룹인지 확인
        if not group["og_required"]:
            raise ValueError("OptionGroup is not required.")

        og_id = group["og_id"]
        selected = session.order_item.selected_options.setdefault(og_id, [])

        if option_id in selected:
            raise ValueError("Option already selected.")
        if len(selected) >= group["og_max"]:
            raise ValueError("Maximum selectable options exceeded.")

        selected.append(option_id)

        # 모든 필수 그룹이 1개 이상 선택되면 다음 단계(수량)로
        all_required_selected = True
        for g in menu["option_groups"]:
            if not g["og_required"]:
                continue
            if not session.order_item.selected_options.get(g["og_id"]):
                all_required_selected = False
                break

        if all_required_selected:
            session.order_item.status = OrderItemStatus.SELECTING_QUANTITY

    # ------------------------------------------------------------------
    # set_quantity : 주문 수량 설정 → status=ASKING_OPTIONAL_OPTION
    # ------------------------------------------------------------------
    @staticmethod
    async def set_quantity_controllers_orderController(
        session: Session,
        quantity: int,
    ) -> None:
        """주문 수량 설정"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")
        if quantity < 1:
            raise ValueError("Quantity must be greater than 0.")

        session.order_item.quantity = quantity
        session.order_item.status = OrderItemStatus.ASKING_OPTIONAL_OPTION

    # ------------------------------------------------------------------
    # select_optional_option : 선택 옵션 선택 (og_max 까지 누적, 상태 유지)
    # ------------------------------------------------------------------
    @staticmethod
    async def select_optional_option_controllers_orderController(
        db: AsyncSession,
        session: Session,
        option_id: int,
    ) -> None:
        """선택 옵션 선택"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        # FSM 조건: status == ASKING_OPTIONAL_OPTION
        if session.order_item.status != OrderItemStatus.ASKING_OPTIONAL_OPTION:
            raise ValueError("Invalid order item state.")

        menu = await ServicesMenus.get_single_menu_detail_services_menus(
            db=db,
            m_id=session.order_item.menu_id,
        )

        group = OrderController._find_group_by_option(menu, option_id)
        if group is None:
            raise ValueError("Option not found.")

        # 선택(비필수) 그룹인지 확인
        if group["og_required"]:
            raise ValueError("OptionGroup is required.")

        og_id = group["og_id"]
        selected = session.order_item.selected_options.setdefault(og_id, [])

        if option_id in selected:
            raise ValueError("Option already selected.")
        if len(selected) >= group["og_max"]:
            raise ValueError("Maximum selectable options exceeded.")

        selected.append(option_id)
        # 상태는 ASKING_OPTIONAL_OPTION 유지 (확정은 complete_order_item)

    # ------------------------------------------------------------------
    # complete_order_item : 작성 완료 (필수/min/max 검증 후 COMPLETE)
    # ------------------------------------------------------------------
    @staticmethod
    async def complete_order_item_controllers_orderController(
        db: AsyncSession,
        session: Session,
    ) -> None:
        """현재 주문(OrderItem) 작성 완료"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        menu = await ServicesMenus.get_single_menu_detail_services_menus(
            db=db,
            m_id=session.order_item.menu_id,
        )

        # OrderItem 완료 시 검증 (REQUIRED / MIN / MAX)
        for group in menu["option_groups"]:
            og_id = group["og_id"]
            count = len(session.order_item.selected_options.get(og_id, []))

            if group["og_required"] and count == 0:
                raise ValueError(
                    f"Required option group not selected : {group['og_name']}"
                )
            if count > 0:
                if count < group["og_min"]:
                    raise ValueError(
                        f"Option min not met : {group['og_name']}"
                    )
                if count > group["og_max"]:
                    raise ValueError(
                        f"Option limit exceeded : {group['og_name']}"
                    )

        # 수량 입력 여부 확인 (반드시 set_quantity 를 거쳐야 함)
        if session.order_item.quantity is None:
            raise ValueError("Quantity not selected.")

        session.order_item.status = OrderItemStatus.COMPLETE

    # ------------------------------------------------------------------
    # cancel_order_item : 현재 주문 취소
    # ------------------------------------------------------------------
    @staticmethod
    async def cancel_order_item_controllers_orderController(
        session: Session,
    ) -> None:
        """현재 주문(OrderItem) 취소"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        session.order_item = None