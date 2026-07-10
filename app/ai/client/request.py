from pydantic import BaseModel
from typing import Optional


class SessionStateRequest(BaseModel):
    """AI 서버로 전달할 세션 상태"""
    se_id: str
    fsm_state: Optional[str] = None
    order_type: Optional[str] = None
    order_item: Optional[dict] = None
    cart: Optional[list] = None


class LLMRequest(BaseModel):
    """AI 서버 요청 DTO"""
    session: SessionStateRequest
    query: str
    context: Optional[str] = ""