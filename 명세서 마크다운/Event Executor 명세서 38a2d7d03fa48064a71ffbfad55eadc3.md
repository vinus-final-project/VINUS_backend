# Event Executor 명세서

Event Executor 명세서

| Executor ID | 입력 | 처리 내용 | 호출 대상 | 성공 시 | 실패 시 |
| --- | --- | --- | --- | --- | --- |
| EX001 | Event List | FIFO 순서로 Event 실행 | FSM | 다음 Event 실행 | 실행 중단 및 SessionResponse 반환 |
| EX002 | FSM Event | `FSM.dispatch()` 호출 | FSM | FSMResult 반환 | 실행 중단 및 SessionResponse 반환 |
| EX003 | FSMResult | 실행 결과 확인 | - | 다음 Event 실행 | 실행 중단 및 SessionResponse 반환 |
| EX004 | 모든 Event 완료 | SessionResponse 생성 및 반환 | - | SessionResponse 반환 | - |

Event Executor 실행 정책

| 항목 | 정책 |
| --- | --- |
| 입력 | Rule Engine 또는 LLM이 생성한 Event List |
| 출력 | SessionResponse |
| Event Queue | FIFO |
| Event 실행 | 생성된 순서대로 실행 |
| FSM 호출 | dispatch(event) |
| Validation | FSM 처리 |
| Controller 호출 | FSM 처리 |
| Session 갱신 | FSM 처리 |
| Event 실패 | Executor가 실행 중단 |
| Rollback | 수행하지 않음 |
| Event 완료 | SessionResponse 반환 |

Event Executor 처리 흐름

| 단계 | 처리 |
| --- | --- |
| 1 | Rule Engine 또는 LLM으로부터 Event List 수신 |
| 2 | Event Queue(FIFO) 생성 |
| 3 | 첫 번째 Event 선택 |
| 4 | FSM.dispatch(Event) 호출 |
| 5 | FSM 내부 처리 |
| 6 | FSMResult 반환 |
| 7 | 성공 여부 확인 |
| 8 | 다음 Event 존재 여부 확인 |
| 9 | 남은 Event가 있으면 반복 |
| 10 | 모든 Event 완료 후 SessionResponse 반환 |

Event Executor 예외 처리 정책

| 상황 | 처리 |
| --- | --- |
| FSM 처리 실패 | 이후 Event 실행 중단 |
| CRUD(DB) 오류 | ERROR 반환 |
| Session 없음 | ERROR 반환 |
| Event 없음 | SessionResponse 즉시 반환 |

Event Executor 입력 예시

| Rule Engine 결과(Event List) | 실행 순서 |
| --- | --- |
| SELECT_MENU | ① |
| SET_QUANTITY | ② |
| SELECT_REQUIRED_OPTION | ③ |
| SELECT_OPTIONAL_OPTION | ④ |

Event Executor 출력 예시

| 실행 결과 | 반환 |
| --- | --- |
| 모든 Event 성공 | SessionResponse |
| FSM 처리 실패 | ERROR(Response) |
| Repository 오류 | ERROR(Response) |

Event Executor 인터페이스

| 메서드 | 입력 | 반환 | 설명 | 호춢자 |
| --- | --- | --- | --- | --- |
| execute() | List, Session | SessionResponse | Event List 실행 | Rule Engine |