# WebSocket 명세서

WebSocket 처리 명세

| 항목 | 내용 |
| --- | --- |
| 역할 | Android와 Backend 간 양방향 통신 |
| 프로토콜 | WebSocket |
| 통신 방식 | Full-Duplex |
| 연결 주체 | Android(Client) ↔ Python(Server) |
| 요청 데이터 형식 | JSON Metadata + PCM Binary Frame |
| 응답 데이터 형식 | JSON |
| 음성 전송 | Binary Frame(PCM) |
| 응답 전송 | JSON(SessionResponse / ErrorResponse) |
| VAD | Android에서 수행 |
| STT | Backend에서 수행 |
| AI 처리 | Rule Engine 처리 실패 시 RAG Service 및 LLM Service를 통해 자연어 응답 생성 |
| Session 관리 | SessionController/FSM 담당 |
| 비즈니스 로직 | WebSocket은 음성 데이터를 AI 처리 파이프라인으로 전달하고 처리 결과를 Android로 전송한다. |

WebSocket 메서드 명세

| Method | 입력 | 출력 | 설명 |
| --- | --- | --- | --- |
| connect() | Connection Request | Connection Result | WebSocket 연결 생성 |
| receive_metadata() | VoiceRequest(JSON) | - | 음성 메타데이터 수신 |
| receive_audio() | PCM Binary Frame | - | PCM 음성 데이터 수신 후 STT 전달 |
| send() | SessionResponse / ErrorResponse | - | Android로 처리 결과 전송 |
| disconnect() | Close Request | - | WebSocket 연결 종료 |

WebSocket 처리 흐름

| 단계 | 처리 |
| --- | --- |
| 1 | Android가 WebSocket 연결 요청 |
| 2 | Server가 연결 수락 |
| 3 | Android가 VoiceRequest(JSON Metadata) 전송 |
| 4 | Android가 PCM Binary Frame 전송 |
| 5 | Server가 STT로 전달 |
| 6 | STT → RapidFuzz → Rule Parser → Rule Engine 수행 |
| 7 | Rule 처리 성공 시 Event Executor 수행 |
| 8 | Rule 처리 실패 시 RAG Service에서 관련 문서를 검색 |
| 9 | LLM Service가 검색 결과를 기반으로 자연어 응답 생성 |
| 10 | SessionResponse 생성 |
| 11 | Android로 SessionResponse 전송 |

WebSocket 메시지 정의

| Message Type | 전송 방식 | 송신 | 수신 | DTO |
| --- | --- | --- | --- | --- |
| VOICE_REQUEST_METADATA | JSON | Android | Server | VoiceRequest |
| VOICE_REQUEST_AUDIO | Binary(PCM) | Android | Server | PCM Audio |
| SESSION_RESPONSE | JSON | Server | Android | SessionResponse |
| ERROR_RESPONSE | JSON | Server | Android | ErrorResponse |
| PAYMENT_RESULT | JSON | 결제 모듈 | Server | PaymentResultRequest |

WebSocket 실행 정책

| 항목 | 정책 |
| --- | --- |
| 연결 방식 | Persistent Connection |
| 통신 방식 | Request / Response |
| VoiceRequest 전송 방식 | JSON Metadata 전송 후 PCM Binary Frame 전송 |
| 음성 데이터 | PCM Binary |
| JSON 역할 | 세션 정보 및 메타데이터 전달 |
| Binary 역할 | 음성 데이터 전달 |
| Session 관리 | SessionController/FSM 담당 |
| 연결 종료 | Session 종료 또는 Client 종료 요청 시 |
| VoiceRequest 식별 | JSON Metadata 수신 후 가장 먼저 도착하는 PCM Binary Frame을 동일 요청으로 처리 |

WebSocket 예외 처리

| 상황 | 처리 |
| --- | --- |
| WebSocket 연결 실패 | ERROR_RESPONSE 전송 |
| JSON Metadata 누락 | ERROR_RESPONSE 전송 |
| PCM Binary 미수신 | ERROR_RESPONSE 전송 |
| VoiceRequest 형식 오류 | ERROR_RESPONSE 전송 |
| Session 없음 | ERROR_RESPONSE 전송 |
| 내부 서버 오류 | ERROR_RESPONSE 전송 |
| WebSocket 연결 종료 | Session 종료 후 연결 해제 |

WebSocket 전체 처리 흐름

| Android(Client) | Python(Server) |
| --- | --- |
| connect() | 연결 수락 |
| VoiceRequest(JSON Metadata) | receive_metadata() |
| PCM Binary Frame | receive_audio() |
| 대기 | STT → RapidFuzz → Rule Parser → Rule Engine → Event Executor |
| SessionResponse 수신 | send() |
| TTS 출력 | - |
| disconnect() | 연결 종료 |

WebSocket 아키텍처 흐름

```
		Android(Client)
					│
					▼
VoiceRequest(JSON Metadata)
					│
					▼
	 PCM Binary Frame
					│
					▼
			WebSocket
					│
					▼
				 STT
					│
					▼
			RapidFuzz
					│
					▼
			Rule Parser
			 		│
			 		▼
			Rule Engine
					 │
		┌──────┴───────┐
		│              │
		▼              ▼
  Event       RAG Service
 Executor          │
    │              ▼
    │         LLM Service
    │              │
    └──────┬───────┘
           ▼
    SessionResponse
           │
           ▼
        Android
```