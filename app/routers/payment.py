from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.payment import SchemePaymentConfirmRequest, SchemePaymentConfirmResponse
from app.services.payment import Payment

router = APIRouter(prefix="/payments", tags=["Payments"])

@router.post("/confirm", response_model=SchemePaymentConfirmResponse, status_code=status.HTTP_200_OK)
async def confirm_routers_paymentRouter(
    payment_data: SchemePaymentConfirmRequest,
    db: AsyncSession = Depends(get_db)
):
    return await Payment.confirm_services_payment(
        db,
        payment_data.payment_key,
        payment_data.order_id,
        payment_data.amount
    )