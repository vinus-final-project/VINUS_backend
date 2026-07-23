# app/ai/stt/whisperService.py
import asyncio
import os
import re
from collections import Counter

import numpy as np
import torch
from faster_whisper import WhisperModel

from app.ai.ruleEngine import rules  # 메뉴 사전 (initial_prompt 자동 생성용)


class WhisperService:
    # ===== 변수 선언 =====
    model_size = "large-v3-turbo"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if torch.cuda.is_available() else "int8"
    language = "ko"
    # device = os.getenv("STT_DEVICE", "cuda")
    # if device == "cuda" and not torch.cuda.is_available():
    #         raise RuntimeError(
    #             "[STT] CUDA(GPU)를 사용할 수 없습니다. "
    #             "CUDA용 PyTorch/드라이버 설치를 확인하거나, "
    #             "CPU로 실행하려면 환경변수 STT_DEVICE=cpu 를 설정하세요."
    #         )
    # compute_type = "float16" if device == "cuda" else "int8"
    # language = "ko"
    # 메뉴 인식 정확도 향상용 힌트 — menus.csv(메뉴 사전) 기반 자동 생성
    #   메뉴가 바뀌면 csv 만 갱신하면 프롬프트도 따라온다.
    #   ("곡물라떼→옥몰라테" 같은 오인식을 인식 단계에서 줄이는 목적)
    initial_prompt = (
        "카페 키오스크 주문입니다. 메뉴: "
        + ", ".join(rules.MENU_DICTIONARY.keys())
        + ". 옵션: 아이스, 핫, 따뜻하게, 시원하게, 레귤러, 라지, 샷 추가, "
        "바닐라 시럽, 헤이즐넛 시럽, 카라멜 시럽, 휘핑 추가, 펄 추가, "
        "얼음 적게, 얼음 많이, 당도 50, 당도 100, 주세요, 빼주세요."
    )

    # ===== 할루시네이션 필터 =====
    # 세그먼트 품질 임계값 (Whisper 공식 휴리스틱 기반 — 실발화 로그 보고 조정)
    NO_SPEECH_PROB_MAX = 0.6    # 무음일 확률이 이보다 높으면 폐기
    AVG_LOGPROB_MIN = -1.0      # 인식 확신도가 이보다 낮으면 폐기
    COMPRESSION_RATIO_MAX = 2.4 # 반복(루프 환각) 지표가 이보다 높으면 폐기

    # 무음/잡음에서 튀어나오는 대표 환각 문구 (발화 전체가 일치할 때만 폐기)
    HALLUCINATION_BLACKLIST = (
        "감사합니다", "고맙습니다", "감사합니다 감사합니다",
        "시청해주셔서 감사합니다", "시청해 주셔서 감사합니다",
        "구독과 좋아요", "구독 부탁드립니다", "좋아요와 구독",
        "다음 영상에서 만나요", "다음 시간에 만나요",
        "자막 제공", "한글자막", "수고하셨습니다", "아멘",
    )

    # 반복 감지: 동일 토큰 비율이 이보다 크면 루프 환각으로 판정
    REPEAT_TOKEN_RATIO_MAX = 0.5
    REPEAT_MIN_TOKENS = 6       # 짧은 발화는 반복 판정 제외

    # 모델 (지연 로딩 싱글톤 — uvicorn --reload 시 reloader 프로세스의
    #  중복 로드 방지. 실제 서버 프로세스에서 lifespan 웜업으로 1회 로드)
    model = None

    @classmethod
    def get_model_stt_whisper(cls) -> WhisperModel:
        if cls.model is None:
            cls.model = WhisperModel(
                cls.model_size, device=cls.device, compute_type=cls.compute_type,
            )
            print(f"[STT] WhisperModel 로드 완료 — device={cls.device}, compute_type={cls.compute_type}")
        return cls.model

    # ===== 함수 정의 =====
    # PCM int16 bytes → float32 numpy 변환
    @staticmethod
    def convert_stt_whisper(pcm_bytes: bytes) -> np.ndarray:
        audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        # 방어: 혹시 범위 밖 값이 있어도 -1.0~1.0 보장
        audio_float32 = np.clip(audio_float32, -1.0, 1.0)
        return audio_float32

    # ------------------------------------------------------------------
    # 할루시네이션 판정 도우미
    # ------------------------------------------------------------------
    @staticmethod
    def _normalize_for_blacklist_stt_whisper(text: str) -> str:
        """블랙리스트 비교용 정규화 — 문장부호/공백 제거."""
        return re.sub(r"[\s.,!?~…'\"]+", "", text)

    @staticmethod
    def _is_hallucination_stt_whisper(text: str) -> bool:
        """최종 텍스트 단위 환각 판정 (블랙리스트 전체 일치 / 토큰 반복)."""
        # 1) 블랙리스트 — 발화 "전체"가 환각 문구와 일치할 때만
        #    ("네 감사합니다 결제할게요" 같은 정상 발화는 통과)
        normalized = WhisperService._normalize_for_blacklist_stt_whisper(text)
        for phrase in WhisperService.HALLUCINATION_BLACKLIST:
            if normalized == WhisperService._normalize_for_blacklist_stt_whisper(phrase):
                return True

        # 2) 토큰 반복 — 같은 단어가 과반이면 루프 환각
        tokens = text.split()
        if len(tokens) >= WhisperService.REPEAT_MIN_TOKENS:
            most_common = Counter(tokens).most_common(1)[0][1]
            if most_common / len(tokens) > WhisperService.REPEAT_TOKEN_RATIO_MAX:
                return True

        return False

    # 실제 Whisper 추론 (동기) — to_thread로 감싸서 호출됨
    @staticmethod
    def run_stt_whisper(pcm_bytes: bytes) -> str:
        audio_data = WhisperService.convert_stt_whisper(pcm_bytes)

        segments, _info = WhisperService.get_model_stt_whisper().transcribe(
            audio_data,
            language=WhisperService.language,
            beam_size=1,                        # 키오스크: 속도 우선 (turbo는 1로도 충분)
            temperature=[0.0, 0.2, 0.4],        # 기본 0.0, 반복 루프 감지 시 fallback 탈출
            condition_on_previous_text=False,   # 발화 단건 처리 — 이전 문맥 연결 차단(환각 방지)
            vad_filter=False,                   # VAD는 백엔드 VadSegmenter 가 수행
            initial_prompt=WhisperService.initial_prompt,
        )

        # 세그먼트 품질 필터 — 무음 확률/확신도/반복 지표로 환각 세그먼트 폐기
        pieces = []
        for seg in segments:
            if seg.no_speech_prob > WhisperService.NO_SPEECH_PROB_MAX:
                print(f"[STT] 세그먼트 폐기(no_speech {seg.no_speech_prob:.2f}): {seg.text}")
                continue
            if seg.avg_logprob < WhisperService.AVG_LOGPROB_MIN:
                print(f"[STT] 세그먼트 폐기(logprob {seg.avg_logprob:.2f}): {seg.text}")
                continue
            if seg.compression_ratio > WhisperService.COMPRESSION_RATIO_MAX:
                print(f"[STT] 세그먼트 폐기(반복 {seg.compression_ratio:.2f}): {seg.text}")
                continue
            pieces.append(seg.text)

        text = "".join(pieces).strip()

        # 최종 텍스트 환각 판정 (블랙리스트 / 토큰 반복)
        if text and WhisperService._is_hallucination_stt_whisper(text):
            print(f"[STT] 환각 판정 폐기: {text}")
            return ""

        return text

    # STT 진입점 — PCM Binary를 한국어 텍스트로 변환 (비동기)
    @staticmethod
    async def transcribe_stt_whisper(pcm_bytes: bytes, sample_rate: int = 16000) -> str:
        if not pcm_bytes:
            print("[STT] 입력 PCM 없음 → 빈 텍스트 반환")
            return ""

        # 명세상 16kHz 고정 — 다른 값이 오면 경고 (리샘플링은 상위에서)
        if sample_rate != 16000:
            print(f"[STT] 경고: sample_rate={sample_rate}, 16000 가정과 다름")

        # 동기 추론을 별도 스레드로 실행 — 이벤트 루프 블로킹 방지 (동시 요청 대비)
        transcribed_text = await asyncio.to_thread(
            WhisperService.run_stt_whisper, pcm_bytes
        )

        # 테스트용 — STT 결과 확인
        print(f"[STT] 변환 결과: {transcribed_text}")

        return transcribed_text