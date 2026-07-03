from fastapi import WebSocket

# ──────────────────────────────────────────────────────────────
# ConnectionManager — WebSocket 연결 관리 (명세서/WebSocket.md)
#
#   connect()    | 연결 수락 + 보관
#   disconnect() | 연결 제거
#   send_json()  | 특정 session 으로 JSON 전송 (SessionResponse 등)
#   bind()       | 연결 후 발급된 session_id 를 기존 연결에 매핑
#
# 연결 보관:
#   session_id → WebSocket (session_id 미발급 연결은 id(ws) 키로 임시 보관)
# ──────────────────────────────────────────────────────────────


class ConnectionManager:
    def __init__(self) -> None:
        self._connections: dict[str, WebSocket] = {}

    async def connect_websocket_manager(
        self, websocket: WebSocket, session_id: str | None = None
    ) -> str:
        """연결 수락 후 보관. 반환값은 보관 키."""
        await websocket.accept()
        key = session_id or f"anon-{id(websocket)}"
        self._connections[key] = websocket
        return key

    def bind_websocket_manager(self, old_key: str, session_id: str) -> None:
        """세션 발급 전(anon) 연결을 session_id 키로 재매핑."""
        ws = self._connections.pop(old_key, None)
        if ws is not None:
            self._connections[session_id] = ws

    def disconnect_websocket_manager(self, key: str) -> None:
        self._connections.pop(key, None)

    async def send_json_websocket_manager(self, session_id: str, payload: dict) -> bool:
        """해당 세션 연결로 JSON 전송 (SessionResponse / ErrorResponse)."""
        ws = self._connections.get(session_id)
        if ws is None:
            return False
        await ws.send_json(payload)
        return True


# 앱 전역 싱글턴
manager = ConnectionManager()
