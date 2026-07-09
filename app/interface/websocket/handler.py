import json

from fastapi import WebSocket, WebSocketDisconnect

from app.ai.stt.whisperService import WhisperService
from app.interface.websocket.manager import manager
from app.interface.websocket.message import MessageType

# ──────────────────────────────────────────────────────────────
# handler — WebSocket 송수신 (명세서/WebSocket.md 메서드 명세)
#
#   receive_metadata() | VoiceRequest(JSON)  수신
#   receive_audio()    | PCM Binary Frame    수신 → STT 전달
#   send()             | SessionResponse / ErrorResponse 전송
#
# 현재 구현 단계:
#   [✓] JSON Metadata / BIND_SESSION 수신
#   [✓] PCM Binary → WhisperService(STT) → 한국어 텍스트
#   [ ] Normalizer(RapidFuzz) → RuleParser → RuleEngine(0 bytes, 미구현)
#       → EventExecutor → SessionResponse 송신
# ──────────────────────────────────────────────────────────────

# 너무 짧은 발화는 잡음일 가능성 — STT 스킵 기준 (0.3초 = 16000 * 0.3 * 2 bytes)
MIN_AUDIO_BYTES = 9600


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

            # ── JSON 메시지 ─────────────────────────────────
            if message.get("text") is not None:
                try:
                    payload = json.loads(message["text"])
                except json.JSONDecodeError:
                    pending_metadata = None
                    continue

                # (a) BIND_SESSION — 터치로 생성된 session_id 를
                #     이 연결에 매핑 (연결 보관 키 재지정)
                if payload.get("type") == MessageType.BIND_SESSION.value:
                    new_sid = payload.get("session_id")
                    if new_sid:
                        manager.bind_websocket_manager(key, new_sid)
                        key = new_sid
                    continue

                # (b) VoiceRequest JSON Metadata (다음 Binary 와 묶임)
                pending_metadata = payload
                # TODO(2차): pending_metadata 검증 (session_id, sample_rate 등)
                continue

            # ── PCM Binary Frame ────────────────────────────
            if message.get("bytes") is not None:
                audio: bytes = message["bytes"]
                meta = pending_metadata or {}
                pending_metadata = None

                # 잡음 가드: 0.3초 미만 발화는 스킵
                if len(audio) < MIN_AUDIO_BYTES:
                    continue

                # ① STT — PCM Binary → 한국어 텍스트
                text = await WhisperService.transcribe_stt_whisper(
                    audio, meta.get("sample_rate", 16000)
                )
                if not text:
                    continue

                # session_id: metadata 우선, 없으면 이 연결의 bind 키
                #   (anon-... 이면 아직 세션 없음 → None)
                sid = meta.get("session_id") or (
                    key if not key.startswith("anon-") else None
                )

                # ② TODO: Normalizer → RuleParser → RuleEngine → EventExecutor
                #   normalized = await Normalizer.normalize_rapidfuzz_normalizer(text)
                #   parsed = await RuleParser.parse_ruleengine_ruleparser(normalized)
                #   events = RuleEngine.???(parsed)          # ruleEngine.py 미구현
                #   result = await EventExecutor.execute_ruleEngine_eventExecutor(
                #       db=db, session=session_or_none, events=events)
                #   ③ 첫 발화(세션 생성)면: manager.bind_websocket_manager(key, result.session_id)
                #   ④ await manager.send_json_websocket_manager(result.session_id,
                #       result.model_dump(mode="json"))
                print(f"[WS] STT 결과 (session={sid}): {text}")
                continue
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_websocket_manager(key)
