from enum import Enum

"""
FSM의 State를 정의합니다
INIT은 포장 매장을 선택하는 상태
ORDERING은 메뉴 주문 및 장바구니 담는 모든 과정을 의미하는 상태
PAYMENT는 결제관련 상태
COMPLETE는 결제 완료 상태입니다.

"""
class FSMState(str, Enum):
    INIT = "INIT"
    ORDERING = "ORDERING"
    PAYMENT = "PAYMENT"
    COMPLETE = "COMPLETE"