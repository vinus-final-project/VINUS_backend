import json

from fastapi import WebSocket, WebSocketDisconnect

from app.ai.pipeline.voicePipeline import VoicePipeline
from app.ai.vad.vadService import filter_utterance_vad_vadService
from app.db.database import AsyncSessionLocal
from app.memory.session.sessionCrud import SessionCrud
from app.interface.websocket.manager import manager
from app.interface.websocket.message import MessageType

# ──────────────────────────────────────────────────────────────
# handler — WebSocket 송수신 (명세서/WebSocket.md 메서드 명세)
#
# 구조 (노이즈게이트 + 청킹 + 실시간 스트리밍):
#   frontend Noise Gate 가 발화 경계를 판정하면서 청크를 즉시 보낸다.
#     SP(게이트 열림)  → VoiceRequest metadata(JSON)
#     speaking 동안    → PCM Binary 청크 연속 수신 (실시간)
#     EP(게이트 닫힘)  → UTTER_END 마커(JSON)
#   backend 는 metadata~UTTER_END 사이 Binary 를 누적해 발화 하나로
#   확정 → VAD 검증/트리밍 → VoicePipeline.
#
# 수신 처리:
#   JSON  BIND_SESSION      → 이 연결에 session_id 매핑
#   JSON  VoiceRequest meta → 발화 시작. 누적 버퍼 초기화 (+미확정분 선확정)
#   Binary PCM 청크          → 누적 버퍼에 추가
#   JSON  UTTER_END         → 발화 확정 → VAD 검증 → 파이프라인
#
# 현재 구현 단계:
#   [✓] BIND_SESSION / metadata / UTTER_END 수신
#   [✓] 발화 확정 → VAD 검증(filter) → VoicePipeline
#       (STT → RapidFuzz → RuleParser → RuleEngine → EventExecutor)
#   [✓] SessionResponse 송신 + 첫 발화 세션 생성 시 연결 재바인딩
# ──────────────────────────────────────────────────────────────

# 발화 누적 상한 (30초 = 16000Hz * 2bytes * 30s) — UTTER_END 유실 등 방어
MAX_UTTER_BYTES = 960_000


async def handle_websocket_handler(
    websocket: WebSocket, session_id: str | None = None
) -> None:
    """/ws/voice 연결 1개의 전체 생명주기 처리."""
    key = await manager.connect_websocket_manager(websocket, session_id)

    # 이 연결의 발화 스트림 상태
    pending_meta: dict = {"sample_rate": 16000, "channels": 1}
    audio_buf: list[bytes] = []   # metadata~UTTER_END 사이 Binary 누적

    async def process_utterance() -> None:
        """누적된 발화를 확정하고 VAD 검증 → 파이프라인 → 응답 송신."""
        nonlocal key
        if not audio_buf:
            return
        pcm = b"".join(audio_buf)
        audio_buf.clear()

        # ① VAD 검증 + 앞뒤 무음 트리밍
        #    (게이트는 데시벨만 보므로 비음성 잡음 세그먼트 걸러냄)
        utterance = filter_utterance_vad_vadService(pcm)
        if utterance is None:
            return

        # ② session_id: metadata 우선, 없으면 이 연결의 bind 키
        sid = pending_meta.get("session_id") or (
            key if not key.startswith("anon-") else None
        )

        # ③ 메모리 세션 조회 (첫 발화 전이면 None → INIT 취급)
        session = None
        if sid:
            try:
                session = await SessionCrud.get_session_session_sessionCrud(sid)
            except KeyError:
                session = None

        # ④ VoicePipeline — STT → RapidFuzz → RuleParser
        #    → RuleEngine → EventExecutor → SessionResponse
        #    (WS 는 Depends 불가 → DB 세션 직접 생성)
        try:
            async with AsyncSessionLocal() as db:
                result = await VoicePipeline.process_pipeline_voicePipeline(
                    db=db,
                    session=session,
                    pcm_bytes=utterance,
                    sample_rate=pending_meta.get("sample_rate", 16000),
                )
        except Exception as exc:
            # 내부 오류 — 연결은 유지하고 다음 발화 계속 수신
            print(f"[WS] 파이프라인 오류 (session={sid}): {exc}")
            return

        # ⑤ 첫 발화로 세션이 생성된 경우 — 연결 키 재바인딩
        if result.session_id and result.session_id != key:
            manager.bind_websocket_manager(key, result.session_id)
            key = result.session_id

        # ⑥ SessionResponse 송신 (이 연결로 직접 전송)
        await websocket.send_json(result.model_dump(mode="json"))

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

                msg_type = payload.get("type")

                # (a) BIND_SESSION — 터치로 생성된 session_id 를
                #     이 연결에 매핑 (연결 보관 키 재지정)
                if msg_type == MessageType.BIND_SESSION.value:
                    new_sid = payload.get("session_id")
                    if new_sid:
                        manager.bind_websocket_manager(key, new_sid)
                        key = new_sid
                    continue

                # (b) UTTER_END — 발화 종료(EP) → 누적분 확정 처리
                if msg_type == MessageType.UTTER_END.value:
                    await process_utterance()
                    continue

                # (c) PAYMENT_RESULT — 결제는 REST(/payments/confirm)로 처리
                if msg_type == MessageType.PAYMENT_RESULT.value:
                    continue

                # (d) VoiceRequest metadata — 발화 시작(SP)
                #     UTTER_END 유실 대비: 미확정 누적분이 있으면 먼저 확정
                if audio_buf:
                    await process_utterance()
                pending_meta.update(payload)
                continue

            # ── PCM Binary 청크 (SP~EP 사이 실시간 스트리밍) ─
            if message.get("bytes") is not None:
                audio_buf.append(message["bytes"])
                # 상한 방어: UTTER_END 유실 등으로 무한 누적 방지
                if sum(len(b) for b in audio_buf) > MAX_UTTER_BYTES:
                    await process_utterance()
                continue
    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect_websocket_manager(key)
