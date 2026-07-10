# app/ai/stt/whisperService.py
import asyncio
import os

import numpy as np
import torch
from faster_whisper import WhisperModel


class WhisperService:
    # ===== 변수 선언 =====
    model_size = "large-v3-turbo"
    # device = "cuda" if torch.cuda.is_available() else "cpu"
    # compute_type = "float16" if torch.cuda.is_available() else "int8"
        # language = "ko"
    device = os.getenv("STT_DEVICE", "cuda")
    if device == "cuda" and not torch.cuda.is_available():
            raise RuntimeError(
                "[STT] CUDA(GPU)를 사용할 수 없습니다. "
                "CUDA용 PyTorch/드라이버 설치를 확인하거나, "
                "CPU로 실행하려면 환경변수 STT_DEVICE=cpu 를 설정하세요."
            )
    compute_type = "float16" if device == "cuda" else "int8"
    language = "ko"
    # 메뉴 인식 정확도 향상용 힌트 (seed 실제 메뉴 기준)
    initial_prompt = (
        "카페 음료 주문입니다. "
        "아메리카노, 에스프레소, 카페라떼, 카푸치노, 바닐라라떼, 헤이즐넛라떼, "
        "카라멜마끼아또, 카페모카, 연유라떼, 흑당카페라떼, 돌체라떼, 아인슈페너, "
        "달고나라떼, 꿀아메리카노, 더치라떼, 디카페인, "
        "녹차라떼, 초코라떼, 딸기 스무디, 복숭아 아이스티, 요거트 스무디, "
        "아이스, 핫, 따뜻하게, 따숩게, 시원하게, 차갑게, 뜨겁게, "
        "레귤러, 라지, 샷 추가, 시럽 추가, 휘핑 추가, 휘핑 빼주세요."
    )

    # 모델 로드 (클래스 정의 시 1회 — 싱글톤)
    model = WhisperModel(model_size, device=device, compute_type=compute_type)

    print(f"[STT] WhisperModel 로드 완료 — device={device}, compute_type={compute_type}")

    # ===== 함수 정의 =====
    # PCM int16 bytes → float32 numpy 변환
    @staticmethod
    def convert_stt_whisper(pcm_bytes: bytes) -> np.ndarray:
        audio_int16 = np.frombuffer(pcm_bytes, dtype=np.int16)
        audio_float32 = audio_int16.astype(np.float32) / 32768.0
        # 방어: 혹시 범위 밖 값이 있어도 -1.0~1.0 보장
        audio_float32 = np.clip(audio_float32, -1.0, 1.0)
        return audio_float32

    # 실제 Whisper 추론 (동기) — to_thread로 감싸서 호출됨
    @staticmethod
    def run_stt_whisper(pcm_bytes: bytes) -> str:
        audio_data = WhisperService.convert_stt_whisper(pcm_bytes)

        segments, _info = WhisperService.model.transcribe(
            audio_data,
            language=WhisperService.language,
            beam_size=1,                        # 키오스크: 속도 우선 (turbo는 1로도 충분)
            temperature=[0.0, 0.2, 0.4],        # 기본 0.0, 반복 루프 감지 시 fallback 탈출
            condition_on_previous_text=False,   # 발화 단건 처리 — 이전 문맥 연결 차단(환각 방지)
            vad_filter=False,                   # VAD는 프론트에서 수행
            initial_prompt=WhisperService.initial_prompt,
        )

        return "".join(seg.text for seg in segments).strip()

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