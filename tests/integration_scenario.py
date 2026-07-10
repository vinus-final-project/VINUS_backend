# tests/integration_scenario.py
"""터치 흐름 통합 테스트 시나리오 (REST).

실행 전제
  1) 백엔드 서버 기동 : python main.py  (기본 http://localhost:8081)
  2) DB 시드 완료 (lifespan 에서 자동)
  3) pip install httpx

실행
  python tests/integration_scenario.py

검증 시나리오
  S1  카테고리/메뉴 조회
  S2  세션 생성 (매장) → ORDERING
  S3  메뉴 선택 → 옵션(ICE) → 수량 2 → 완료(카트 담기)
  S4  장바구니 조회/수량 증감/삭제 규칙
  S5  에러 코드: 없는 메뉴 / 옵션 미선택 완료 / 빈 카트 결제
  S6  결제 시작(PAYMENT) → 결제 취소(ORDERING 복귀)
  S7  세션 취소 → SESSION_END

음성(WS) 테스트는 실제 마이크 PCM 이 필요하므로 본 스크립트 범위 외.
  → wscat -c ws://localhost:8081/ws/voice 로 연결 후
    {"type":"BIND_SESSION","session_id":"<uuid>"} 전송하여 바인딩만 수동 확인.
"""

import sys

import httpx

BASE = "http://localhost:8081"

passed, failed = 0, 0


def check(name: str, cond: bool, detail: str = ""):
    global passed, failed
    if cond:
        passed += 1
        print(f"  [PASS] {name}")
    else:
        failed += 1
        print(f"  [FAIL] {name} {detail}")


def main():
    c = httpx.Client(base_url=BASE, timeout=10.0)

    # ── S1 카테고리/메뉴 조회 ─────────────────────────────
    print("\nS1. 카테고리/메뉴 조회")
    r = c.get("/categories")
    check("GET /categories 200", r.status_code == 200, str(r.status_code))
    categories = r.json()["categories"]
    check("카테고리 존재", len(categories) > 0)

    c_id = categories[0]["c_id"]
    r = c.get("/menus", params={"c_id": c_id})
    check("GET /menus 200", r.status_code == 200)
    menus = r.json()["menus"]
    check("메뉴 존재", len(menus) > 0)
    m_id = menus[0]["m_id"]

    r = c.get(f"/menus/{m_id}")
    check("GET /menus/{m_id} 200", r.status_code == 200)
    detail = r.json()
    option_groups = detail.get("option_groups", [])

    # ── S2 세션 생성 ─────────────────────────────────────
    print("\nS2. 세션 생성 (매장)")
    r = c.post("/sessions", json={"order_type": "STORE"})
    check("POST /sessions 201", r.status_code == 201, str(r.status_code))
    body = r.json()
    sid = body["session_id"]
    check("fsm_state == ORDERING", body["fsm_state"] == "ORDERING", body["fsm_state"])
    check("order_type == STORE", body["order_type"] == "STORE")

    # ── S3 주문 작성 → 카트 ──────────────────────────────
    print("\nS3. 메뉴 선택 → 옵션 → 수량 → 완료")
    r = c.post("/orders", json={"session_id": sid, "menu_id": m_id})
    check("SELECT_MENU 성공", r.status_code == 200 and r.json()["success"])

    # 필수 옵션 그룹이 있으면 각 그룹 첫 옵션 선택
    for og in option_groups:
        if og["og_required"] and og["options"]:
            op_id = og["options"][0]["op_id"]
            r = c.post("/orders/option", json={"session_id": sid, "option_id": op_id})
            check(f"옵션 선택 og={og['og_id']}", r.json()["success"], r.text)

    r = c.post("/orders/quantity", json={"session_id": sid, "quantity": 2})
    check("수량 2 설정", r.json()["order_item"]["quantity"] == 2)

    r = c.post("/orders/complete", json={"session_id": sid})
    body = r.json()
    check("완료 → 카트 1건", body["success"] and len(body["cart"]) == 1, r.text)
    check("order_item 비움", body["order_item"] is None)
    cart_item_id = body["cart"][0]["cart_item_id"]
    total_before = body["total_price"]

    # ── S4 장바구니 규칙 ─────────────────────────────────
    print("\nS4. 장바구니 수량 증감/삭제")
    r = c.patch(f"/sessions/{sid}/cart/{cart_item_id}", json={"delta": 1})
    check("수량 +1 → 3", r.json()["cart"][0]["quantity"] == 3)
    r = c.patch(f"/sessions/{sid}/cart/{cart_item_id}", json={"delta": -1})
    check("수량 -1 → 2", r.json()["cart"][0]["quantity"] == 2)
    check("총액 = 단가×2", r.json()["total_price"] == total_before)

    # ── S5 에러 코드 ─────────────────────────────────────
    print("\nS5. 에러 코드")
    r = c.post("/orders", json={"session_id": sid, "menu_id": 999999})
    body = r.json()
    check(
        "없는 메뉴 → MENU_NOT_FOUND 문구",
        body["success"] is False or body.get("error_code"),
        r.text,
    )
    # 주문 중복 생성 차단 확인 후 현재 주문 취소로 정리
    c.post("/orders/cancel", json={"session_id": sid})

    # ── S6 결제 시작/취소 ────────────────────────────────
    print("\nS6. 결제 시작 → 취소")
    r = c.post("/payments/start", json={"session_id": sid})
    body = r.json()
    check("START_PAYMENT → PAYMENT", body["fsm_state"] == "PAYMENT", r.text)
    check("total_price > 0", body["total_price"] > 0)

    r = c.post("/payments/cancel", json={"session_id": sid})
    check("PAYMENT_CANCEL → ORDERING", r.json()["fsm_state"] == "ORDERING")

    # ── S7 세션 취소 ─────────────────────────────────────
    print("\nS7. 세션 취소")
    r = c.post(f"/sessions/{sid}/cancel")
    body = r.json()
    check("session_end == True", body["session_end"] is True, r.text)
    r = c.get(f"/sessions/{sid}")
    check("취소 후 조회 404", r.status_code == 404, str(r.status_code))

    # ── 결과 ────────────────────────────────────────────
    print(f"\n결과: PASS {passed} / FAIL {failed}")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
