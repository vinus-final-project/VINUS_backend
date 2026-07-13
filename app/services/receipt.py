"""[신규] app/services/receipt.py
 
영수증 출력 서비스 — AHAPOS CPP-3000 (USB, ESC/POS)
 
Windows 프린터 스풀러(RAW) 경유로 ESC/POS 바이트를 전송한다.
- CPP-3000 이 Windows 에 공식 USB 드라이버로 설치되어 있어야 한다.
- 한글: CP949(EUC-KR) 인코딩 + FS & (2바이트 문자 모드)
- PRINTER_NAME 이 비어 있으면 출력을 건너뛴다 (개발 환경 보호).
- 출력 실패는 예외를 밖으로 던지지 않는다 — 결제 흐름에 영향 금지.
"""
 
import asyncio
from datetime import datetime
from typing import Optional
 
from pydantic import BaseModel, Field
 
from app.core.settings import settings
from app.db.models.orders import Orders
 
 
# ──────────────────────────────────────────────────────────────
# 출력 폭 (Font A 기준 열 수)
#   CPP-3000 (80mm 용지 / 72mm 인쇄폭) 은 보통 48열.
#   실제 출력에서 줄이 어긋나면 42 로 조정할 것.
# ──────────────────────────────────────────────────────────────
RECEIPT_COLUMNS = 48
 
# ── ESC/POS 명령 ──────────────────────────────────────────────
_INIT = b"\x1b\x40"              # ESC @  프린터 초기화
_KOR_ON = b"\x1c\x26"            # FS &   2바이트(한글) 문자 모드
_ALIGN_LEFT = b"\x1b\x61\x00"    # ESC a 0
_ALIGN_CENTER = b"\x1b\x61\x01"  # ESC a 1
_SIZE_NORMAL = b"\x1d\x21\x00"   # GS ! 기본 크기
_SIZE_2X = b"\x1d\x21\x11"       # GS ! 가로2배 + 세로2배
_BOLD_ON = b"\x1b\x45\x01"       # ESC E 1
_BOLD_OFF = b"\x1b\x45\x00"      # ESC E 0
_FEED_4 = b"\x1b\x64\x04"        # ESC d 4  — 4줄 피드
_CUT = b"\x1d\x56\x42\x00"       # GS V 66 0 — 피드 후 부분 컷
 
_SEP = "-" * RECEIPT_COLUMNS + "\n"
 
# 주문유형 표시 매핑 (sessions.se_carry / memory OrderType 공용 값)
_ORDER_TYPE_LABEL = {
    "STORE": "매장",
    "TAKEOUT": "포장",
}
 
 
# ──────────────────────────────────────────────────────────────
# 영수증 데이터 모델
# ──────────────────────────────────────────────────────────────
class ReceiptOption(BaseModel):
    name: str        # 옵션 이름
    price: int       # 옵션 1개당 추가금
    qty: int         # 개수 (샷 2개 → qty=2)
 
 
class ReceiptItem(BaseModel):
    name: str                                            # 메뉴명
    qty: int                                             # 수량
    amount: int                                          # 항목 합계 (옵션 포함 단가 × 수량)
    options: list[ReceiptOption] = Field(default_factory=list)
 
 
class ReceiptData(BaseModel):
    od_id: int                       # 주문 PK (재출력 키)
    od_no: int                       # 주문번호 (고객 안내용)
    order_type: Optional[str] = None # "매장" / "포장"
    paid_at: datetime                # 결제 시각
    total_price: int                 # 합계
    items: list[ReceiptItem] = Field(default_factory=list)
 
 
# ──────────────────────────────────────────────────────────────
# 내부 헬퍼
# ──────────────────────────────────────────────────────────────
def _enc(text: str) -> bytes:
    """CP949 인코딩 (한글 2바이트). 인코딩 불가 문자는 ? 처리."""
    return text.encode("cp949", errors="replace")
 
 
def _width(text: str) -> int:
    """출력 열 폭 — CP949 바이트 수 == 프린터 열 수 (한글 2칸)."""
    return len(_enc(text))
 
 
def _line(left: str, right: str = "") -> str:
    """왼쪽/오른쪽 정렬 한 줄 (폭 초과 시 최소 1칸 공백)."""
    pad = RECEIPT_COLUMNS - _width(left) - _width(right)
    return left + " " * max(pad, 1) + right
 
 
def _send_raw_sync(printer_name: str, data: bytes) -> None:
    """Windows 스풀러에 RAW 데이터 전송 (블로킹 — to_thread 로 호출할 것)."""
    import win32print  # pywin32. Windows 전용이라 함수 내부 import
 
    handle = win32print.OpenPrinter(printer_name)
    try:
        win32print.StartDocPrinter(handle, 1, ("VINUS_RECEIPT", None, "RAW"))
        try:
            win32print.StartPagePrinter(handle)
            win32print.WritePrinter(handle, data)
            win32print.EndPagePrinter(handle)
        finally:
            win32print.EndDocPrinter(handle)
    finally:
        win32print.ClosePrinter(handle)
 
 
# ──────────────────────────────────────────────────────────────
# Receipt 서비스
# ──────────────────────────────────────────────────────────────
class Receipt:
 
    # R - DB 주문(관계 로드 완료) → 영수증 데이터 변환
    #     get_paid_order_crud_order 로 조회한 Orders 를 받는다.
    @staticmethod
    def build_from_order_services_receipt(order: Orders) -> ReceiptData:
        items: list[ReceiptItem] = []
 
        for om in order.order_menus:
            # 옵션 행(1행=1개)을 op_id 기준으로 qty 압축
            opt_map: dict[int, ReceiptOption] = {}
            for omo in om.order_menu_options:
                if omo.op_id in opt_map:
                    opt_map[omo.op_id].qty += 1
                else:
                    opt_map[omo.op_id] = ReceiptOption(
                        name=omo.option.op_name,
                        price=omo.option.op_price,
                        qty=1,
                    )
            options = list(opt_map.values())
 
            unit_price = om.menu.m_price + sum(o.price * o.qty for o in options)
            items.append(
                ReceiptItem(
                    name=om.menu.m_name,
                    qty=om.o_m_qty,
                    amount=unit_price * om.o_m_qty,
                    options=options,
                )
            )
 
        se_carry = order.session.se_carry if order.session is not None else None
        order_type = _ORDER_TYPE_LABEL.get(se_carry.value) if se_carry else None
 
        return ReceiptData(
            od_id=order.od_id,
            od_no=order.od_no,
            order_type=order_type,
            paid_at=order.od_time or datetime.now(),
            total_price=order.od_price,
            items=items,
        )
 
    # R - 영수증 데이터 → ESC/POS 바이트 렌더링
    @staticmethod
    def render_escpos_services_receipt(data: ReceiptData) -> bytes:
        buf = bytearray()
        buf += _INIT + _KOR_ON
 
        # 상호 — 가운데 / 2배 크기
        buf += _ALIGN_CENTER + _SIZE_2X
        buf += _enc(f"{settings.store_name}\n")
        buf += _SIZE_NORMAL + _enc("\n")
 
        # 주문번호 — 가운데 / 2배 크기 (고객 픽업 안내용)
        buf += _SIZE_2X + _enc(f"주문번호 {data.od_no}\n") + _SIZE_NORMAL
 
        # 주문 정보
        buf += _ALIGN_LEFT + _enc(_SEP)
        buf += _enc(_line("결제일시", data.paid_at.strftime("%Y-%m-%d %H:%M:%S")) + "\n")
        if data.order_type:
            buf += _enc(_line("주문유형", data.order_type) + "\n")
        buf += _enc(_SEP)
 
        # 주문 항목
        for item in data.items:
            buf += _enc(_line(f"{item.name} x{item.qty}", f"{item.amount:,}") + "\n")
            for opt in item.options:
                buf += _enc(
                    _line(f" + {opt.name} x{opt.qty}", f"(+{opt.price * opt.qty:,})") + "\n"
                )
 
        # 합계
        buf += _enc(_SEP)
        buf += _BOLD_ON + _enc(_line("합계", f"{data.total_price:,}원") + "\n") + _BOLD_OFF
        buf += _enc(_SEP)
 
        # 푸터 + 컷
        buf += _ALIGN_CENTER + _enc("이용해 주셔서 감사합니다\n")
        buf += _FEED_4 + _CUT
        return bytes(buf)
 
    # C - 영수증 출력 (비동기, 예외 삼킴 → 성공 여부만 반환)
    @staticmethod
    async def print_services_receipt(data: ReceiptData) -> bool:
        printer_name = settings.printer_name
        if not printer_name:
            print("[RECEIPT] PRINTER_NAME 미설정 — 출력 건너뜀")
            return False
 
        try:
            payload = Receipt.render_escpos_services_receipt(data)
            await asyncio.to_thread(_send_raw_sync, printer_name, payload)
            print(f"[RECEIPT] 출력 완료: od_id={data.od_id}, od_no={data.od_no}")
            return True
        except Exception as e:
            print(f"[RECEIPT] 출력 실패: od_id={data.od_id} — {e}")
            return False