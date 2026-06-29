# LLM Service 명세서

LLM Service 처리 명세

| 항목 | 내용 |
| --- | --- |
| 역할 | RAG Service가 생성한 Context와 사용자 발화를 기반으로 자연어 응답을 생성하여 Android에 전달할 SessionResponse를 생성한다. |
| 호출 시점 | RAG Service 처리 완료 후 |
| 입력 | Session, Query(String), Context(String) |
| 출력 | LLMResult |
| 호출자 | WebSocket AI 처리 흐름 |
| 다음 처리 | FSM.dispatch() |

LLM Service 메서드 명세

| Method | 입력 | 출력 | 설명 |
| --- | --- | --- | --- |
| generate_result() | Session, Query(String), Context(String) | LLMResult 반환 | Context를 기반으로 자연어 응답과
FSM Event(필요 시)를 생성하여
LLMResult를 반환한다. |

LLM Service 실행 정책

| 항목 | 정책 |
| --- | --- |
| 모델 | 프로젝트에서 사용하는 LLM |
| 입력 | Session, Query, Context |
| Prompt 생성 | Query와 Context를 기반으로 Prompt 생성 |
| Context 사용 | RAG Service에서 생성한 Context 사용 |
| 응답 언어 | 한국어 |
| 추천 처리 | 추천 요청 시 Vector Search 결과를 기반으로 추천 생성 |
| 메뉴 정보 | Context에 포함된 정보만 사용 |
| Session 활용 | 현재 FSM 상태, OrderItem, Cart, OrderType 등을 참고 |
| 검색 결과 없음 | 안내 문구를 포함한 LLMResult 반환 |
| 출력 | LLMResult 반환 |
| Event 생성 | FSM에서 처리 가능한 주문 의도가 존재하지 않을 경우events는 null로 반환한다. |

LLM Service 처리 흐름

| 단계 | 처리 |
| --- | --- |
| 1 | Session, Query, Context 수신 |
| 2 | Prompt 생성 |
| 3 | LLM 호출 |
| 4 | Event 생성(필요 시) |
| 5 | 자연어 응답 생성 |
| 6 | LLMResult 반환 |

LLM Service 입력 DTO

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| session | Session | 현재 세션 정보 |
| query | String | 사용자 발화 |
| context | String | RAG Service에서 생성한 Context |

LLM Service 출력 DTO

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| result | String | LLM 자연어 응답 |
| **events** | **List<FSMEvent>** | FSM에서 실행할 Event 목록 (없으면 빈 리스트) |
| parameters | Map<String,Object> | Event 실행에 필요한 파라미터 |
| response | String | Android에 전달할 안내 문구 |
| source | LLM | 처리 출처 |

LLM Prompt 정책

| 항목 | 정책 |
| --- | --- |
| Context 우선 | Context에 포함된 정보만 활용하여 응답 생성 |
| 정보 부족 | Context에 정보가 없을 경우 해당 사실을 사용자에게 안내 |
| 추천 요청 | Context에 포함된 후보 메뉴를 기반으로 추천 생성 |
| 메뉴 정보 | Context 외의 메뉴 정보는 생성하지 않음(Hallucination 방지) |
| 응답 길이 | 1~2문장 |
| 응답 형식 | 자연스러운 한국어 |
| Event 생성 | Rule Engine이 해석하지 못한 사용자 발화 중FSM에서 처리 가능한 주문 의도가 존재할 경우FSM Event를 생성한다. |

이벤트 생성 정책

| 항목 | 정책 |
| --- | --- |
| Event 생성 | FSM에서 처리 가능한 주문 의도가 존재하면 0개 이상의 Event를 생성한다. |
| Event 실행 | 생성된 Event는 직접 실행하지 않고 EventExecutor로 전달한다. |
| Event 없음 | 빈 Event List를 반환한다. |

Prompt 구성 정책

| 구성 요소 | 내용 |
| --- | --- |
| System Prompt | 키오스크 주문 도우미 역할 정의 |
| User Prompt | 사용자 발화(Query) |
| Context | RAG Service 검색 결과 |
| Session | 현재 주문 상태(FSM, Cart, OrderItem 등) |

예외 처리 정책

| 상황 | 처리 |
| --- | --- |
| Context 없음 | 관련 정보를 찾을 수 없습니다.안내 문구를 포함한 LLMResult 반환 |
| LLM 호출 실패 | ErrorResponse 또는 기본 안내 LLMResult 반환 |
| 추천 후보 없음 | 추천 불가 안내를 포함한
LLMResult 반환 |