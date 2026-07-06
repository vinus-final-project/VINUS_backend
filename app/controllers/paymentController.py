from app.memory.session.session import Session


class PaymentController:

    # 결제 시작 검증 (ORDERING→PAYMENT 전이는 dispatcher가 처리)
    @staticmethod
    async def start_payment_controllers_paymentController(
        session: Session,
    ) -> None:
        """결제 시작 — 카트/주문 상태 검증"""

        # 장바구니 비었으면 결제 불가
        if not session.cart:
            raise ValueError("EMPTY_CART")

        # 작성 중인 주문이 남아있으면 결제 불가 (담거나 취소 먼저)
        if session.order_item is not None:
            raise ValueError("ORDER_ITEM_EXISTS")

        # 품절 검증: SoldOut 테이블이 프로젝트에서 제외되어 생략