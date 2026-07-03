from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.payment import PaymentConfirmRequest, PaymentConfirmResponse
from app.services.payment import Payment

router = APIRouter(prefix="/payments", tags=["Payments"])

# C - 결제 승인 요청 처리
@router.post("/confirm", response_model=PaymentConfirmResponse, status_code=status.HTTP_200_OK)
async def confirm_routers_paymentRouter(
    payment_data: PaymentConfirmRequest,
    db: AsyncSession = Depends(get_db)
):
    return await Payment.confirm_services_payment(
        db,
        payment_data.payment_key,
        payment_data.order_id,
        payment_data.amount
    )