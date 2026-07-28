from __future__ import annotations

import io
import tempfile
from time import perf_counter
from pathlib import Path
from queue import Empty, Queue

import numpy as np
import requests

from config import (
    STT_COMPUTE_TYPE,
    STT_CLOUD_TIMEOUT,
    STT_DEVICE,
    STT_ENERGY_THRESHOLD,
    STT_BEAM_SIZE,
    STT_MAX_SECONDS,
    STT_MODEL,
    STT_PROVIDER,
    STT_LANGUAGE,
    STT_SILENCE_SECONDS,
    STT_START_TIMEOUT_SECONDS,
    CLOUD_ONLY,
    GROQ_API_KEY,
    GROQ_STT_MODEL,
    OPENAI_API_KEY,
    OPENAI_STT_MODEL,
)


class SpeechRecognizer:
    def __init__(
        self,
        model_name: str = STT_MODEL,
        sample_rate: int = 16000,
        max_seconds: float = STT_MAX_SECONDS,
        silence_seconds: float = STT_SILENCE_SECONDS,
        start_timeout_seconds: float = STT_START_TIMEOUT_SECONDS,
        energy_threshold: float = STT_ENERGY_THRESHOLD,
    ) -> None:
        self.sample_rate = sample_rate
        self.max_seconds = max_seconds
        self.silence_seconds = silence_seconds
        self.start_timeout_seconds = start_timeout_seconds
        self.energy_threshold = energy_threshold
        self.beam_size = STT_BEAM_SIZE
        self.provider = STT_PROVIDER
        self.cloud_timeout = STT_CLOUD_TIMEOUT
        self.language = STT_LANGUAGE
        self.model = None
        self.cloud_enabled = self.provider != "local" and bool(GROQ_API_KEY or OPENAI_API_KEY)
        if not self.cloud_enabled:
            if CLOUD_ONLY:
                raise RuntimeError("Cloud speech-to-text requires a Groq or OpenAI API key.")
            try:
                from faster_whisper import WhisperModel
            except ImportError as exc:
                raise RuntimeError(
                    "faster-whisper is not installed. Run `pip install -r requirements.txt`."
                ) from exc
            self.model = WhisperModel(
                model_name,
                device=STT_DEVICE,
                compute_type=STT_COMPUTE_TYPE,
            )

    def listen_once(self) -> str:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "sounddevice is not installed. Run `pip install -r requirements.txt`."
            ) from exc

        block_ms = 100
        block_size = int(self.sample_rate * block_ms / 1000)
        silence_blocks_limit = max(1, int(self.silence_seconds * 1000 / block_ms))
        max_blocks = max(1, int(self.max_seconds * 1000 / block_ms))
        start_timeout_blocks = max(1, int(self.start_timeout_seconds * 1000 / block_ms))
        queue: Queue[np.ndarray] = Queue()

        def callback(indata, frames, time, status) -> None:
            if status:
                return
            queue.put(indata.copy().reshape(-1))

        started_at = perf_counter()
        print("Listening...")
        frames: list[np.ndarray] = []
        heard_speech = False
        silence_blocks = 0
        total_blocks = 0

        with sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="float32",
            blocksize=block_size,
            callback=callback,
        ):
            while total_blocks < max_blocks:
                try:
                    block = queue.get(timeout=1.0)
                except Empty:
                    continue

                total_blocks += 1
                energy = float(np.sqrt(np.mean(np.square(block))))
                is_speech = energy >= self.energy_threshold

                if is_speech:
                    if not heard_speech:
                        print("Speech detected...")
                    heard_speech = True
                    silence_blocks = 0
                    frames.append(block)
                    continue

                if heard_speech:
                    frames.append(block)
                    silence_blocks += 1
                    if silence_blocks >= silence_blocks_limit:
                        break
                elif total_blocks >= start_timeout_blocks:
                    return ""

        if not frames:
            return ""
        print("Processing speech...")
        audio = np.concatenate(frames)
        text = self.transcribe(audio)
        print(f"[timing] listen+stt: {perf_counter() - started_at:.2f}s")
        return text

    def transcribe(self, audio: np.ndarray) -> str:
        if self.cloud_enabled:
            return self._transcribe_cloud(audio)
        return self._transcribe_local(audio)

    def _transcribe_cloud(self, audio: np.ndarray) -> str:
        """Upload a short, in-memory WAV to the fastest configured STT provider."""
        try:
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError(
                "soundfile is not installed. Run `pip install -r requirements.txt`."
            ) from exc

        wav = io.BytesIO()
        sf.write(wav, audio, self.sample_rate, format="WAV", subtype="PCM_16")
        payload = wav.getvalue()
        providers = ("groq", "openai") if self.provider == "auto" else (self.provider,)
        failures: list[str] = []
        for provider in providers:
            if provider == "groq" and GROQ_API_KEY:
                url, key, model = (
                    "https://api.groq.com/openai/v1/audio/transcriptions",
                    GROQ_API_KEY,
                    GROQ_STT_MODEL,
                )
            elif provider == "openai" and OPENAI_API_KEY:
                url, key, model = (
                    "https://api.openai.com/v1/audio/transcriptions",
                    OPENAI_API_KEY,
                    OPENAI_STT_MODEL,
                )
            else:
                continue
            try:
                data = {"model": model, "response_format": "json", "temperature": "0"}
                if self.language:
                    data["language"] = self.language
                response = requests.post(
                    url,
                    headers={"Authorization": f"Bearer {key}"},
                    files={"file": ("kairo.wav", payload, "audio/wav")},
                    data=data,
                    timeout=self.cloud_timeout,
                )
                if response.status_code == 200:
                    return str(response.json().get("text", "")).strip()
                failures.append(f"{provider} HTTP {response.status_code}: {response.text[:120]}")
            except Exception as exc:
                failures.append(f"{provider}: {exc}")
        raise RuntimeError("Cloud speech-to-text unavailable: " + "; ".join(failures))

    def _transcribe_local(self, audio: np.ndarray) -> str:
        if self.model is None:
            raise RuntimeError("No speech-to-text provider is available.")
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
            path = Path(handle.name)
        try:
            import soundfile as sf

            sf.write(path, audio, self.sample_rate)
            segments, _info = self.model.transcribe(
                str(path),
                vad_filter=True,
                beam_size=self.beam_size,
                temperature=0.0,
                condition_on_previous_text=False,
            )
            return " ".join(segment.text.strip() for segment in segments).strip()
        finally:
            path.unlink(missing_ok=True)
