# app/ai/rapidfuzz/normalizer.py
import csv
import os
import re
from typing import List, Tuple

from rapidfuzz import process, fuzz


class Normalizer:
    # ===== 변수 선언 =====
    base_dir = os.path.dirname(os.path.abspath(__file__))
    menus_csv_path = os.path.join(base_dir, "menus.csv")
    options_csv_path = os.path.join(base_dir, "options.csv")

    score_threshold = 85      # 자모 기준 유사도 임계값(0~100)
    min_token_length = 2      # 너무 짧은 단일 토큰은 보정 제외
    max_ngram = 3             # 띄어쓰기 묶음 최대 단어 수
    ngram_tolerance = 5       # 묶음이 단독보다 이 점수 이내로 낮으면 묶음 우선

    # 수량 토큰 판정 — 숫자와 동일하게 묶음 병합에서 제외할 한글 수사
    #   ("메이플 크룽지 두 개" 의 "두" 가 메뉴명 3-gram 에 먹혀 사라지는
    #    문제 방지. 완전일치 패턴이라 "세트"/"열대" 같은 일반 단어는 무관)
    qty_token_re = re.compile(
        r"^(?:\d+|하나|둘|셋|넷|다섯|여섯|일곱|여덟|아홉|열|한|두|세|네)"
        r"(?:개|잔|번|장|명)?$"
    )

    # 한글 유니코드 자모 테이블
    chosung_list = [
        "ㄱ", "ㄲ", "ㄴ", "ㄷ", "ㄸ", "ㄹ", "ㅁ", "ㅂ", "ㅃ", "ㅅ",
        "ㅆ", "ㅇ", "ㅈ", "ㅉ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    ]
    jungsung_list = [
        "ㅏ", "ㅐ", "ㅑ", "ㅒ", "ㅓ", "ㅔ", "ㅕ", "ㅖ", "ㅗ", "ㅘ",
        "ㅙ", "ㅚ", "ㅛ", "ㅜ", "ㅝ", "ㅞ", "ㅟ", "ㅠ", "ㅡ", "ㅢ", "ㅣ",
    ]
    jongsung_list = [
        "", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ",
        "ㄻ", "ㄼ", "ㄽ", "ㄾ", "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ",
        "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ",
    ]

    # 사전: (원본, 자모변환) 쌍 — 모듈 import 시 1회 로드
    dictionary: List[Tuple[str, str]] = []
    # 자모 문자열만 뽑은 리스트 (RapidFuzz 검색 대상)
    dictionary_jamo: List[str] = []

    # 자모 혼동 접기(folding) — 발음상 헷갈리는 자모를 같은 문자로 접어서 비교
    #   ("옥몰라테"→"곡물라떼": ㅌ↔ㄸ, ㅗ↔ㅜ 접으면 유사도 70→90 으로 상승)
    #   비교 전용이며 치환 결과는 항상 원본 표준명 사용. 임계값은 그대로 85.
    jamo_fold_map = str.maketrans({
        # 격음/경음 → 평음 (STT 혼동 잦음)
        "ㅋ": "ㄱ", "ㄲ": "ㄱ",
        "ㅌ": "ㄷ", "ㄸ": "ㄷ",
        "ㅍ": "ㅂ", "ㅃ": "ㅂ",
        "ㅊ": "ㅈ", "ㅉ": "ㅈ",
        "ㅆ": "ㅅ",
        # 모음 혼동
        "ㅜ": "ㅗ", "ㅐ": "ㅔ", "ㅒ": "ㅖ",
    })

    # ===== 함수 정의 =====
    # 한글 음절을 자모로 분해 (한글 아닌 글자는 그대로)
    @staticmethod
    def decompose_rapidfuzz_normalizer(text: str) -> str:
        result = []
        for char in text:
            code = ord(char)
            # 한글 음절 범위(가~힣)
            if 0xAC00 <= code <= 0xD7A3:
                offset = code - 0xAC00
                chosung_index = offset // 588
                jungsung_index = (offset % 588) // 28
                jongsung_index = offset % 28
                result.append(Normalizer.chosung_list[chosung_index])
                result.append(Normalizer.jungsung_list[jungsung_index])
                result.append(Normalizer.jongsung_list[jongsung_index])
            else:
                # 한글이 아니면(영문/숫자) 그대로
                result.append(char)
        return "".join(result)

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
        all_terms = menu_terms + option_terms

        # (원본, 접은 자모) 쌍으로 저장 + 접은 자모만 별도 리스트
        #   비교는 folded 자모끼리, 치환은 원본 표준명으로
        Normalizer.dictionary = [
            (
                term,
                Normalizer.decompose_rapidfuzz_normalizer(term).translate(
                    Normalizer.jamo_fold_map
                ),
            )
            for term in all_terms
        ]
        Normalizer.dictionary_jamo = [
            jamo for (_, jamo) in Normalizer.dictionary
        ]

    # 보정 — STT 텍스트의 메뉴명/옵션명 오인식을 표준명으로 치환
    @staticmethod
    async def normalize_rapidfuzz_normalizer(text: str) -> str:
        if not text or not Normalizer.dictionary:
            print(f"[RapidFuzz] 보정 생략(빈 입력 또는 사전 없음): {text}")
            return text

        tokens = text.split()
        normalized_tokens = []
        index = 0

        while index < len(tokens):
            max_window = min(Normalizer.max_ngram, len(tokens) - index)

            # window별 매칭 점수 계산 (자모 기준)
            window_results = {}   # window 크기 → (원본표준명, 점수)
            for window in range(1, max_window + 1):
                phrase_tokens = tokens[index:index + window]
                candidate = "".join(phrase_tokens)

                if window == 1 and len(candidate) < Normalizer.min_token_length:
                    continue

                # 수량 토큰(숫자/한글 수사)은 묶음 병합에서 제외
                #   ("바닐라 시럽 2개" → "바닐라 시럽", "메이플 크룽지 두 개"
                #    → "메이플 크룽지 개" 처럼 수량이 사라지는 문제 방지
                #    — 수량 토큰은 그대로 통과시킨다)
                if window > 1 and any(
                    any(ch.isdigit() for ch in tok)
                    or Normalizer.qty_token_re.match(tok)
                    for tok in phrase_tokens
                ):
                    continue

                # 후보를 자모로 변환 + 혼동 접기 후 사전(접은 자모)과 비교
                candidate_jamo = Normalizer.decompose_rapidfuzz_normalizer(
                    candidate
                ).translate(Normalizer.jamo_fold_map)
                match = process.extractOne(
                    candidate_jamo,
                    Normalizer.dictionary_jamo,
                    scorer=fuzz.ratio,
                )
                if match is not None:
                    # match = (자모문자열, 점수, 인덱스) → 인덱스로 원본 표준명 조회
                    matched_index = match[2]
                    original_term = Normalizer.dictionary[matched_index][0]
                    window_results[window] = (original_term, match[1])

            # 단독(window=1) 점수 — 비교 기준
            single_score = window_results.get(1, (None, 0))[1]

            # 긴 묶음부터 검사
            chosen_term = None
            chosen_window = 1
            for window in range(max_window, 0, -1):
                if window not in window_results:
                    continue
                term, score = window_results[window]

                if score < Normalizer.score_threshold:
                    continue
                if score >= single_score - Normalizer.ngram_tolerance:
                    chosen_term = term
                    chosen_window = window
                    break

            if chosen_term is not None:
                normalized_tokens.append(chosen_term)
                index += chosen_window
            else:
                normalized_tokens.append(tokens[index])
                index += 1

        normalized_text = " ".join(normalized_tokens)

        # 테스트용 — 보정 전/후 비교
        print(f"[RapidFuzz] 보정 전: {text}")
        print(f"[RapidFuzz] 보정 후: {normalized_text}")

        return normalized_text


# 모듈 import 시 사전 1회 로드
Normalizer.init_rapidfuzz_normalizer()