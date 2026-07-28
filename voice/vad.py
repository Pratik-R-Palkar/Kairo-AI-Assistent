from __future__ import annotations

import numpy as np


class VoiceActivityDetector:
    """Voice Activity Detector using WebRTC VAD or fallback audio energy threshold."""

    def __init__(self, mode: int = 2, energy_threshold: float = 0.012) -> None:
        self.energy_threshold = energy_threshold
        self._vad = None
        try:
            import webrtcvad

            self._vad = webrtcvad.Vad(mode)
        except Exception:
            self._vad = None

    def is_speech(self, frame: np.ndarray, sample_rate: int = 16000) -> bool:
        if frame is None or len(frame) == 0:
            return False

        # Try WebRTC VAD if available and frame size is valid (10ms, 20ms, or 30ms)
        if self._vad is not None and frame.dtype == np.int16:
            frame_len_ms = (len(frame) * 1000) // sample_rate
            if frame_len_ms in (10, 20, 30):
                try:
                    return self._vad.is_speech(frame.tobytes(), sample_rate)
                except Exception:
                    pass

        # RMS Energy threshold calculation (fallback or standard for float32 arrays)
        if frame.dtype != np.float32:
            frame_float = frame.astype(np.float32) / 32768.0
        else:
            frame_float = frame

        rms_energy = float(np.sqrt(np.mean(np.square(frame_float))))
        return rms_energy >= self.energy_threshold
