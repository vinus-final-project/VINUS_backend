import json

from fastapi import WebSocket, WebSocketDisconnect

from app.ai.pipeline.voicePipeline import VoicePipeline
from app.ai.vad.vadService import VadSegmenter, filter_utterance_vad_vadService
from app.db.database import AsyncSessionLocal
from app.memory.session.sessionCrud import SessionCrud
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
#   [✓] 연속 PCM → VAD 세그먼트 → VoicePipeline
#       (STT → RapidFuzz → RuleParser → RuleEngine → EventExecutor)
#   [✓] SessionResponse 송신 + 첫 발화 세션 생성 시 연결 재바인딩
# ──────────────────────────────────────────────────────────────


async def handle_websocket_handler(
    websocket: WebSocket, session_id: str | None = None
) -> None:
    """/ws/voice 연결 1개의 전체 생명주기 처리."""
    key = await manager.connect_websocket_manager(websocket, session_id)

    # 이 연결의 스트림 파라미터 (frontend metadata 로 갱신)
    stream_meta: dict = {"sample_rate": 16000, "channels": 1}
    tts_active = {"on": False}   # 프론트 TTS_STATE — 재생 중이면 에코 필터 적용

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

                # (b) PAYMENT_RESULT — 결제는 REST(/payments/confirm)로 처리.
                #     stream_meta 오염 방지를 위해 무시
                if payload.get("type") == MessageType.PAYMENT_RESULT.value:
                    continue

                # (b-2) TTS_STATE — 스피커 재생 중 플래그 (자기 에코 필터용)
                if payload.get("type") == "TTS_STATE":
                    tts_active["on"] = bool(payload.get("active"))
                    continue

                # (c) 스트림 metadata — 최신 값으로 갱신
                stream_meta.update(payload)
                continue

            # ── PCM Binary 청크 (연속 스트림) ────────────────
            if message.get("bytes") is not None:
                # VAD: 청크를 세그먼터에 밀어넣고, 완성된 발화만 파이프라인으로
                for utterance in segmenter.feed_vad_vadService(message["bytes"]):
                    # 앞뒤 무음/제로 패딩 제거 + 실음성 재검증
                    #   (제거 안 하면 발화 꼬리의 무음에서 Whisper 가 환각 문구 생성)
                    utterance = filter_utterance_vad_vadService(utterance)
                    if utterance is None:
                        continue
                    # ① session_id: metadata 우선, 없으면 이 연결의 bind 키
                    sid = stream_meta.get("session_id") or (
                        key if not key.startswith("anon-") else None
                    )

                    # ② 메모리 세션 조회 (첫 발화 전이면 None → INIT 취급)
                    session = None
                    if sid:
                        try:
                            session = await SessionCrud.get_session_session_sessionCrud(sid)
                        except KeyError:
                            session = None

                    # ③ VoicePipeline — STT → RapidFuzz → RuleParser
                    #    → RuleEngine → EventExecutor → SessionResponse
                    #    (WS 는 Depends 불가 → DB 세션 직접 생성)
                    try:
                        async with AsyncSessionLocal() as db:
                            result = await VoicePipeline.process_pipeline_voicePipeline(
                                db=db,
                                session=session,
                                tts_active=tts_active["on"],
                                pcm_bytes=utterance,
                                sample_rate=stream_meta.get("sample_rate", 16000),
                            )
                    except Exception as exc:
                        # 내부 오류 — 연결은 유지하고 다음 발화 계속 수신
                        print(f"[WS] 파이프라인 오류 (session={sid}): {exc}")
                        continue

                    # 환각 필터로 폐기된 발화 — 응답 없이 다음 발화 대기
                    if result is None:
                        continue

                    # ④ 첫 발화로 세션이 생성된 경우 — 연결 키 재바인딩
                    if result.session_id and result.session_id != key:
                        manager.bind_websocket_manager(key, result.session_id)
                        key = result.session_id

                    # ⑤ SessionResponse 송신 (이 연결로 직접 전송)
                    await websocket.send_json(result.model_dump(mode="json"))
                continue
    except WebSocketDisconnect:
        pass
    finally:
        segmenter.reset_vad_vadService()
        manager.disconnect_websocket_manager(key)