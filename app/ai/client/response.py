from pydantic import BaseModel
from typing import List


class FSMEventResponse(BaseModel):
    """AI 서버에서 받은 FSM 이벤트"""
    type: str
    parameters: dict = {}


class LLMResponse(BaseModel):
    """AI 서버 응답 DTO"""
    result: str                       # LLM 자연어 응답 원문
    events: List[FSMEventResponse] = []  # FSM 이벤트 목록 (없으면 빈 리스트)
    response: str                     # Android에 전달할 안내 문구
    source: str = "LLM"               # 처리 출처