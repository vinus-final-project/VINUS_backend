import json

from fastapi import WebSocket, WebSocketDisconnect

from app.ai.stt.whisperService import WhisperService
from app.ai.vad.vadService import VadSegmenter
from app.interface.websocket.manager import manager
from app.interface.websocket.message import MessageType

# ──────────────────────────────────────────────────────────────
# handler — WebSocket 송수신 (명세서/WebSocket.md 메서드 명세)
#
# frontend 는 마이크 PCM(16kHz mono Int16)을 "연속 스트림"으로 보낸다.
# VAD(발화 구간 분리)는 backend 의 VadSegmenter 가 수행한다.
#
# 수신 처리:
#   JSON  BIND_SESSION      → 이 연결에 session_id 매핑
#   JSON  스트림 metadata    → sample_rate/channels/session_id 보관
#   Binary PCM 청크          → VadSegmenter.feed → 발화 완성 시 STT
#
# 현재 구현 단계:
#   [✓] BIND_SESSION / 스트림 metadata 수신
#   [✓] 연속 PCM → VAD 세그먼트 → WhisperService(STT) → 한국어 텍스트
#   [ ] Normalizer(RapidFuzz) → RuleParser → RuleEngine(미구현)
#       → EventExecutor → SessionResponse 송신
# ──────────────────────────────────────────────────────────────


async def handle_websocket_handler(
    websocket: WebSocket, session_id: str | None = None
) -> None:
    """/ws/voice 연결 1개의 전체 생명주기 처리."""
    key = await manager.connect_websocket_manager(websocket, session_id)

    # 이 연결의 스트림 파라미터 (frontend metadata 로 갱신)
    stream_meta: dict = {"sample_rate": 16000, "channels": 1}

    # 이 연결 전용 VAD 세그먼터 (연속 PCM → 발화 구간 분리)
    segmenter = VadSegmenter()

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
                    continue

                # (a) BIND_SESSION — 터치로 생성된 session_id 를
                #     이 연결에 매핑 (연결 보관 키 재지정)
                if payload.get("type") == MessageType.BIND_SESSION.value:
                    new_sid = payload.get("session_id")
                    if new_sid:
                        manager.bind_websocket_manager(key, new_sid)
                        key = new_sid
                    continue

                # (b) 스트림 metadata — 최신 값으로 갱신
                stream_meta.update(payload)
                continue

            # ── PCM Binary 청크 (연속 스트림) ────────────────
            if message.get("bytes") is not None:
                # VAD: 청크를 세그먼터에 밀어넣고, 완성된 발화만 STT 로
                for utterance in segmenter.feed_vad_vadService(message["bytes"]):
                    # ① STT — 발화 PCM → 한국어 텍스트
                    text = await WhisperService.transcribe_stt_whisper(
                        utterance, stream_meta.get("sample_rate", 16000)
                    )
                    if not text:
                        continue

                    # session_id: metadata 우선, 없으면 이 연결의 bind 키
                    sid = stream_meta.get("session_id") or (
                        key if not key.startswith("anon-") else None
                    )

                    # ② TODO: Normalizer → RuleParser → RuleEngine → EventExecutor
                    #   normalized = await Normalizer.normalize_rapidfuzz_normalizer(text)
                    #   parsed = await RuleParser.parse_ruleengine_ruleparser(normalized)
                    #   events = RuleEngine.???(parsed)          # ruleEngine.py 미구현
                    #   result = await EventExecutor.execute_ruleEngine_eventExecutor(
                    #       db=db, session=session_or_none, events=events)
                    #   ③ 첫 발화(세션 생성)면:
                    #       manager.bind_websocket_manager(key, result.session_id)
                    #   ④ await manager.send_json_websocket_manager(
                    #       result.session_id, result.model_dump(mode="json"))
                    print(f"[WS] STT 결과 (session={sid}): {text}")
                continue
    except WebSocketDisconnect:
        pass
    finally:
        segmenter.reset_vad_vadService()
        manager.disconnect_websocket_manager(key)
