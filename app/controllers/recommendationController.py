"""RecommendationController : 추천 요청/수락 처리.

- REQUEST_RECOMMENDATION : 발화 조건(condition)에서 맛 키워드를 뽑아
  메뉴 설명(m_description) 매칭으로 추천 후보를 고른다.
  (키워드 없음/매칭 실패 → 기본 상위 메뉴 폴백)
  결과는 session.recommendation_list 에 보관 + 안내 문구(session.message) 세팅.
- ACCEPT_RECOMMENDATION : 추천 목록 첫 번째 메뉴로 OrderItem 생성
  (OrderController 재사용 — ORDER_ITEM_EXISTS / MENU_NOT_FOUND 동일 처리)

NOTE: 1차 룰 기반 구현. 이후 LLM/RAG 추천으로 교체 시
      본 컨트롤러 내부만 바꾸면 됨 (이벤트/응답 계약 유지).
"""

from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.controllers.orderController import OrderController
from app.memory.session.session import Session
from app.services.menus import Menus

# 발화 조건에서 찾는 맛/온도 키워드 (m_description 매칭용)
RECOMMEND_CONDITION_KEYWORDS = (
    "달콤", "고소", "시원", "따뜻", "상큼", "진한", "부드러", "쌉쌀", "새콤", "청량",
)

RECOMMEND_LIMIT = 5


class RecommendationController:

    # ------------------------------------------------------------------
    # request_recommendation : 추천 목록 생성
    # ------------------------------------------------------------------
    @staticmethod
    async def request_recommendation_controllers_recommendationController(
        db: AsyncSession,
        session: Session,
        condition: Optional[str] = "",
    ) -> None:
        """조건 키워드 매칭 → recommendation_list 갱신 + 안내 문구"""

        # 조건 문장에서 첫 번째 매칭 키워드 추출 (없으면 None → 기본 추천)
        keyword = next(
            (k for k in RECOMMEND_CONDITION_KEYWORDS if k in (condition or "")),
            None,
        )

        menus = await Menus.get_recommendation_menus_services_menus(
            db=db, keyword=keyword, limit=RECOMMEND_LIMIT,
        )
        if not menus:
            raise ValueError("RECOMMENDATION_NOT_FOUND")

        session.recommendation_list = [m["m_id"] for m in menus]

        names = ", ".join(m["m_name"] for m in menus)
        session.message = f"{names} 어떠세요?"

    # ------------------------------------------------------------------
    # accept_recommendation : 추천 첫 메뉴로 주문 시작
    # ------------------------------------------------------------------
    @staticmethod
    async def accept_recommendation_controllers_recommendationController(
        db: AsyncSession,
        session: Session,
    ) -> None:
        """추천 목록 첫 메뉴 → OrderItem 생성 (목록은 소진 처리)"""

        if not session.recommendation_list:
            raise ValueError("RECOMMENDATION_NOT_FOUND")

        menu_id = session.recommendation_list[0]

        # OrderController 재사용 (ORDER_ITEM_EXISTS / MENU_NOT_FOUND 검증 포함)
        await OrderController.create_order_item_controllers_orderController(
            db=db, session=session, menu_id=menu_id,
        )

        # 추천 목록 소진 + 안내 문구
        session.recommendation_list = []
        menu_name = (session.current_menu or {}).get("m_name", "")
        session.message = f"{menu_name} 선택했어요. 옵션을 골라주세요."
