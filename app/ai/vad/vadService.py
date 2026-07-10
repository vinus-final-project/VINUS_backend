# app/ai/vad/vadService.py
#
# WebRTC VAD 기반 발화 검증/분리
#
# 현재 구조 (발화 단위 전송):
#   frontend Noise Gate 가 SP(임계 돌파)~EP(hangover 소진) 구간을
#   발화 하나로 잘라 Binary 1개로 보낸다.
#   → backend 는 filter_utterance_vad_vadService() 로 이 세그먼트가
#     진짜 음성인지 "검증 + 앞뒤 무음 트리밍"만 수행한 뒤 STT 로 넘긴다.
#
#   pcm = filter_utterance_vad_vadService(binary)
#   if pcm: text = await WhisperService.transcribe_stt_whisper(pcm)
#
# (구) 연속 스트림 구조용 VadSegmenter(feed/flush)도 하위에 유지 —
#   스트리밍 방식으로 되돌릴 경우를 대비한 보존용.
#
# 요구 패키지: webrtcvad-wheels  (pip install webrtcvad-wheels)
#   ※ py-webrtcvad 의 프리컴파일(wheel) 포크 — C 빌드 도구 없이 설치 가능.
#     패키지명만 다르고 import 모듈명은 동일하게 `webrtcvad` 를 사용한다.
#
# 튜닝 포인트:
#   AGGRESSIVENESS      0(관대)~3(엄격). 잡음 많은 환경 → 3
#   MIN_VOICE_MS        세그먼트 내 음성 프레임 총합이 이보다 짧으면 폐기
#   TRIM_PAD_FRAMES     트리밍 시 앞뒤로 남겨둘 여유 프레임
#   MIN_UTTER_BYTES     최종 발화 최소 길이 (환각 방지)

import webrtcvad

SAMPLE_RATE = 16000
FRAME_MS = 20                                   # webrtcvad 허용: 10/20/30ms
FRAME_BYTES = SAMPLE_RATE * FRAME_MS // 1000 * 2  # 640 bytes (Int16)

AGGRESSIVENESS = 3
MIN_VOICE_MS = 300          # 세그먼트 안 음성 프레임 총합 최소 (300ms)
                            #   — 문 닫는 소리 등 비음성 잡음 세그먼트 폐기
TRIM_PAD_FRAMES = 5         # 트리밍 시 첫/마지막 음성 프레임 앞뒤 여유 (100ms)
MIN_UTTER_BYTES = 16000     # 최종 발화 0.5초 미만 폐기 (환각 방지)

# (구) 스트림 세그먼터용
START_VOICE_FRAMES = 5      # 100ms 연속 음성 → 발화 시작
END_SILENCE_FRAMES = 20     # 400ms 연속 무음 → 발화 종료
PREROLL_FRAMES = 5          # 100ms pre-roll

# 세그먼트 검증용 공용 VAD 인스턴스 (stateless 판정이라 공유 가능)
_vad_checker = webrtcvad.Vad(AGGRESSIVENESS)


def filter_utterance_vad_vadService(pcm: bytes) -> bytes | None:
    """발화 세그먼트(SP~EP) 검증 + 앞뒤 무음 트리밍.

    frontend Noise Gate 는 데시벨만 보므로 문 닫는 소리, 기침 같은
    비음성 잡음도 세그먼트로 올 수 있다. WebRTC VAD 로 프레임별
    음성 여부를 판정해서:
      1) 음성 프레임 총합 < MIN_VOICE_MS → None (비음성 잡음 폐기)
      2) 첫 음성 프레임 - PAD ~ 마지막 음성 프레임 + PAD 로 트리밍
      3) 트리밍 결과가 MIN_UTTER_BYTES 미만 → None
    """
    if not pcm or len(pcm) < FRAME_BYTES:
        return None

    # 20ms 프레임별 음성 판정
    n_frames = len(pcm) // FRAME_BYTES
    voice_flags: list[bool] = []
    for i in range(n_frames):
        frame = pcm[i * FRAME_BYTES : (i + 1) * FRAME_BYTES]
        voice_flags.append(_vad_checker.is_speech(frame, SAMPLE_RATE))

    voice_count = sum(voice_flags)
    if voice_count * FRAME_MS < MIN_VOICE_MS:
        return None  # 음성이 거의 없음 — 잡음 세그먼트

    # 앞뒤 무음 트리밍 (pad 프레임 여유 포함)
    first = voice_flags.index(True)
    last = len(voice_flags) - 1 - voice_flags[::-1].index(True)
    start = max(0, first - TRIM_PAD_FRAMES) * FRAME_BYTES
    end = min(n_frames, last + 1 + TRIM_PAD_FRAMES) * FRAME_BYTES

    trimmed = pcm[start:end]
    return trimmed if len(trimmed) >= MIN_UTTER_BYTES else None


class VadSegmenter:
    def __init__(self) -> None:
        self._vad = webrtcvad.Vad(AGGRESSIVENESS)
        self._buffer = b""            # 프레임 경계 정렬용 잔여 바이트
        self._state = "idle"          # idle | speaking
        self._voice_run = 0
        self._silence_run = 0
        self._speech: list[bytes] = []    # 발화 구간 프레임 누적
        self._preroll: list[bytes] = []   # 최근 프레임 (pre-roll)

    def feed_vad_vadService(self, chunk: bytes) -> list[bytes]:
        """PCM 청크 입력 → 완성된 발화(utterance bytes) 목록 반환.

        frontend 청크(64ms 등)와 webrtcvad 프레임(20ms) 경계가 다르므로
        내부 버퍼로 정렬한다. 발화가 완성될 때마다 결과 목록에 추가.
        """
        utterances: list[bytes] = []
        self._buffer += chunk

        while len(self._buffer) >= FRAME_BYTES:
            frame = self._buffer[:FRAME_BYTES]
            self._buffer = self._buffer[FRAME_BYTES:]

            is_voice = self._vad.is_speech(frame, SAMPLE_RATE)

            # pre-roll 링버퍼 유지
            self._preroll.append(frame)
            if len(self._preroll) > PREROLL_FRAMES:
                self._preroll.pop(0)

            if is_voice:
                self._voice_run += 1
                self._silence_run = 0
                if self._state == "idle" and self._voice_run >= START_VOICE_FRAMES:
                    # 발화 시작 — pre-roll 부터 담아서 앞부분 안 잘리게
                    self._state = "speaking"
                    self._speech = list(self._preroll)
                elif self._state == "speaking":
                    self._speech.append(frame)
            else:
                self._silence_run += 1
                self._voice_run = 0
                if self._state == "speaking":
                    self._speech.append(frame)  # 끝 무렵 침묵 약간 포함
                    if self._silence_run >= END_SILENCE_FRAMES:
                        # 발화 종료 → 합쳐서 반환 목록에 추가
                        utterance = b"".join(self._speech)
                        self._state = "idle"
                        self._speech = []
                        if len(utterance) >= MIN_UTTER_BYTES:
                            utterances.append(utterance)

        return utterances

    def flush_vad_vadService(self) -> bytes | None:
        """발화 강제 확정 (스트림 갭 감지 시 호출).

        frontend Noise Gate 가 닫히면 무음 청크가 아예 오지 않아
        END_SILENCE_FRAMES 를 채울 수 없는 경우가 생긴다.
        handler 가 수신 갭(예: 1초 이상)을 감지하면 이 메서드로
        진행 중이던 발화를 강제로 확정한다.
        """
        if self._state != "speaking":
            return None
        utterance = b"".join(self._speech)
        self._state = "idle"
        self._speech = []
        self._voice_run = 0
        self._silence_run = 0
        return utterance if len(utterance) >= MIN_UTTER_BYTES else None

    def reset_vad_vadService(self) -> None:
        """연결 종료/세션 초기화 시 상태 리셋."""
        self._buffer = b""
        self._state = "idle"
        self._voice_run = 0
        self._silence_run = 0
        self._speech = []
        self._preroll = []
