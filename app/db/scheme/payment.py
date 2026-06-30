from pydantic import BaseModel, ConfigDict

class PaymentConfirmRequest(BaseModel):
    payment_key: str
    order_id: int
    amount: int

class PaymentConfirmResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    success: bool
    od_id: int
    od_state: str