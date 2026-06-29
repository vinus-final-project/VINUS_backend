from app.memory.session.enums import OrderType, SessionStatus
from app.memory.session.session import Session
from app.memory.session.sessionCrud import SessionCrud
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.menus import ServicesMenus


class SystemController:

    # ------------------------------------------------------------------
    # Command
    # ------------------------------------------------------------------

    @staticmethod
    async def create_session_controllers_systemController(
        order_type: OrderType,
    ) -> Session:
        """새 Session 생성"""

        # Session 생성
        session = await SessionCrud.create_session_session_sessionCrud()

        # 주문 유형 저장
        session.order_type = order_type

        return session
    

    @staticmethod
    async def complete_session_controllers_systemController(
        session: Session,
    ) -> None:
        """Session 완료"""

        session.session_status = SessionStatus.COMPLETED

        await SessionCrud.update_session_session_sessionCrud(session)



    @staticmethod
    async def cancel_session_controllers_systemController(
        session: Session,
    ) -> None:
        """Session 취소"""

        session.session_status = SessionStatus.CANCELED

        await SessionCrud.update_session_session_sessionCrud(session)


    @staticmethod
    async def expire_session_controllers_systemController(
        session: Session,
    ) -> None:
        """Session 만료"""

        session.session_status = SessionStatus.EXPIRED

        await SessionCrud.update_session_session_sessionCrud(session)


