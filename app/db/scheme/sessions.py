from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from enum import Enum
from datetime import datetime


# --- Enum 정의 ---
class SessionStatus(str, Enum):
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    EXPIRED = "EXPIRED"
    CANCELED = "CANCELED"


class SessionCarry(str, Enum):
    STORE = "STORE"
    TAKEOUT = "TAKEOUT"


# --- [세션 생성/조회]용 스키마 ---
class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    se_id: str
    se_status: SessionStatus
    se_carry: Optional[SessionCarry] = None
    se_started_at: datetime
    se_ended_at: Optional[datetime] = None

    # ↓↓↓ 아래 필드는 sessions 테이블 컬럼 아님 ↓↓↓
    # 담당자 작업 완료 후 서비스 레벨에서 채워짐. 현재는 타입 미확정 → Optional 처리.

    fsm_state: Optional[str] = None
    # FSM 담당자 작업 예정. INIT / ORDERING / PAYMENT / COMPLETE 등 (FSM 설계명세서 참고)

    order_type: Optional[str] = None
    # 주문 담당자 작업 예정. STORE / TAKEOUT 등 (SELECT_ORDER_TYPE 이벤트 결과)

    order_item: Optional[dict] = None
    # 주문 담당자 작업 예정. DB 테이블 아님 — 세션 내 임시 주문중 항목(메모리/세션 상태).
    # 실제 구조(예: m_id, quantity, status, selected_options 등) 확정 시 별도 Pydantic 모델로 교체 필요.

    cart: Optional[List[dict]] = None
    # 주문/장바구니 담당자 작업 예정. orderMenus 테이블과 직접 매핑되는지 별도 임시구조인지 미확정.
    # 확정 시 List[OrderItem] 형태로 교체 필요.

    recommendation_list: Optional[List[dict]] = None
    # LLM 추천 담당자(본인) 작업 예정. LLM 출력 포맷 미확정.
    # 확정 시 List[RecommendedMenu] 형태로 교체 예정 (예상: m_id, m_name, m_price, reason 등).