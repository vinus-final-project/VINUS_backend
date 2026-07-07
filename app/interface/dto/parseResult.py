# app/interface/dto/parseResult.py
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ParseResult(BaseModel):
    # ===== 변수 선언 =====
    session_id: Optional[str] = None                   # 세션 식별자 (첫 발화 시 None — 세션 생성 전)
    intent: str                                        # ORDER / CART / PAYMENT / RECOMMEND / INFO / SESSION
    entities: Dict[str, Any] = Field(default_factory=dict)
    source: str = "RULE"                               # RULE / LLM