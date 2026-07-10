"""SessionCrud : 세션 메모리 CRUD.

- SessionMemory(Map 저장소) 와 Session 객체에 대한 모든 CRUD 진입점
- Session 자체(생성/조회/수정/삭제) 와
  Session 내부 데이터(cart_item, log) 의 CRUD 를 모두 담당
- Controller / EventExecutor 등이 본 클래스의 정적 메서드를 호출

함수명 규칙 : `행위명_대상_폴더명(session)_파일명(sessionCrud)`
              파일명은 카멜케이스 그대로 사용.
메서드 순서 : C → R → U → D
"""

from typing import List, Optional
from uuid import uuid4
from collections import Counter

from app.memory.session.enums import (
    OrderItemStatus,
    SpeakerType,
    SessionStatus,
)
from app.memory.session.cartItem import CartItem, CartItemOption
from app.memory.session.orderItem import OrderItem
from app.memory.session.session import Log, Session
from app.memory.session.sessionMemory import SessionMemory



class SessionCrud:
    # -- 함수 정의 (CRUD: C → R → U → D) ------------------------------------

    # C - 새 Session 생성 후 메모리에 등록
    @staticmethod
    async def create_session_session_sessionCrud() -> Session:
        new_session_id = str(uuid4())

        while new_session_id in SessionMemory.sessions:
            new_session_id = str(uuid4())

        new_session = Session(session_id=new_session_id)
        SessionMemory.sessions[new_session_id] = new_session
        return new_session

    # ------------------------------------------------------------------
    # C - 카트에 주문 항목 추가
    #     카트 저장 규칙
    #       1) status == COMPLETE 일 때만 추가 가능
    #       2) 동일 메뉴 + 동일 옵션 → 기존 CartItem 의 수량 누적
    #       3) 그 외 → current_menu 스냅샷으로 이름/가격 조립해 신규 생성
    #          (누적 옵션은 개수를 세어 qty 로 압축, 가격은 op_price×개수)
    # ------------------------------------------------------------------
    @staticmethod
    async def add_cart_item_session_sessionCrud(
        session: Session,
        pending_item: OrderItem,
    ) -> None:
        # 1) COMPLETE 가 아니면 카트 추가 차단
        if pending_item.status != OrderItemStatus.COMPLETE:
            raise ValueError(
                "order_item.status 가 COMPLETE 일 때만 cart 에 추가할 수 있습니다."
            )

        # 2) 동일 메뉴 + 동일 옵션이면 수량만 누적
        for cart_item in session.cart:
            if (
                cart_item.menu_id == pending_item.menu_id
                and cart_item.selected_options == pending_item.selected_options
            ):
                cart_item.quantity += pending_item.quantity
                return

        # 3) 신규 CartItem 생성 — current_menu 스냅샷에서 이름/가격 조립
        menu = session.current_menu
        if menu is None:
            raise ValueError("Current menu not loaded.")

        options_detail: list[CartItemOption] = []
        option_price_sum = 0
        for og_id, op_ids in pending_item.selected_options.items():
            group = next(
                (g for g in menu["option_groups"] if g["og_id"] == og_id),
                None,
            )
            if group is None:
                continue

            # 같은 op_id 개수 세기 (누적 옵션 → qty)
            for op_id, qty in Counter(op_ids).items():
                op = next(
                    (o for o in group["options"] if o["op_id"] == op_id),
                    None,
                )
                if op is None:
                    continue
                options_detail.append(
                    CartItemOption(
                        op_id=op["op_id"],
                        op_name=op["op_name"],
                        op_price=op["op_price"],
                        qty=qty,
                    )
                )
                # 옵션 추가금 = 1개 가격 × 개수
                option_price_sum += op["op_price"] * qty

        # 1개당 가격 = 메뉴 가격 + 옵션 추가금 합(개수 반영)
        unit_price = menu["m_price"] + option_price_sum

        session.cart.append(
            CartItem(
                cart_item_id=session._next_cart_item_id,
                menu_id=pending_item.menu_id,
                menu_name=menu["m_name"],
                quantity=pending_item.quantity,
                unit_price=unit_price,
                selected_options=pending_item.selected_options.copy(),
                options=options_detail,
            )
        )
        session._next_cart_item_id += 1

    # C - 세션 로그 한 줄 추가
    @staticmethod
    async def create_log_session_sessionCrud(
        session: Session,
        speaker: SpeakerType,
        message: str,
        intent: Optional[str] = None,
    ) -> None:
        session.logs.append(
            Log(
                speaker=speaker,
                message=message,
                intent=intent,
            )
        )

    # R - Session 개별 조회 (없으면 KeyError)
    @staticmethod
    async def get_session_session_sessionCrud(
        session_id: str,
    ) -> Session:
        if session_id not in SessionMemory.sessions:
            raise KeyError(f"Session not found: {session_id}")

        return SessionMemory.sessions[session_id]

    # R - Session 전체 조회 (디버그/관리 용도)
    @staticmethod
    async def get_all_session_session_sessionCrud() -> List[Session]:
        return list(SessionMemory.sessions.values())

    # R - Session 존재 여부 확인
    @staticmethod
    async def exists_session_session_sessionCrud(
        session_id: str,
    ) -> bool:
        return session_id in SessionMemory.sessions

    # U - Session 갱신 (in-memory 이므로 사실상 참조 갱신/덮어쓰기)
    @staticmethod
    async def update_session_session_sessionCrud(
        session: Session,
    ) -> Session:
        SessionMemory.sessions[session.session_id] = session
        return session

    # U - Session 만료 처리
    @staticmethod
    async def expire_session_session_sessionCrud(
        session: Session,
    ) -> Session:
        session.session_status = SessionStatus.EXPIRED
        return session
    
    # D - Session 삭제 (메모리에서 완전 제거)
    @staticmethod
    async def delete_session_session_sessionCrud(
        session_id: str,
    ) -> None:
        # 이미 없어도 조용히 통과 (pop 기본값 None)
        SessionMemory.sessions.pop(session_id, None)

    # D - CartItem 삭제
    @staticmethod
    async def remove_cart_item_session_sessionCrud(
        session: Session,
        cart_item_id: int,
    ) -> None:
        for cart_item in session.cart:
            if cart_item.cart_item_id == cart_item_id:
                session.cart.remove(cart_item)
                return

        raise ValueError(
            f"CartItem not found: {cart_item_id}"
        )
    # U - CartItem 수량 증가 (+1)
    @staticmethod
    async def increase_cart_item_quantity_session_sessionCrud(
        session: Session,
        cart_item_id: int,
    ) -> None:
        for cart_item in session.cart:
            if cart_item.cart_item_id == cart_item_id:
                cart_item.quantity += 1
                return
        raise ValueError(f"CartItem not found: {cart_item_id}")

    # U - CartItem 수량 감소 (-1, 0이 되면 삭제)
    @staticmethod
    async def decrease_cart_item_quantity_session_sessionCrud(
        session: Session,
        cart_item_id: int,
    ) -> None:
        for cart_item in session.cart:
            if cart_item.cart_item_id == cart_item_id:
                cart_item.quantity -= 1
                if cart_item.quantity <= 0:
                    session.cart.remove(cart_item)
                return
        raise ValueError(f"CartItem not found: {cart_item_id}")

    # D - Cart 전체 삭제
    @staticmethod
    async def clear_cart_session_sessionCrud(
        session: Session,
    ) -> None:
        session.cart.clear()

    # (중복 정의였던 delete_session_session_sessionCrud 제거 —
    #  위쪽 "D - Session 삭제 (메모리에서 완전 제거)" 정의 하나만 유지)

    # D - 전체 Session 초기화 (테스트/디버그 전용)
    @staticmethod
    async def delete_all_session_sessionCrud() -> None:
        SessionMemory.sessions.clear()