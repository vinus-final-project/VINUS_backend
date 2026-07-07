import json

from fastapi import WebSocket, WebSocketDisconnect

from app.interface.websocket.manager import manager

# ──────────────────────────────────────────────────────────────
# handler — WebSocket 송수신 (명세서/WebSocket.md 메서드 명세)
#
#   receive_metadata() | VoiceRequest(JSON)  수신
#   receive_audio()    | PCM Binary Frame    수신 → STT 전달
#   send()             | SessionResponse / ErrorResponse 전송
#
# 1차 배포: 연결 수락 + 수신 소비만 (음성 파이프라인은 2차)
#
# 2차에서 구현할 흐름:
#   1) receive_metadata → sample_rate/channels/session_id 보관
#   2) receive_audio    → 직후 도착하는 PCM Binary 를 동일 요청으로 묶어
#                         VoicePipeline(STT → RapidFuzz → Rule → FSM) 전달
#   3) send             → 처리 결과 SessionResponse 를 frontend 로 송신
# ──────────────────────────────────────────────────────────────


async def handle_websocket_handler(
    websocket: WebSocket, session_id: str | None = None
) -> None:
    """/ws/voice 연결 1개의 전체 생명주기 처리."""
    key = await manager.connect_websocket_manager(websocket, session_id)
    # 마지막으로 수신한 JSON Metadata (다음 Binary Frame 과 묶임)
    pending_metadata: dict | None = None

    try:
        while True:
            message = await websocket.receive()

            if message.get("type") == "websocket.disconnect":
                break

            # ── JSON Metadata (VoiceRequest) ────────────────
            if message.get("text") is not None:
                try:
                    pending_metadata = json.loads(message["text"])
                except json.JSONDecodeError:
                    pending_metadata = None
                # TODO(2차): pending_metadata 검증 (session_id, sample_rate 등)
                continue

            # ── PCM Binary Frame ────────────────────────────
            if message.get("bytes") is not None:
                # TODO(2차): pending_metadata + bytes → VoicePipeline 전달
                #   result = await voice_pipeline(pending_metadata, message["bytes"])
                #   await manager.send_json_websocket_manager(sid, result)
                pending_metadata = None
                continue
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_websocket_manager(key)
