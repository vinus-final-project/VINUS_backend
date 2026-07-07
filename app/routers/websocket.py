from fastapi import APIRouter, WebSocket

from app.interface.websocket.handler import handle_websocket_handler

router = APIRouter(tags=["WebSocket"])

# ──────────────────────────────────────────────────────────────
# /ws/voice — 음성 주문 세션 WebSocket 라우터
#
# 라우터는 endpoint 정의만 하고, 실제 송수신/연결 관리는
# app/interface/websocket (handler / manager / message) 에 위임한다.
#
#   - session_id 는 optional query param (세션 발급 전에도 연결 가능)
#   - 1차 배포: 연결 수락 + 유지 (음성 파이프라인은 2차)
# ──────────────────────────────────────────────────────────────


@router.websocket("/ws/voice")
async def voice_websocket_routers_websocket(
    websocket: WebSocket,
    session_id: str | None = None,  # ?session_id=... (optional)
):
    await handle_websocket_handler(websocket, session_id)