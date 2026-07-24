from typing import Optional

from pydantic import BaseModel, ConfigDict


# 결제 승인 요청 (프론트 → confirm)
class PaymentConfirmRequest(BaseModel):
    session_id: str      # 메모리 세션 조회용
    order_id: str        # 프론트가 토스 창에 쓴 orderId (session_id + suffix)
    payment_key: str     # 토스가 발급한 paymentKey
    amount: int          # 위변조 검증용 금액


# 결제 승인 응답
class PaymentConfirmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    success: bool
    od_id: int
    od_state: str
    od_no: int
    payment: Optional[dict] = None   # 토스 confirm 응답 원본 (영수증용, 프론트 전달만)