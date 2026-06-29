from app.memory.session.enums import OrderType, SessionStatus
from app.memory.session.session import Session
from app.memory.session.sessionCrud import SessionCrud
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.menus import Menus


class SystemController:

    # ------------------------------------------------------------------
    # 세션 생성 (= SELECT_ORDER_TYPE 핸들러)
    #   매장/포장 선택과 동시에 새 Session 생성 + order_type 세팅
    #   INIT → ORDERING 전이는 dispatcher 가 처리
    # ------------------------------------------------------------------
    @staticmethod
    async def create_session_controllers_systemController(
        order_type: OrderType,
    ) -> Session:
        """매장/포장 선택과 함께 새 Session 생성"""
        session = await SessionCrud.create_session_session_sessionCrud()
        session.order_type = order_type
        return session

    # ------------------------------------------------------------------
    # 세션 완료
    # ------------------------------------------------------------------
    @staticmethod
    async def complete_session_controllers_systemController(
        session: Session,
    ) -> None:
        """Session 완료"""
        session.session_status = SessionStatus.COMPLETED
        await SessionCrud.update_session_session_sessionCrud(session)

    # ------------------------------------------------------------------
    # 세션 취소 (상태 표기 후 메모리에서 제거)
    # ------------------------------------------------------------------
    @staticmethod
    async def cancel_session_controllers_systemController(
        session: Session,
    ) -> None:
        """Session 취소 → 메모리에서 삭제"""
        session.session_status = SessionStatus.CANCELED
        await SessionCrud.delete_session_session_sessionCrud(session.session_id)

    # ------------------------------------------------------------------
    # 세션 만료 (상태 표기 후 메모리에서 제거)
    # ------------------------------------------------------------------
    @staticmethod
    async def expire_session_controllers_systemController(
        session: Session,
    ) -> None:
        """Session 만료 → 메모리에서 삭제"""
        session.session_status = SessionStatus.EXPIRED
        await SessionCrud.delete_session_session_sessionCrud(session.session_id)

    # ------------------------------------------------------------------
    # 메뉴 정보 조회 (Query)
    # ------------------------------------------------------------------
    @staticmethod
    async def get_menu_info_controllers_systemController(
        db: AsyncSession,
        menu_id: int,
    ) -> dict:
        """메뉴 정보 조회 (없으면 Menus 가 404=MENU_NOT_FOUND 발생)"""
        return await Menus.get_single_menu_detail_services_menus(
            db=db,
            m_id=menu_id,
        )