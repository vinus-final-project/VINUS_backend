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
    #   - 수량 미지정(None) / 필수옵션 유무로 시작 상태 분기
    #   - current_menu 스냅샷 저장
    # ------------------------------------------------------------------
    @staticmethod
    async def create_order_item_controllers_orderController(
        db: AsyncSession,
        session: Session,
        menu_id: int,
    ) -> None:
        """OrderItem 생성"""

        if session.order_item is not None:
            raise ValueError("OrderItem already exists.")

        menu = await Menus.get_single_menu_detail_services_menus(
            db=db,
            m_id=menu_id,
        )

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
    # select_option : 옵션 선택 (필수/선택 구분 없이, 교체/토글)
    #   - 단일선택 그룹(og_max==1) : 교체 (같은 옵션 재선택 시 해제)
    #   - 다중선택 그룹(og_max>1)  : 토글 (있으면 제거 / 없으면 추가, 꽉차면 거절)
    #   - status 제한 없음 (order_item만 있으면 아무 옵션이나 자유선택)
    # ------------------------------------------------------------------
    @staticmethod
    async def select_option_controllers_orderController(
        session: Session,
        option_id: int,
    ) -> None:
        """옵션 선택 — 교체/토글 (필수·선택 자유선택)"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")

        menu = session.current_menu
        if menu is None:
            raise ValueError("Current menu not loaded.")

        group = OrderController._find_group_by_option(menu, option_id)
        if group is None:
            raise ValueError("Option not found.")

        og_id = group["og_id"]
        selected = session.order_item.selected_options.setdefault(og_id, [])

        if option_id in selected:
            # 이미 선택됨 → 해제(토글 오프)
            selected.remove(option_id)
        elif group["og_max"] == 1:
            # 단일선택 그룹 → 교체
            selected.clear()
            selected.append(option_id)
        else:
            # 다중선택 그룹 → 추가 (꽉 차면 거절)
            if len(selected) >= group["og_max"]:
                raise ValueError("Maximum selectable options exceeded.")
            selected.append(option_id)

        # 필수 그룹 전부 채워지면 다음 단계(선택옵션)로 상태 갱신
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
        """주문 수량 설정"""

        if session.order_item is None:
            raise ValueError("OrderItem not found.")
        if quantity < 1:
            raise ValueError("Quantity must be greater than 0.")

        session.order_item.quantity = quantity

    # ------------------------------------------------------------------
    # complete_order_item : 작성 완료 (필수/min/max + 수량 검증 후 COMPLETE)
    # ------------------------------------------------------------------
    @staticmethod
    async def complete_order_item_controllers_orderController(
        session: Session,
    ) -> None:
        """현재 주문(OrderItem) 작성 완료"""

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