from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.crud.paymentCrud import PaymentCrud
from pydantic import BaseModel

router = APIRouter(prefix="/payments", tags=["Payments"])

# ✅ 요청 스키마
class PaymentResultRequest(BaseModel):
    session_id: str
    payment_status: str

# ✅ 응답 스키마
class PaymentResultResponse(BaseModel):
    success: bool


@router.post("/result")
async def payment_result_routers_paymentRouter(
    payment_data: PaymentResultRequest,
    db: AsyncSession = Depends(get_db)
) -> PaymentResultResponse:
    """
    결제 결과 콜백
    
    요청:
    {
        "session_id": "user-123-abc",
        "payment_status": "success"
    }
    
    응답:
    {
        "success": true
    }
    """
    
    # 1. 세션 ID로 주문 찾기
    order = await PaymentCrud.get_order_by_session_id_crud_paymentCrud(db, payment_data.session_id)
    
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 주문을 찾을 수 없습니다."
        )
    
    # 2. 결제 상태에 따라 주문 상태 업데이트
    if payment_data.payment_status.lower() == "success":
        # 결제 성공 → paid
        await PaymentCrud.update_order_status(db, order.od_id, "paid")
        return PaymentResultResponse(success=True)
    else:
        # 결제 실패 → cancelled
        await PaymentCrud.update_order_status(db, order.od_id, "cancelled")
        return PaymentResultResponse(success=False)