from pydantic import BaseModel, ConfigDict
from typing import Optional
from enum import Enum
from datetime import datetime


class SpeakerType(str, Enum):
    AI = "AI"
    SYSTEM = "SYSTEM"
    USER = "USER"


class SessionLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    sl_id: int
    se_id: str
    sl_speaker: SpeakerType
    sl_message: str
    sl_intent: Optional[str] = None
    sl_created_at: datetime