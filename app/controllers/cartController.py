from app.memory.session.session import Session
from app.memory.session.cartItem import CartItem
from app.memory.session.orderItem import OrderItem
from app.memory.session.sessionCrud import SessionCrud


class CartController:

    # ------------------------------------------------------------------
    # 내부 헬퍼 : cart_item_id 로 카트 항목 조회 (에코백 이름용, 없으면 None)
    # ------------------------------------------------------------------
    @staticmethod
    def _find_cart_item(session: Session, cart_item_id: int) -> CartItem | None:
        for ci in session.cart:
            if ci.cart_item_id == cart_item_id:
                return ci
        return None

    # 장바구니 조회 (Query)
    @staticmethod
    async def get_cart_controllers_cartController(
        session: Session,
    ) -> list[CartItem]:
        # 에코백 — 확인 + 다음 행동 안내 (터치/음성 공용)
        session.message = "장바구니 화면이에요. 주문 내역을 확인해주세요."
        return session.cart

    # 현재 OrderItem을 장바구니에 추가 + order_item 제거
    @staticmethod
    async def add_to_cart_controllers_cartController(
        session: Session,
        order_item: OrderItem,
    ) -> None:
        if order_item is None:
            raise ValueError("OrderItem not found.")

        # 에코백용 메뉴 이름 — 스냅샷 제거 전에 확보
        menu = session.current_menu
        menu_name = menu.get("m_name") if isinstance(menu, dict) else None

        # 카트 저장 규칙(COMPLETE 확인 / 동일메뉴+옵션 병합)은 sessionCrud가 담당
        await SessionCrud.add_cart_item_session_sessionCrud(
            session=session,
            pending_item=order_item,
        )
        session.order_item = None
        session.current_menu = None

        # 에코백 (터치/음성 공용)
        session.message = (
            f"{menu_name} 장바구니에 담았어요."
            if menu_name
            else "장바구니에 담았어요."
        )

    # 장바구니 항목 삭제 (없으면 CART_ITEM_NOT_FOUND)
    @staticmethod
    async def remove_cart_item_controllers_cartController(
        session: Session,
        cart_item_id: int,
    ) -> None:
        # 에코백용 이름 — 삭제 전에 확보
        ci = CartController._find_cart_item(session, cart_item_id)

        await SessionCrud.remove_cart_item_session_sessionCrud(
            session=session,
            cart_item_id=cart_item_id,
        )

        # 에코백 (터치/음성 공용)
        session.message = (
            f"{ci.menu_name} 뺐어요." if ci else "장바구니에서 뺐어요."
        )

    # 장바구니 전체 삭제
    @staticmethod
    async def clear_cart_controllers_cartController(
        session: Session,
    ) -> None:
        await SessionCrud.clear_cart_session_sessionCrud(session)

        # 에코백 (터치/음성 공용)
        session.message = "장바구니를 비웠어요."

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

        # 에코백 (터치/음성 공용) — 증가 후 수량 포함
        ci = CartController._find_cart_item(session, cart_item_id)
        if ci:
            session.message = f"{ci.menu_name} 하나 더 담았어요. {ci.quantity}개예요."

    # 수량 감소 (-1, 0이면 삭제)
    @staticmethod
    async def decrease_quantity_controllers_cartController(
        session: Session,
        cart_item_id: int,
    ) -> None:
        # 에코백용 이름 — 감소로 항목이 사라질 수 있어 먼저 확보
        before = CartController._find_cart_item(session, cart_item_id)

        await SessionCrud.decrease_cart_item_quantity_session_sessionCrud(
            session=session,
            cart_item_id=cart_item_id,
        )

        # 에코백 (터치/음성 공용) — 남았으면 수량, 사라졌으면 뺐다고 안내
        after = CartController._find_cart_item(session, cart_item_id)
        if after:
            session.message = f"{after.menu_name} 하나 뺐어요. {after.quantity}개예요."
        elif before:
            session.message = f"{before.menu_name} 뺐어요."