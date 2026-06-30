# app/ai/rapidfuzz/normalizer.py
import csv
import os
from typing import List

from rapidfuzz import process, fuzz


class Normalizer:
    # ===== 변수 선언 =====
    base_dir = os.path.dirname(os.path.abspath(__file__))
    menus_csv_path = os.path.join(base_dir, "menus.csv")
    options_csv_path = os.path.join(base_dir, "options.csv")

    score_threshold = 80      # 보정 유사도 임계값(0~100)
    min_token_length = 2      # 너무 짧은 토큰은 보정 제외

    # 사전(메뉴명+옵션명) — 모듈 import 시 1회 로드
    dictionary: List[str] = []

    # ===== 함수 정의 =====
    # CSV 지정 컬럼 값들을 리스트로 반환
    @staticmethod
    def load_rapidfuzz_normalizer(csv_path: str, column_name: str) -> List[str]:
        if not os.path.exists(csv_path):
            return []
        term_list = []
        with open(csv_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                value = row.get(column_name, "").strip()
                if value:
                    term_list.append(value)
        return term_list

    # 사전 초기화 (모듈 import 시 1회 호출)
    @staticmethod
    def init_rapidfuzz_normalizer() -> None:
        menu_terms = Normalizer.load_rapidfuzz_normalizer(
            Normalizer.menus_csv_path, "m_name"
        )
        option_terms = Normalizer.load_rapidfuzz_normalizer(
            Normalizer.options_csv_path, "op_name"
        )
        Normalizer.dictionary = menu_terms + option_terms

    # 보정 — STT 텍스트의 메뉴명/옵션명 오인식을 표준명으로 치환
    @staticmethod
    async def normalize_rapidfuzz_normalizer(text: str) -> str:
        if not text or not Normalizer.dictionary:
            print(f"[RapidFuzz] 보정 생략(빈 입력 또는 사전 없음): {text}")
            return text

        tokens = text.split()
        normalized_tokens = []

        for token in tokens:
            if len(token) < Normalizer.min_token_length:
                normalized_tokens.append(token)
                continue

            match = process.extractOne(
                token,
                Normalizer.dictionary,
                scorer=fuzz.ratio,
                score_cutoff=Normalizer.score_threshold,
            )

            if match is None:
                normalized_tokens.append(token)
            else:
                normalized_tokens.append(match[0])

        normalized_text = " ".join(normalized_tokens)

        # 테스트용 — 보정 전/후 비교
        print(f"[RapidFuzz] 보정 전: {text}")
        print(f"[RapidFuzz] 보정 후: {normalized_text}")

        return normalized_text


# 모듈 import 시 사전 1회 로드
Normalizer.init_rapidfuzz_normalizer()