# test_normalize.py  (backend 루트에 임시)
import asyncio
from app.ai.rapidfuzz.normalizer import Normalizer


# 테스트 케이스 — 다양한 오인식 상황
test_cases = [
    "바일라라떼, 따숩게, 주세요.",   # STT 실제 결과 (이번 확인 대상!)
    "바이널라떼 휘핑 빼주세요.",     # STT 이전 결과 (자모 거리 멀어서 안 잡혔던 것)
    "아매리카노 한잔 아이스",        # 메뉴 오타
    "카페라뗴 따뜻하게",             # 라떼 오타 (뗴)
    "바닐라 라떼 주세요",            # 띄어쓰기 다름
    "아인슈페너 하나",               # 메뉴 + 수량 (수량 보존 확인)
    "흑당 카페라떼",                 # 띄어쓰기
    "녹차라떼랑 초코라떼",           # 두 메뉴
    "딸기 스무디 라지로",            # 메뉴 + 옵션
    "캬라멜 마끼아또",               # 오타 + 띄어쓰기
    "디카페인연유라떄",              # 붙여쓴 긴 오타
    "안녕하세요 주문할게요",         # 메뉴 없는 문장 (과잉 보정 체크)
]


async def main():
    for text in test_cases:
        print("=" * 40)
        await Normalizer.normalize_rapidfuzz_normalizer(text)
    print("=" * 40)


asyncio.run(main())