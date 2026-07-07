# test_parser.py  (backend 루트에 임시)
import asyncio
from app.ai.ruleEngine.ruleParser import RuleParser


test_cases = [
    "바닐라라떼 따숩게, 주세요.",      # ORDER: menu + HOT
    "아메리카노 두 잔 아이스",          # ORDER: menu + quantity + ICE
    "아메리카노 아이스 샷 추가",        # ORDER: menu + ICE + 샷
    "옵션 안 할게",                     # ORDER: skip_optional
    "장바구니 보여줘",                  # CART SHOW
    "장바구니 비워",                    # CART CLEAR
    "아메리카노 하나 더",               # CART INCREASE
    "결제할게요",                       # PAYMENT
    "달달한 거 추천해줘",               # RECOMMEND REQUEST
    "그걸로 할게",                      # RECOMMEND ACCEPT
    "메뉴 뭐 있어?",                    # INFO
    "매장에서 먹고 갈게요",             # SESSION STORE
    "주문 취소할래",                    # SESSION CANCEL
    "오늘 날씨 좋네요",                 # 해석 불가 → LLM 폴백
    "아메리카노 주문하고 결제까지 해줘", # 복합 → LLM 폴백
    "아이스 아메리카노랑 아이스 라떼줘"
]


async def main():
    for text in test_cases:
        print("=" * 50)
        print(f"입력: {text}")
        await RuleParser.parse_ruleEngine_ruleParser(text)
    print("=" * 50)


asyncio.run(main())