from enum import Enum

# ──────────────────────────────────────────────────────────────
# WebSocket Message Type (명세서/WebSocket.md 메시지 정의)
#
#   Message Type            | 전송 방식     | 송신       | 수신
#   ----------------------- | ------------ | ---------- | ------
#   VOICE_REQUEST_METADATA  | JSON         | Android    | Server
#   VOICE_REQUEST_AUDIO     | Binary(PCM)  | Android    | Server
#   SESSION_RESPONSE        | JSON         | Server     | Android
#   ERROR_RESPONSE          | JSON         | Server     | Android
#   PAYMENT_RESULT          | JSON         | 결제 모듈   | Server
#   BIND_SESSION            | JSON         | Android    | Server
#
#   BIND_SESSION: 터치 흐름으로 세션이 생성된 경우(POST /sessions),
#   이미 열려있는 WS 연결(anon)에 그 session_id 를 매핑하기 위해
#   frontend 가 보내는 제어 메시지.
#     { "type": "BIND_SESSION", "session_id": "<uuid>" }
#
#   UTTER_END: 발화 종료(EP) 마커. frontend Noise Gate 가 발화 청크를
#   실시간 스트리밍하다가 게이트가 닫히면 보낸다. backend 는
#   metadata~UTTER_END 사이 Binary 를 누적해 발화 하나로 확정한다.
#     { "type": "UTTER_END" }
# ──────────────────────────────────────────────────────────────


class MessageType(str, Enum):
    VOICE_REQUEST_METADATA = "VOICE_REQUEST_METADATA"
    VOICE_REQUEST_AUDIO = "VOICE_REQUEST_AUDIO"
    SESSION_RESPONSE = "SESSION_RESPONSE"
    ERROR_RESPONSE = "ERROR_RESPONSE"
    PAYMENT_RESULT = "PAYMENT_RESULT"
    BIND_SESSION = "BIND_SESSION"
    UTTER_END = "UTTER_END"
