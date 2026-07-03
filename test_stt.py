# test_stt.py  (backend 루트)
import asyncio
import wave
import numpy as np
from app.ai.stt.whisperService import WhisperService


WAV_PATH = "test.wav"   # 네 wav 파일명


def load_wav_as_pcm(wav_path: str) -> bytes:
    """wav 파일을 읽어 16kHz/mono/16bit PCM bytes로 변환"""
    with wave.open(wav_path, "rb") as wf:
        channels = wf.getnchannels()
        sample_rate = wf.getframerate()
        sample_width = wf.getsampwidth()
        n_frames = wf.getnframes()

        print(f"[WAV 정보] 채널={channels}, 샘플레이트={sample_rate}Hz, "
              f"샘플폭={sample_width*8}bit, 길이={n_frames/sample_rate:.2f}초")

        raw = wf.readframes(n_frames)

    if sample_width != 2:
        print(f"[경고] 16bit(2byte)가 아님({sample_width}byte).")

    audio = np.frombuffer(raw, dtype=np.int16)

    # 스테레오 → 모노
    if channels == 2:
        print("[변환] 스테레오 → 모노")
        audio = audio.reshape(-1, 2).mean(axis=1).astype(np.int16)

    # 16kHz로 리샘플링 (핵심!)
    if sample_rate != 16000:
        print(f"[변환] {sample_rate}Hz → 16000Hz 리샘플링")
        target_len = int(len(audio) * 16000 / sample_rate)
        indices = np.linspace(0, len(audio) - 1, target_len)
        audio = np.interp(indices, np.arange(len(audio)), audio).astype(np.int16)

    return audio.tobytes()


async def main():
    pcm = load_wav_as_pcm(WAV_PATH)
    print(f"[PCM] {len(pcm)} bytes 준비됨")
    result = await WhisperService.transcribe_stt_whisper(pcm)
    print(f"\n=== 최종 결과: {result} ===")


asyncio.run(main())