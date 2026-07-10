"""EventList DTO : Rule Engine/LLM → Event Executor.

Rule Engine 이 한 발화(턴)를 해석해 실행할 Event 목록과
사용자 정상 안내 문구(message)를 담아 넘긴다.
- message 는 '정상 안내'만 (에러 문구는 백엔드가 error_code 로 채움)
- 턴당 한 문자열 (이벤트별 아님)
"""

from typing import Optional

from pydantic import BaseModel, Field

from app.fsm.event import FSMEvent


class EventList(BaseModel):
    session_id: Optional[str] = None                        # 세션 식별자
    events: list[FSMEvent] = Field(default_factory=list)    # 실행할 Event 목록 (FIFO)
    message: Optional[str] = None                           # 정상 안내 문구 (턴당 1개, RuleEngine/LLM 작성)