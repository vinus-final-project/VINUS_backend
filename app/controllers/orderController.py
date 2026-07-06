from sqlalchemy.ext.asyncio import AsyncSession

from app.services.menus import Menus
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
    #   - 수량은 미지정(None) → set_quantity 에서 입력
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
        menu = await Menus.get_single_menu_detail_services_menus(
            db=db,
            m_id=menu_id,
        )

        # 필수 옵션 그룹이 있으면 필수옵션 단계,
        # 없으면 바로 선택옵션 단계로 시작
        has_required = any(
            group["og_required"] for group in menu["option_groups"]
        )
        initial_status = (
            OrderItemStatus.SELECTING_REQUIRED_OPTION
            if has_required
            else OrderItemStatus.ASKING_OPTIONAL_OPTION
        )

        session.order_item = OrderItem(
            menu_id=menu_id,
            status=initial_status,
        )
        session.current_menu = menu                 


    # ------------------------------------------------------------------
    # select_required_option : 필수 옵션 선택
    #   → 모든 필수 그룹이 채워지면 status=ASKING_OPTIONAL_OPTION
    # ------------------------------------------------------------------
    @staticmethod   
    async def select_required_option_controllers_orderController(
        session: Session,
        option_id: int,
    ) -> None:
        """필수 옵션 선택 (메뉴는 세션 스냅샷 사용)"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        menu = session.current_menu
        if menu is None:
            raise ValueError("Current menu not loaded.")

        group = OrderController._find_group_by_option(menu, option_id)
        if group is None:
            raise ValueError("Option not found.")

        if not group["og_required"]:
            raise ValueError("OptionGroup is not required.")

        og_id = group["og_id"]
        selected = session.order_item.selected_options.setdefault(og_id, [])

        if option_id in selected:
            raise ValueError("Option already selected.")
        if len(selected) >= group["og_max"]:
            raise ValueError("Maximum selectable options exceeded.")

        selected.append(option_id)

        # 모든 필수 그룹이 채워지면 다음 단계(선택옵션)로
        all_required_selected = True
        for g in menu["option_groups"]:
            if not g["og_required"]:
                continue
            if not session.order_item.selected_options.get(g["og_id"]):
                all_required_selected = False
                break

        if all_required_selected:
            session.order_item.status = OrderItemStatus.ASKING_OPTIONAL_OPTION

    # ------------------------------------------------------------------
    # set_quantity : 주문 수량 설정 (언제든 변경 가능, status 변경 없음)
    # ------------------------------------------------------------------
    @staticmethod
    async def set_quantity_controllers_orderController(
        session: Session,
        quantity: int,
    ) -> None:
        """주문 수량 설정 (언제든 변경 가능, status 변경 없음)"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")
        if quantity < 1:
            raise ValueError("Quantity must be greater than 0.")

        # 수량은 값만 갱신 — 흐름 단계에 영향 없음
        session.order_item.quantity = quantity

    # ------------------------------------------------------------------
    # select_optional_option : 선택 옵션 선택 (og_max 까지 누적, 상태 유지)
    # ------------------------------------------------------------------
    @staticmethod
    async def select_optional_option_controllers_orderController(
        session: Session,
        option_id: int,
    ) -> None:
        """선택 옵션 선택 (메뉴는 세션 스냅샷 사용)"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        if session.order_item.status != OrderItemStatus.ASKING_OPTIONAL_OPTION:
            raise ValueError("Invalid order item state.")

        menu = session.current_menu
        if menu is None:
            raise ValueError("Current menu not loaded.")

        group = OrderController._find_group_by_option(menu, option_id)
        if group is None:
            raise ValueError("Option not found.")

        if group["og_required"]:
            raise ValueError("OptionGroup is required.")

        og_id = group["og_id"]
        selected = session.order_item.selected_options.setdefault(og_id, [])

        if option_id in selected:
            raise ValueError("Option already selected.")
        if len(selected) >= group["og_max"]:
            raise ValueError("Maximum selectable options exceeded.")

        selected.append(option_id)

    # ------------------------------------------------------------------
    # complete_order_item : 작성 완료 (필수/min/max + 수량 검증 후 COMPLETE)
    # ------------------------------------------------------------------
    @staticmethod
    async def complete_order_item_controllers_orderController(
        session: Session,
    ) -> None:
        """작성 완료 (메뉴는 세션 스냅샷 사용, 필수/min/max + 수량 검증)"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        menu = session.current_menu
        if menu is None:
            raise ValueError("Current menu not loaded.")

        for group in menu["option_groups"]:
            og_id = group["og_id"]
            count = len(session.order_item.selected_options.get(og_id, []))

            if group["og_required"] and count == 0:
                raise ValueError(
                    f"Required option group not selected : {group['og_name']}"
                )
            if count > 0:
                if count < group["og_min"]:
                    raise ValueError(f"Option min not met : {group['og_name']}")
                if count > group["og_max"]:
                    raise ValueError(f"Option limit exceeded : {group['og_name']}")

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
        session.current_menu = None       