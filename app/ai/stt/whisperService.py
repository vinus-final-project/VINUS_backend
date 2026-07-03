# app/ai/stt/whisperService.py
import numpy as np
import torch
from faster_whisper import WhisperModel


class WhisperService:
    # ===== 변수 선언 =====
    model_size = "large-v3-turbo"
    device = "cuda" if torch.cuda.is_available() else "cpu"
    compute_type = "float16" if torch.cuda.is_available() else "int8"
    language = "ko"

    # 메뉴 인식 정확도 향상용 힌트 (Whisper에 도메인 맥락 제공)
    initial_prompt = (
        "카페 음료 주문입니다. "
        "아메리카노, 카페라떼, 바닐라라떼, 카라멜마끼아또, 아인슈페너, "
        "흑당카페라떼, 녹차라떼, 초코라떼, 딸기스무디, 아이스, 핫, 라지, 휘핑, 샷추가."
    )

    # 모델 로드 (클래스 정의 시 1회 — 싱글톤)
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    # ===== 함수 정의 =====
    # PCM int16 bytes → float32 numpy 변환
    @staticmethod
    def convert_stt_whisper(pcm_bytes: bytes) -> np.ndarray:
        audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        return audio_float32

    # STT — PCM Binary를 한국어 텍스트로 변환
    @staticmethod
    async def transcribe_stt_whisper(pcm_bytes: bytes, sample_rate: int = 16000) -> str:
        if not pcm_bytes:
            print("[STT] 입력 PCM 없음 → 빈 텍스트 반환")
            return ""

        audio_data = WhisperService.convert_stt_whisper(pcm_bytes)

        # faster-whisper 추론(동기 라이브러리)
        segments, _info = WhisperService.model.transcribe(
            audio_data,
            language=WhisperService.language,
            beam_size=5,
            vad_filter=False,
            initial_prompt=WhisperService.initial_prompt,
        )

        transcribed_text = "".join(seg.text for seg in segments).strip()

        # 테스트용 — STT 결과 확인
        print(f"[STT] 변환 결과: {transcribed_text}")

        return transcribed_text