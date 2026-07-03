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
# ──────────────────────────────────────────────────────────────


class MessageType(str, Enum):
    VOICE_REQUEST_METADATA = "VOICE_REQUEST_METADATA"
    VOICE_REQUEST_AUDIO = "VOICE_REQUEST_AUDIO"
    SESSION_RESPONSE = "SESSION_RESPONSE"
    ERROR_RESPONSE = "ERROR_RESPONSE"
    PAYMENT_RESULT = "PAYMENT_RESULT"
