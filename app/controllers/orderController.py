from fastapi import HTTPException
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
    #   - 상태는 IN_PROGRESS 로 시작 (필수/선택 구분 없이 옵션 자유선택)
    #   - current_menu 스냅샷 저장
    # ------------------------------------------------------------------
    @staticmethod
    async def create_order_item_controllers_orderController(
        db: AsyncSession,
        session: Session,
        menu_id: int,
    ) -> None:
        """OrderItem 생성 (IN_PROGRESS 상태로 시작)"""

        # 이미 작성 중인 주문이 있으면 차단
        if session.order_item is not None:
            raise ValueError("ORDER_ITEM_EXISTS")

        # 메뉴 조회 (존재 확인)
        #   - 서비스가 404(HTTPException) → 표준 코드 MENU_NOT_FOUND 로 변환
        try:
            menu = await Menus.get_single_menu_detail_services_menus(
                db=db,
                m_id=menu_id,
            )
        except HTTPException:
            raise ValueError("MENU_NOT_FOUND")

        session.order_item = OrderItem(
            menu_id=menu_id,
            quantity=1,
            status=OrderItemStatus.IN_PROGRESS,
        )
        session.current_menu = menu  # 메뉴 스냅샷 저장

    # ------------------------------------------------------------------
    # select_option : 옵션 추가 (+1, 누적)
    #   - 단일선택 그룹(og_max==1) : 교체 (온도/사이즈 등)
    #   - 다중/누적 그룹(og_max>1)  : 같은 옵션 중복 허용(개수+1), 총 개수 ≤ og_max
    # ------------------------------------------------------------------
    @staticmethod
    async def select_option_controllers_orderController(
        session: Session,
        option_id: int,
    ) -> None:
        """옵션 추가 (+1)"""

        # OrderItem 존재 확인
        if session.order_item is None:
            raise ValueError("ORDER_ITEM_NOT_FOUND")

        # 메뉴 스냅샷 확인 (없으면 내부 상태 이상 → 방어)
        menu = session.current_menu
        if menu is None:
            raise ValueError("INVALID_STATE")

        # 옵션이 속한 그룹 역추적
        group = OrderController._find_group_by_option(menu, option_id)
        if group is None:
            raise ValueError("OPTION_NOT_FOUND")

        og_id = group["og_id"]
        selected = session.order_item.selected_options.setdefault(og_id, [])

        if group["og_max"] == 1:
            # 단일선택 그룹 → 교체 (개수 개념 없음)
            selected.clear()
            selected.append(option_id)
        else:
            # 다중/누적 그룹 → 개수 +1 (그룹 총 개수가 og_max 미만일 때만)
            if len(selected) >= group["og_max"]:
                raise ValueError("OPTION_LIMIT_EXCEEDED")
            selected.append(option_id)  # 중복 허용 = 누적

    # ------------------------------------------------------------------
    # deselect_option : 옵션 감소 (-1)
    #   - 해당 옵션 한 개만 제거 (없으면 무시)
    # ------------------------------------------------------------------
    @staticmethod
    async def deselect_option_controllers_orderController(
        session: Session,
        option_id: int,
    ) -> None:
        """옵션 감소 (-1, 한 개만 제거)"""

        # OrderItem 존재 확인
        if session.order_item is None:
            raise ValueError("ORDER_ITEM_NOT_FOUND")

        # 메뉴 스냅샷 확인 (없으면 내부 상태 이상 → 방어)
        menu = session.current_menu
        if menu is None:
            raise ValueError("INVALID_STATE")

        # 옵션이 속한 그룹 역추적
        group = OrderController._find_group_by_option(menu, option_id)
        if group is None:
            raise ValueError("OPTION_NOT_FOUND")

        og_id = group["og_id"]
        selected = session.order_item.selected_options.get(og_id, [])

        # 한 개만 제거 (없으면 무시)
        if option_id in selected:
            selected.remove(option_id)

    # ------------------------------------------------------------------
    # set_quantity : 주문 수량 설정 (언제든 변경 가능)
    # ------------------------------------------------------------------
    @staticmethod
    async def set_quantity_controllers_orderController(
        session: Session,
        quantity: int,
    ) -> None:
        """주문 수량 설정"""

        # OrderItem 존재 확인
        if session.order_item is None:
            raise ValueError("ORDER_ITEM_NOT_FOUND")
        # 수량 유효성 (1개 이상)
        if quantity < 1:
            raise ValueError("INVALID_QUANTITY")

        # 수량은 값만 갱신
        session.order_item.quantity = quantity

    # ------------------------------------------------------------------
    # complete_order_item : 작성 완료 (개수 기준 필수/min/max 검증)
    # ------------------------------------------------------------------
    @staticmethod
    async def complete_order_item_controllers_orderController(
        session: Session,
    ) -> None:
        """현재 주문(OrderItem) 작성 완료"""

        # OrderItem 존재 확인
        if session.order_item is None:
            raise ValueError("ORDER_ITEM_NOT_FOUND")

        # 메뉴 스냅샷 확인 (없으면 내부 상태 이상 → 방어)
        menu = session.current_menu
        if menu is None:
            raise ValueError("INVALID_STATE")

        # 옵션 그룹별 검증 (count = 중복 포함 개수)
        for group in menu["option_groups"]:
            og_id = group["og_id"]
            count = len(session.order_item.selected_options.get(og_id, []))

            # 필수 그룹 미선택
            if group["og_required"] and count == 0:
                raise ValueError("REQUIRED_OPTION_MISSING")
            # 선택된 그룹은 개수 min/max 검사
            if count > 0:
                if count < group["og_min"]:
                    raise ValueError("OPTION_MIN_NOT_MET")
                if count > group["og_max"]:
                    raise ValueError("OPTION_LIMIT_EXCEEDED")

        session.order_item.status = OrderItemStatus.COMPLETE

    # ------------------------------------------------------------------
    # cancel_order_item : 현재 주문 취소
    # ------------------------------------------------------------------
    @staticmethod
    async def cancel_order_item_controllers_orderController(
        session: Session,
    ) -> None:
        """현재 주문(OrderItem) 취소"""

        # OrderItem 존재 확인
        if session.order_item is None:
            raise ValueError("ORDER_ITEM_NOT_FOUND")

        # OrderItem + 메뉴 스냅샷 제거
        session.order_item = None
        session.current_menu = None