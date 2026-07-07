# app/interface/dto/sttResult.py
from typing import Optional

from pydantic import BaseModel


class SttResult(BaseModel):
    # ===== 변수 선언 =====
    session_id: Optional[str] = None    # 세션 식별자 (첫 발화 시 None — 세션 생성 전)
    text: str                           # STT 변환 결과