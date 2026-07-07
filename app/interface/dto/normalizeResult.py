# app/interface/dto/normalizeResult.py
from typing import Optional

from pydantic import BaseModel


class NormalizeResult(BaseModel):
    # ===== 변수 선언 =====
    session_id: Optional[str] = None    # 세션 식별자 (첫 발화 시 None — 세션 생성 전)
    text: str                           # 보정된 텍스트