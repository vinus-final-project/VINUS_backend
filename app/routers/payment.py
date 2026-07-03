from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_db
from app.db.scheme.payment import PaymentConfirmRequest, PaymentConfirmResponse
from app.services.payment import Payment

router = APIRouter(prefix="/payments", tags=["Payments"])


@router.post("/confirm", response_model=PaymentConfirmResponse, status_code=status.HTTP_200_OK)
async def confirm_routers_payment(
    payment_data: PaymentConfirmRequest,
    db: AsyncSession = Depends(get_db),
):
    return await Payment.confirm_services_payment(
        db=db,
        session_id=payment_data.session_id,
        order_id=payment_data.order_id,
        payment_key=payment_data.payment_key,
        amount=payment_data.amount,
    )