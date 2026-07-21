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
        # 에코백 — 카트 내용 낭독 (화면을 볼 수 없는 사용자용).
        #   음성 "장바구니 보여줘"(SHOW_CART 이벤트)에서만 발동 —
        #   터치 카트 진입은 REST 를 안 부르므로 PageGuide 문구가 담당.
        if not session.cart:
            session.message = "장바구니가 비어 있어요. 주문하실 메뉴를 말씀해주세요."
            return session.cart

        # 항목 낭독 — 단위(음료 잔/디저트 개)는 ruleEngine 메뉴 메타 캐시 재사용
        from app.ai.ruleEngine.ruleEngine import RuleEngine
        parts = []
        for ci in session.cart[:5]:
            unit = RuleEngine.menu_unit_cached_ruleEngine_ruleEngine(ci.menu_id)
            parts.append(f"{ci.menu_name} {ci.quantity}{unit}")
        rest = len(session.cart) - 5
        listed = ", ".join(parts) + (f" 외 {rest}가지" if rest > 0 else "")

        total = sum(ci.unit_price * ci.quantity for ci in session.cart)
        session.message = (
            f"장바구니에 {listed}, 합계 {total:,}원이에요. "
            "결제하시려면 결제, 빼시려면 메뉴 이름과 함께 빼줘라고 말씀해주세요."
        )
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

        # 에코백 (터치/음성 공용) — 확인 + 다음 행동 안내
        #   (눈 감고 쓰는 사용자는 다음에 뭘 말해야 하는지 알 수 없음)
        base = (
            f"{menu_name} 장바구니에 담았어요."
            if menu_name
            else "장바구니에 담았어요."
        )
        session.message = (
            base + " 계속 주문하시려면 메뉴 이름을, "
            "결제하시려면 결제라고 말씀해주세요."
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

        # 에코백 (터치/음성 공용) — 증가 후 수량 포함 (단위: 잔/개)
        ci = CartController._find_cart_item(session, cart_item_id)
        if ci:
            from app.ai.ruleEngine.ruleEngine import RuleEngine
            unit = RuleEngine.menu_unit_cached_ruleEngine_ruleEngine(ci.menu_id)
            josa = "이에요" if unit == "잔" else "예요"
            session.message = (
                f"{ci.menu_name} 하나 더 담았어요. {ci.quantity}{unit}{josa}."
            )

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

        # 에코백 (터치/음성 공용) — 남았으면 수량(단위: 잔/개), 사라졌으면 뺐다고 안내
        after = CartController._find_cart_item(session, cart_item_id)
        if after:
            from app.ai.ruleEngine.ruleEngine import RuleEngine
            unit = RuleEngine.menu_unit_cached_ruleEngine_ruleEngine(after.menu_id)
            josa = "이에요" if unit == "잔" else "예요"
            session.message = (
                f"{after.menu_name} 하나 뺐어요. {after.quantity}{unit}{josa}."
            )
        elif before:
            session.message = f"{before.menu_name} 뺐어요."