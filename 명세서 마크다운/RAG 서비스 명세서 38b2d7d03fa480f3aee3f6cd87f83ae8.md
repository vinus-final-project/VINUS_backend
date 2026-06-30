# RAG 서비스 명세서

RAG Service 처리 명세

| 항목 | 내용 |
| --- | --- |
| 역할 | Rule Engine에서 처리하지 못한 사용자 발화를 Embedding으로 변환하여 Vector DB에서 관련 문서를 검색하고, LLM Service에 전달할 Context를 생성한다. |
| 호출 시점 | Rule Engine 처리 실패 시 |
| 입력 | Session, Query(String) |
| 출력 | Context(String) |
| Vector DB | ChromaDB |
| 호출자 | WebSocket AI 처리 흐름 |
| 다음 처리 | LLM Service |

RAG Service 메서드 명세

| Method | 입력 | 출력 | 설명 |
| --- | --- | --- | --- |
| retrieve() | Session, Query(String) | Context(String) | 사용자 발화와 관련된 메뉴 정보를 검색하여 LLM 입력용 Context를 생성한다. |

RAG Service 실행 정책

| 항목 | 정책 |
| --- | --- |
| 검색 방식 | Vector Search |
| 검색 대상 | 메뉴명, 메뉴 설명, 옵션, 카테고리, 알레르기 정보 |
| Vector DB | ChromaDB |
| Top-K | 5 |
| 검색 성공 | 검색된 문서를 하나의 Context(String)로 생성하여 반환 |
| 검색 실패 | Empty Context(String) 반환 |
| Session 사용 | 현재 주문 상태 및 추천 이력을 참고하여 검색 품질 향상 |

RAG Service 처리 흐름

| 단계 | 처리 |
| --- | --- |
| 1 | Rule Engine 처리 실패 |
| 2 | Session과 사용자 발화(Query) 수신 |
| 3 | ChromaDB에서 유사 메뉴 문서 검색 |
| 4 | 검색된 문서를 하나의 Context(String)로 구성 |
| 5 | Context를 LLM Service로 전달 |

RAG Service 입력 DTO

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| session | Session | 현재 세션 정보 |
| query | String | 사용자 발화 |

RAG Service 출력 DTO

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| context | String | 검색된 메뉴 정보를 LLM Prompt에 사용할 수 있도록 구성한 Context |

검색 대상 문서

| 문서 | 포함 정보 |
| --- | --- |
| Menu Document | 메뉴명, 카테고리, 설명, 가격 |
| Option Document | 옵션명, 옵션 가격, 필수 여부 |
| Ingredient Document | 원재료 정보 |
| Allergy Document | 알레르기 정보 |