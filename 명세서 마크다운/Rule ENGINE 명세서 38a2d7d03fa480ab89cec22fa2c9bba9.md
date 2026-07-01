# Rule ENGINE 명세서

Intent 정의(=사용자 의도)

| Intent | 설명 |
| --- | --- |
| ORDER | 메뉴 주문 및 옵션 선택 |
| CART | 장바구니 관리 |
| PAYMENT | 결제 |
| RECOMMEND | 메뉴 추천 |
| INFO | 메뉴 정보 조회 |
| SESSION | 주문 세션 관리 |

Rule Parser 명세서

| Rule ID | 입력 조건 | Intent | Entity | LLM 호출 | 설명 |
| --- | --- | --- | --- | --- | --- |
| R001 | 메뉴명 포함 | ORDER | menu | X | 메뉴 선택 |
| R002 | 수량 표현 포함 | ORDER | quantity | X | 수량 추출 |
| R003 | 필수 옵션 포함(아이스, 핫, 라지 등) | ORDER | required_option | X | 필수 옵션 추출 |
| R004 | 선택 옵션 포함(샷 추가 등) | ORDER | optional_option | X | 선택 옵션 추출 |
| R005 | "옵션 안 할게", "그대로", "없어요" 포함 | ORDER | skip_optional=true | X | 선택 옵션 생략 |
| R006 | "장바구니", "담은 메뉴" 포함 | CART | action=SHOW | X | 장바구니 조회 |
| R007 | "삭제", "빼", "제거" 포함 | CART | action=REMOVE, cart_item | X | 장바구니 삭제 |
| R008 | "전체 삭제", "비워" 포함 | CART | action=CLEAR | X | 장바구니 비우기 |
| R009 | "하나 더", "증가" 포함 | CART | action=INCREASE, cart_item | X | 수량 증가 |
| R010 | "하나 빼", "감소" 포함 | CART | action=DECREASE, cart_item | X | 수량 감소 |
| R011 | "결제", "계산" 포함 | PAYMENT | action=START | X | 결제 시작 |
| R012 | "추천", "추천해줘" 포함 | RECOMMEND | action=REQUEST, condition | X | 추천 요청 |
| R013 | "그걸로", "추천 메뉴로 할게" 포함 | RECOMMEND | action=ACCEPT | X | 추천 메뉴 선택 |
| R014 | "메뉴", "커피 뭐 있어" 포함 | INFO | type=MENU, category | X | 메뉴 조회 |
| R015 | "매장", "포장" 포함 | SESSION | order_type | X | 주문 유형 선택 |
| R016 | "취소", "처음부터" 포함 | SESSION | action=CANCEL | X | 주문 취소 |

**Entity 정의**

| Entity | 설명 | 예시 |
| --- | --- | --- |
| menu | 메뉴명 | 아메리카노 |
| quantity | 수량 | 1, 2 |
| required_option | 필수 옵션 | ICE, HOT, LARGE |
| optional_option | 선택 옵션 | 샷 추가 |
| skip_optional | 선택 옵션 생략 여부 | true |
| action | 수행 동작 | SHOW, REMOVE, CLEAR, START, ACCEPT |
| cart_item | 장바구니 메뉴 | 아메리카노 |
| condition | 추천 조건 | 달달한, 따뜻한 |
| category | 메뉴 카테고리 | 커피 |
| type | 정보 조회 종류 | MENU, ALLERGY, INGREDIENT |
| order_type | 주문 유형 | STORE, TAKEOUT |

**LLM 호출 조건**

| Rule ID | 조건 |
| --- | --- |
| L001 | 메뉴를 인식하지 못한 경우 |
| L002 | Intent를 판단하지 못한 경우 |
| L003 | "그거", "이거", "저거", "아까 추천한 거" 등 문맥 참조 표현 |
| L004 | 규칙으로 해석할 수 없는 자연어 표현 |
| L005 | 자유 대화, 메뉴 설명, 추천 이유 등 자연어 응답 필요 |
| L006 | 여러 메뉴, 여러 Intent 또는 여러 행동이 동시에 포함된 경우 |
| L007 | RapidFuzz 후보가 여러 개이며 판별이 어려운 경우 |
| L008 | 모든 규칙이 정상 매칭되면 호출하지 않음 |

ParseResult DTO

| 필드 | 타입 | 설명 |
| --- | --- | --- |
| intent | Intent | 추출된 Intent |
| entities | Entity Map | 추출된 Entity |
| source | RULE / LLM | Rule Parser 또는 LLM 결과 |

Rule Parser 정책

| 항목 | 정책 |
| --- | --- |
| 메뉴 인식 | RapidFuzz |
| Intent 분석 | Rule 기반 |
| Entity 추출 | Rule 기반 |
| Parser 성공 | ParseResult 반환 |
| Parser 실패 | LLM 전달 |
| LLM 성공 | ParseResult 반환 |
| LLM 실패 | ERROR 반환 |

**Rule Engine 명세서**

| Engine ID | Intent | Entity 조건 | 생성 FSM Event | 실행 순서 | 실패 시 |
| --- | --- | --- | --- | --- | --- |
| E001 | ORDER | menu | SELECT_MENU | 1 | 중단 |
| E002 | ORDER | quantity | SET_QUANTITY | 2 | 중단 |
| E003 | ORDER | required_option | SELECT_REQUIRED_OPTION | 3 | 중단 |
| E004 | ORDER | optional_option | SELECT_OPTIONAL_OPTION | 4 | 중단 |
| E005 | ORDER | skip_optional=true | SKIP_OPTIONAL_OPTION | 4 | 중단 |
| E006 | CART | action=SHOW | SHOW_CART | 1 | 중단 |
| E007 | CART | action=REMOVE | REMOVE_CART_ITEM | 1 | 중단 |
| E008 | CART | action=CLEAR | CLEAR_CART | 1 | 중단 |
| E009 | CART | action=INCREASE | INCREASE_CART_ITEM | 1 | 중단 |
| E010 | CART | action=DECREASE | DECREASE_CART_ITEM | 1 | 중단 |
| E011 | PAYMENT | action=START | START_PAYMENT | 1 | 중단 |
| E012 | RECOMMEND | action=REQUEST | REQUEST_RECOMMENDATION | 1 | 중단 |
| E013 | RECOMMEND | action=ACCEPT | ACCEPT_RECOMMENDATION | 1 | 중단 |
| E014 | INFO | type=MENU | REQUEST_MENU_INFO | 1 | 중단 |
| E015 | SESSION | order_type | SELECT_ORDER_TYPE | 1 | 중단 |
| E016 | SESSION | action=CANCEL | CANCEL_SESSION | 1 | 중단 |

**Rule Engine 실행 정책**

| 항목 | 정책 |
| --- | --- |
| 입력 | ParseResult |
| 출력 | List<FSMEvent> |
| Intent 개수 | **1개만 허용** |
| 메뉴(OrderItem) | **1개만 처리** |
| Event 생성 방식 | Intent + Entity 기반 |
| Event 저장 방식 | FIFO |
| Event 실행 방식 | 생성 순서대로 순차 실행 |
| Rollback | 수행하지 않음 |
| Event 생성 실패 | ERROR 반환 또는 LLM 전달 |

**시스템 정책**

| 항목 | 정책 |
| --- | --- |
| 한 번에 처리 가능한 메뉴 | 1개 |
| 한 번에 처리 가능한 Intent | 1개 |
| 한 번에 처리 가능한 행동 | 1개 |
| 여러 메뉴 주문 감지 | LLM 전달 또는 "한 번에 한 메뉴씩 주문해 주세요." 안내 |
| 여러 Intent 감지 | LLM 전달 또는 "한 번에 한 가지 요청만 말씀해 주세요." 안내 |
| FSM 처리 방식 | 순차 처리(State Transition) |
| Pending OrderItem | 항상 1개 |

**처리 예시**

| 사용자 입력 | Parser 결과 | Rule Engine 결과 |
| --- | --- | --- |
| 아메리카노 하나 | ORDER(menu, quantity) | SELECT_MENU → SET_QUANTITY |
| 아메리카노 아이스 | ORDER(menu, required_option) | SELECT_MENU → SELECT_REQUIRED_OPTION |
| 아메리카노 아이스 샷 추가 | ORDER(menu, required_option, optional_option) | SELECT_MENU → SELECT_REQUIRED_OPTION → SELECT_OPTIONAL_OPTION |
| 옵션 안 할게 | ORDER(skip_optional=true) | SKIP_OPTIONAL_OPTION |
| 장바구니 보여줘 | CART(action=SHOW) | SHOW_CART |
| 장바구니 비워 | CART(action=CLEAR) | CLEAR_CART |
| 아메리카노 하나 더 | CART(action=INCREASE) | INCREASE_CART_ITEM |
| 결제할게 | PAYMENT(action=START) | START_PAYMENT |
| 추천해줘 | RECOMMEND(action=REQUEST) | REQUEST_RECOMMENDATION |
| 그걸로 할게 | RECOMMEND(action=ACCEPT) | ACCEPT_RECOMMENDATION |
| 메뉴 알려줘 | INFO(type=MENU) | REQUEST_MENU_INFO |
| 주문 취소 | SESSION(action=CANCEL) | CANCEL_SESSION |

엔티티 스키마

| Intent | 필수 Entity | 선택 Entity |
| --- | --- | --- |
| ORDER | `menu` | `quantity`, `required_option`, `optional_option`, `skip_optional` |
| CART | `action` | `cart_item` |
| PAYMENT | `action` | - |
| RECOMMEND | `action` | `condition` |
| INFO | `type` | `menu`, `category` |
| SESSION | `action` 또는 `order_type` | - |

Parser 정책(발표용)

| 항목 | 정책 |
| --- | --- |
| 메뉴 인식 | RapidFuzz |
| Intent 분석 | Rule 기반 |
| Entity 추출 | Rule 기반 |
| 실패 | LLM |

**Rule Engine 정책**

| 항목 | 정책 |
| --- | --- |
| 입력 | ParseResult |
| 출력 | List |