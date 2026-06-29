"""SessionMemory : 세션 인메모리 저장소.

- Session 객체를 RAM에 보관하는 Map 저장소입니다.
- CRUD 로직은 sessionCrud.py에서 수행합니다.
"""

from typing import Dict

from app.memory.session.session import Session


class SessionMemory:
    sessions: Dict[str, Session] = {}