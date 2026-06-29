"""FSM Dispatcher.

FSM Event를 실행합니다.

동작 순서
1. 현재 FSM 상태 확인
2. Event 허용 여부 확인
3. Controller 실행
4. 성공 시 FSM 상태 변경
"""

from typing import Optional

from app.fsm.event import Event
from app.fsm.state import FSMState
from app.fsm.transition import TRANSITIONS
from app.memory.session.session import Session


class Dispatcher:

    @staticmethod
    async def dispatch(
        session: Optional[Session],
        event: Event,
    ) -> Optional[Session]:
        """
        Parameters
        ----------
        session : Optional[Session]
            INIT 상태에서는 None,
            ORDERING 이후에는 현재 Session

        event : Event
            실행할 FSM Event

        Returns
        -------
        Optional[Session]
            Controller 실행 결과 Session
        """

        # --------------------------------------------------------------
        # 현재 FSM 상태 확인
        # --------------------------------------------------------------
        current_state = (
            FSMState.INIT
            if session is None
            else session.fsm_state
        )

        # --------------------------------------------------------------
        # Transition 확인
        # --------------------------------------------------------------
        transitions = TRANSITIONS[current_state]

        if event not in transitions:
            raise ValueError(
                f"Invalid transition : {current_state} -> {event}"
            )

        next_state = transitions[event]

        # --------------------------------------------------------------
        # Controller 실행
        # --------------------------------------------------------------
        # TODO
        # session = await EventHandler.execute(
        #     session=session,
        #     event=event,
        # )

        # --------------------------------------------------------------
        # 상태 변경
        # --------------------------------------------------------------
        if session is not None and next_state is not None:
            session.fsm_state = next_state

        return session