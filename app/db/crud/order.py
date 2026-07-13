from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload


from app.db.models.orders import Orders, OdState
from app.db.models.orderMenus import OrderMenus
from app.db.models.orderMenuOptions import OrderMenuOptions
from app.db.models.sessions import Sessions, SessionStatus, SeCarry
from app.db.models.sessionLogs import SessionLogs, SpeakerType
from app.memory.session.session import Session


class Order:
    """결제 완료 주문 영속화 (메모리 카트 → DB)"""

    # ------------------------------------------------------------------
    # C - 결제 완료 주문 저장 (한 트랜잭션)
    #     메모리 카트 → orders / orderMenus / orderMenuOptions
    #                 + sessions / sessionLogs
    #     누적 옵션(qty>1)은 orderMenuOptions 에 개수만큼 행을 생성한다.
    # ------------------------------------------------------------------
    @staticmethod
    async def save_paid_order_crud_order(
        db: AsyncSession,
        session: Session,
        payment_key: str,
        total_price: int,
    ) -> int:
        # 1) sessions (부모) — orders FK가 참조하므로 먼저 저장
        db_session = Sessions(
            se_id=session.session_id,
            se_status=SessionStatus.COMPLETED,
            se_carry=(
                SeCarry(session.order_type.value)
                if session.order_type is not None
                else None
            ),
            se_started_at=session.created_at,
            se_ended_at=datetime.now(),
        )
        db.add(db_session)

        # 2) orders — 주문번호(od_no) 발급 후 저장
        result = await db.execute(select(func.max(Orders.od_no)))
        next_od_no = (result.scalar() or 0) + 1

        db_order = Orders(
            se_id=session.session_id,
            od_price=total_price,
            od_state=OdState.PAID,
            od_no=next_od_no,
            pa_key=payment_key,
        )
        db.add(db_order)
        await db.flush()   # od_id 확보

        # 3) orderMenus + orderMenuOptions (카트 항목별)
        for cart_item in session.cart:
            db_order_menu = OrderMenus(
                od_id=db_order.od_id,
                m_id=cart_item.menu_id,
                o_m_qty=cart_item.quantity,
            )
            db.add(db_order_menu)
            await db.flush()   # o_m_id 확보

            # 옵션 — 누적 개수(qty)만큼 행 생성
            for opt in cart_item.options:
                for _ in range(opt.qty):
                    db.add(
                        OrderMenuOptions(
                            o_m_id=db_order_menu.o_m_id,
                            op_id=opt.op_id,
                        )
                    )

        # 4) sessionLogs (로그 버퍼 flush)
        for log in session.logs:
            db.add(
                SessionLogs(
                    se_id=session.session_id,
                    sl_speaker=SpeakerType(log.speaker.value),
                    sl_message=log.message,
                    sl_intent=log.intent,
                )
            )

        await db.commit()
        return db_order.od_id
    
    # ------------------------------------------------------------------
    # R - 영수증 출력용 주문 조회 (메뉴/옵션/세션 관계 즉시 로드)
    #     결제 직후 자동 출력 + /payments/receipt 재출력 공용.
    # ------------------------------------------------------------------
    @staticmethod
    async def get_paid_order_crud_order(
        db: AsyncSession,
        od_id: int,
    ) -> Orders | None:
        result = await db.execute(
            select(Orders)
            .options(
                selectinload(Orders.session),
                selectinload(Orders.order_menus).selectinload(OrderMenus.menu),
                selectinload(Orders.order_menus)
                .selectinload(OrderMenus.order_menu_options)
                .selectinload(OrderMenuOptions.option),
            )
            .where(Orders.od_id == od_id)
        )
        return result.scalar_one_or_none()
 