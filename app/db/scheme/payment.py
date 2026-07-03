from pydantic import BaseModel, ConfigDict

# payment_key 대신 session_id를 받도록 전면 교체
class PaymentConfirmRequest(BaseModel):
    session_id: str     # 프론트엔드 키오스크 세션 ID
    amount: int         # 위변조 검증용 금액

class PaymentConfirmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    success: bool
    od_id: int
    od_state: str