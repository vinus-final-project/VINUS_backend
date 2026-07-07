# app/ai/ruleEngine/ruleParser.py
import csv
import os
import re
from typing import List, Optional

from app.interface.dto.parseResult import ParseResult


class RuleParser:
    # ===== 변수 선언 =====
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # rapidfuzz 폴더의 menus.csv 재사용 (RapidFuzz 사전과 동일 소스)
    menus_csv_path = os.path.join(base_dir, "..", "rapidfuzz", "menus.csv")

    menu_names: List[str] = []               # 메뉴명 사전 (긴 이름 우선 매칭용 정렬)

    # R003 — 필수 옵션 별칭 → 표준값
    # [변경 #8] "차가운 걸로" 등 추가 / "얼음" 계열은 얼음량 옵션과 충돌하므로 제외
    temperature_alias = {
        "아이스": "ICE", "차갑게": "ICE", "시원하게": "ICE", "차가운": "ICE",
        "시원한": "ICE", "찹게": "ICE", "차가운 걸로": "ICE", "시원한 걸로": "ICE",
        "핫": "HOT", "따뜻하게": "HOT", "따숩게": "HOT", "뜨겁게": "HOT",
        "데워서": "HOT", "뜨신거": "HOT", "따뜻한": "HOT", "뜨거운": "HOT",
        "따신": "HOT", "뜨숩게": "HOT", "뜨뜻하게": "HOT", "따뜻한 걸로": "HOT",
    }
    size_alias = {
        "라지": "라지", "크게": "라지", "큰": "라지", "큰거": "라지", "큰걸로": "라지",
        "레귤러": "레귤러", "보통": "레귤러", "기본": "레귤러",
        "작은": "레귤러", "작은거": "레귤러", "작은걸로": "레귤러",
    }

    # R004 — 선택 옵션 키워드
    optional_keywords = ["바닐라 시럽", "헤이즐넛 시럽", "카라멜 시럽", "샷", "시럽", "휘핑"]

    # 옵션 제외 표현 — 옵션 키워드 "바로 뒤"에 붙는 경우만 제외로 판정 [변경 #1]
    exclude_markers = ["빼", "제외", "없이", "안 넣", "안넣", "넣지마"]

    # R005 — 선택 옵션 생략
    # [변경 #9] 오탐 위험 큰 범용 단어("아니", "끝", "그만", "됐다고" 등) 축소
    skip_keywords = ["안 할게", "안할게", "그대로 주세요", "그대로 해줘", "없어요", "괜찮아", "필요 없"]

    # R006~R010 — 장바구니
    cart_show_keywords = ["장바구니", "담은 메뉴", "담은 거", "고른 메뉴", "고른 거",
                          "담았던 거", "말한 거", "주문하려한거", "카트", "말한 것들", "아까 그것들"]
    cart_remove_keywords = ["삭제", "빼줘", "빼 줘", "제거", "없애", "지워", "지워줘"]
    cart_clear_keywords = ["전체 삭제", "비워", "다 빼"]
    cart_increase_keywords = ["하나 더", "한 개 더", "추가로 하나", "증가", "한 잔 더"]
    cart_decrease_keywords = ["하나 빼", "한 개 빼", "감소", "줄여", "한 잔 빼"]

    # R011 — 결제
    # [변경 #5] "끝났어" 제거 — "추천 끝났어" 같은 문장 오탐 방지
    payment_keywords = ["결제", "계산", "주문 완료"]

    # R012~R013 — 추천
    recommend_request_keywords = ["추천", "골라줘봐", "맞는 거", "적당한 거", "레커멘드"]
    # [변경 #4] "이거"/"그거" 단독 제거 — 명세 L003(문맥 참조 표현은 LLM 담당)
    #           명확한 수락 표현만 유지
    recommend_accept_keywords = ["그걸로 할게", "그거로 할게", "추천 메뉴로", "그걸로 주세요", "그걸로 해줘"]

    # R014 — 정보 조회
    # [변경 #7] 가격/설명 질문 키워드 추가 — "아메리카노 얼마야?"가 ORDER로 새는 것 방지
    info_keywords = ["뭐 있어", "뭐가 있", "메뉴 알려", "메뉴 보여", "어떤 메뉴"]
    info_question_keywords = ["얼마", "가격", "뭐야", "뭐예요", "어떤 거야", "설명", "알려줘", "들어가"]

    # R015 — 주문 유형
    order_type_alias = {
        "매장": "STORE", "먹고 갈": "STORE", "여기서": "STORE", "마시고 갈": "STORE",
        "포장": "TAKEOUT", "가져갈": "TAKEOUT", "테이크아웃": "TAKEOUT", "들고 갈": "TAKEOUT", "테이크어웨이": "TAKEOUT"
    }

    # R016 — 세션 취소
    cancel_keywords = ["취소", "처음부터", "그만할래", "그만둘래"]

    # 수량 표현 (R002)
    korean_number = {
        "한": 1, "하나": 1, "두": 2, "둘": 2, "세": 3, "셋": 3,
        "네": 4, "넷": 4, "다섯": 5, "여섯": 6, "일곱": 7, "여덟": 8, "아홉": 9, "열": 10,
    }

    # ===== 함수 정의 =====
    # 메뉴 사전 로드 (모듈 import 시 1회)
    @staticmethod
    def init_ruleengine_ruleparser() -> None:
        path = os.path.abspath(RuleParser.menus_csv_path)
        if not os.path.exists(path):
            RuleParser.menu_names = []
            return
        names = []
        with open(path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                value = row.get("m_name", "").strip()
                if value:
                    names.append(value)
        # 긴 이름 우선 ("디카페인 바닐라라떼"가 "바닐라라떼"보다 먼저 매칭되게)
        RuleParser.menu_names = sorted(names, key=len, reverse=True)

    # 텍스트에서 메뉴명 찾기 (R001)
    # [변경 #2, #10] 공백 전부 제거한 텍스트로 "기본" 비교 ("아 메 리 카 노" 대응)
    #               + 발견된 메뉴를 "전부" 리스트로 반환 (2개 이상 감지용)
    @staticmethod
    def find_menu_ruleengine_ruleparser(text: str) -> List[str]:
        compact_text = text.replace(" ", "")
        found_menus = []
        for menu_name in RuleParser.menu_names:
            compact_menu = menu_name.replace(" ", "")
            if compact_menu in compact_text:
                found_menus.append(menu_name)
                # 중복 매칭 방지: 찾은 부분은 소비 처리
                # ("디카페인 바닐라라떼" 찾으면 그 안의 "바닐라라떼"가 또 잡히지 않게)
                compact_text = compact_text.replace(compact_menu, "", 1)
        return found_menus

    # 텍스트에서 수량 찾기 (R002)
    # [변경 #11] 숫자는 단위(잔/개/컵) 필수 — "2026년" 오탐 방지
    # [변경 #3] "둘 주세요"처럼 문장 중간의 단독 수사도 단어 경계로 인식
    @staticmethod
    def find_quantity_ruleengine_ruleparser(text: str) -> Optional[int]:
        # "하나 더"는 수량이 아니라 CART INCREASE라 제외
        if any(k in text for k in RuleParser.cart_increase_keywords):
            return None
        # 숫자 + 단위 필수 (2잔, 3개, 1컵) — 단위 없는 숫자는 수량으로 보지 않음
        match = re.search(r"(\d+)\s*(잔|개|컵)", text)
        if match:
            quantity = int(match.group(1))
            if quantity > 0:
                return quantity
        # 한글 수사 + 단위 (한 잔, 두 개)
        for word, number in RuleParser.korean_number.items():
            if re.search(rf"{word}\s*(잔|개|컵)", text):
                return number
        # 단독 수사 — 단어 경계 기준 ("둘 주세요", 문장 끝 "하나")
        # "둘러볼게" 같은 오탐 방지를 위해 앞뒤가 공백/문장경계인 경우만
        for word, number in RuleParser.korean_number.items():
            if re.search(rf"(^|\s){word}(\s|$)", text):
                return number
        return None

    # 파싱 진입점 — 텍스트 → ParseResult (해석 불가/복합 시 None → LLM 폴백)
    @staticmethod
    async def parse_ruleengine_ruleparser(text: str) -> Optional[ParseResult]:
        if not text:
            return None

        # 구두점 정리
        clean_text = re.sub(r"[.,!?~]", " ", text).strip()

        matched_intents = []   # (intent, entities) 후보 수집

        # 메뉴 감지 (여러 곳에서 쓰므로 먼저 1회 수행)
        found_menus = RuleParser.find_menu_ruleengine_ruleparser(clean_text)

        # [변경 #10] 메뉴 2개 이상 = 복합 발화 → 명세 시스템 정책("한 번에 메뉴 1개") 따라 LLM 폴백
        if len(found_menus) >= 2:
            print(f"[RuleParser] 메뉴 {len(found_menus)}개 감지 → LLM 폴백: {found_menus}")
            return None
        menu_name = found_menus[0] if found_menus else None

        # ---------- SESSION (R015, R016) ----------
        for alias, order_type in RuleParser.order_type_alias.items():
            if alias in clean_text:
                matched_intents.append(("SESSION", {"order_type": order_type}))
                break
        if any(k in clean_text for k in RuleParser.cancel_keywords):
            matched_intents.append(("SESSION", {"action": "CANCEL"}))

        # ---------- PAYMENT (R011) ----------
        if any(k in clean_text for k in RuleParser.payment_keywords):
            matched_intents.append(("PAYMENT", {"action": "START"}))

        # ---------- CART (R006~R010) ----------
        # 검사 순서 중요: 구체적 표현(전체 삭제) → 일반 표현(삭제) 순.
        # "하나 빼"(DECREASE)가 "빼줘"(REMOVE)보다 먼저 걸리는 것도 이 elif 순서가 보장 [#6]
        if any(k in clean_text for k in RuleParser.cart_clear_keywords):
            matched_intents.append(("CART", {"action": "CLEAR"}))
        elif any(k in clean_text for k in RuleParser.cart_show_keywords):
            matched_intents.append(("CART", {"action": "SHOW"}))
        elif any(k in clean_text for k in RuleParser.cart_increase_keywords):
            entities = {"action": "INCREASE"}
            if menu_name:
                entities["cart_item"] = menu_name
            matched_intents.append(("CART", entities))
        elif any(k in clean_text for k in RuleParser.cart_decrease_keywords):
            entities = {"action": "DECREASE"}
            if menu_name:
                entities["cart_item"] = menu_name
            matched_intents.append(("CART", entities))
        elif any(k in clean_text for k in RuleParser.cart_remove_keywords):
            # "휘핑 빼주세요"(옵션 제외)와 "아메리카노 빼줘"(장바구니 삭제) 구분:
            # 옵션 키워드가 함께 있으면 CART 삭제가 아님
            if not any(k in clean_text for k in RuleParser.optional_keywords):
                entities = {"action": "REMOVE"}
                if menu_name:
                    entities["cart_item"] = menu_name
                matched_intents.append(("CART", entities))

        # ---------- RECOMMEND (R012, R013) ----------
        if any(k in clean_text for k in RuleParser.recommend_accept_keywords):
            matched_intents.append(("RECOMMEND", {"action": "ACCEPT"}))
        elif any(k in clean_text for k in RuleParser.recommend_request_keywords):
            matched_intents.append(("RECOMMEND", {"action": "REQUEST", "condition": clean_text}))

        # ---------- INFO (R014) ----------
        if any(k in clean_text for k in RuleParser.info_keywords):
            matched_intents.append(("INFO", {"type": "MENU"}))
        # [변경 #7] 메뉴 + 질문 키워드("얼마", "뭐야" 등) = 정보 질문 → ORDER 아닌 INFO
        elif menu_name and any(k in clean_text for k in RuleParser.info_question_keywords):
            matched_intents.append(("INFO", {"type": "MENU", "menu": menu_name}))

        # ---------- ORDER (R001~R005) ----------
        # [변경 #7] 정보 질문으로 이미 판정됐으면 ORDER 시도 안 함
        is_info_question = any(
            intent == "INFO" and "menu" in entities
            for (intent, entities) in matched_intents
        )

        order_entities = {}
        if not is_info_question:
            if menu_name:
                order_entities["menu"] = menu_name

            quantity = RuleParser.find_quantity_ruleengine_ruleparser(clean_text)
            if quantity:
                order_entities["quantity"] = quantity

            # 필수 옵션 (온도/사이즈) — 긴 별칭 우선
            for alias in sorted(RuleParser.temperature_alias, key=len, reverse=True):
                if alias in clean_text:
                    order_entities.setdefault("required_option", []).append(
                        RuleParser.temperature_alias[alias]
                    )
                    break
            for alias in sorted(RuleParser.size_alias, key=len, reverse=True):
                if alias in clean_text:
                    order_entities.setdefault("required_option", []).append(
                        RuleParser.size_alias[alias]
                    )
                    break

            # 선택 옵션 [변경 #1, #9]
            # 옵션 키워드별로 "추가"인지 "제외"인지 개별 판정:
            # 키워드 바로 뒤 5자 이내에 제외 표현(빼/없이/안 넣)이 붙으면 exclude,
            # 아니면 optional(추가). "샷은 빼고 휘핑 추가" → 샷=제외, 휘핑=추가
            for keyword in RuleParser.optional_keywords:
                position = clean_text.find(keyword)
                if position == -1:
                    continue
                after_text = clean_text[position + len(keyword): position + len(keyword) + 5]
                if any(marker in after_text for marker in RuleParser.exclude_markers):
                    order_entities.setdefault("exclude_option", []).append(keyword)
                else:
                    order_entities.setdefault("optional_option", []).append(keyword)

            # 선택 옵션 생략
            if any(k in clean_text for k in RuleParser.skip_keywords):
                order_entities["skip_optional"] = True

        if order_entities:
            matched_intents.append(("ORDER", order_entities))

        # ---------- Intent 판정 (명세: 1개만 허용) ----------
        if len(matched_intents) == 1:
            intent, entities = matched_intents[0]
            result = ParseResult(intent=intent, entities=entities, source="RULE")
            print(f"[RuleParser] intent={intent}, entities={entities}")
            return result

        # 0개(해석 불가) 또는 2개 이상(복합 발화) → LLM 폴백
        print(f"[RuleParser] 해석 불가/복합({len(matched_intents)}개) → LLM 폴백: {clean_text}")
        return None


# 모듈 import 시 메뉴 사전 1회 로드
RuleParser.init_ruleengine_ruleparser()