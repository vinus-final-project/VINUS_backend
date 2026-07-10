# app/ai/vad/vadService.py
#
# VadSegmenter — WebRTC VAD 기반 발화 구간 분리기
#
# frontend 가 마이크 PCM(16kHz mono Int16)을 연속 스트림으로 보내면,
# backend 가 이 세그먼터로 발화 구간을 분리해 STT 로 넘긴다.
#
# 사용 (WS 연결 1개당 인스턴스 1개):
#   segmenter = VadSegmenter()
#   for chunk in incoming_binary_frames:
#       for utterance in segmenter.feed_vad_vadService(chunk):
#           text = await WhisperService.transcribe_stt_whisper(utterance)
#
# 요구 패키지: webrtcvad  (pip install webrtcvad)
#
# 튜닝 포인트:
#   AGGRESSIVENESS      0(관대)~3(엄격). 잡음 많은 환경 → 3
#   START_VOICE_FRAMES  연속 음성 프레임 수 → 발화 시작 판정
#   END_SILENCE_FRAMES  연속 무음 프레임 수 → 발화 종료 판정
#   PREROLL_FRAMES      발화 앞부분 안 잘리게 미리 보관할 프레임 수
#   MIN_UTTER_BYTES     이보다 짧은 발화는 잡음으로 폐기 (0.5초)

import webrtcvad

SAMPLE_RATE = 16000
FRAME_MS = 20                                   # webrtcvad 허용: 10/20/30ms
FRAME_BYTES = SAMPLE_RATE * FRAME_MS // 1000 * 2  # 640 bytes (Int16)

AGGRESSIVENESS = 3
START_VOICE_FRAMES = 5      # 100ms 연속 음성 → 발화 시작
END_SILENCE_FRAMES = 30     # 600ms 연속 무음 → 발화 종료
PREROLL_FRAMES = 5          # 100ms pre-roll
MIN_UTTER_BYTES = 16000     # 0.5초 미만 발화 폐기 (환각 방지)


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

    def reset_vad_vadService(self) -> None:
        """연결 종료/세션 초기화 시 상태 리셋."""
        self._buffer = b""
        self._state = "idle"
        self._voice_run = 0
        self._silence_run = 0
        self._speech = []
        self._preroll = []
