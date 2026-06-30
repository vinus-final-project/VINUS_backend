# STT/RapidFuzz 명세서

STT 처리 명세

| 항목 | 내용 |
| --- | --- |
| 입력 | VoiceRequest(PCM Binary) |
| 출력 | STTResult |
| 모델 | Whisper |
| 호출 시점 | Android VAD 종료 후 |
| 다음 처리 | RapidFuzz |
| 실패 시 | ERROR 반환 |

STT 메서드 명세

| Method | 입력 | 출력 | 설명 |
| --- | --- | --- | --- |
| transcribe() | PCM Audio Stream | Text | 음성을 텍스트로 변환 |

STT 처리 흐름

| 단계 | 처리 |
| --- | --- |
| 1 | Android VAD 종료 |
| 2 | VoiceRequest 수신 |
| 3 | PCM Binary 추출 |
| 4 | Whisper 추론 |
| 5 | Text 생성 |
| 6 | RapidFuzz 전달 |

# RapidFuzz 명세서

RapidFuzz 처리 명세

| 항목 | 내용 |
| --- | --- |
| 입력 | Text |
| 출력 | Normalized Text |
| 처리 방식 | Fuzzy Matching |
| 호출 시점 | STT 완료 후 |
| 다음 처리 | Rule Parser |
| 실패 시 | 원본 Text 전달 또는 ERROR 반환 |

RapidFuzz 메서드 명세

| Method | 입력 | 출력 | 설명 |
| --- | --- | --- | --- |
| normalize() | Text | Normalized Text | 메뉴명 및 키워드 오인식을 보정 |

**RapidFuzz 처리 흐름**

| 단계 | 처리 |
| --- | --- |
| 1 | STT 결과 수신 |
| 2 | 메뉴명 후보 검색 |
| 3 | 유사도 계산 |
| 4 | 최고 점수 후보 선택 |
| 5 | 보정된 Text 반환 |
| 6 | Rule Parser 전달 |

STT + RapidFuzz 전체 처리 흐름

| 단계 | 입력 | 처리 | 출력 |
| --- | --- | --- | --- |
| 1 | PCM Audio Stream | STT(Whisper) | Text |
| 2 | Text | RapidFuzz | Normalized Text |
| 3 | Normalized Text | Rule Parser | ParseResult |