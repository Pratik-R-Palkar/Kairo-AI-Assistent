from __future__ import annotations

from config import TTS_ENABLED, TTS_MAX_SPOKEN_CHARS, TTS_PROVIDER
from voice.tts import ElevenLabsTTS, KokoroTTS


class Speaker:
    def __init__(self) -> None:
        self.enabled = TTS_ENABLED
        if not self.enabled:
            self.tts = None
        elif TTS_PROVIDER == "elevenlabs":
            self.tts = ElevenLabsTTS()
        else:
            self.tts = KokoroTTS()


    def say(self, text: str, mood: str | None = None) -> None:
        if not self.tts:
            return
        try:
            self.tts.speak(self._spoken_text(text), mood=mood)
        except Exception as exc:
            print(f"[tts unavailable: {exc}]")

    def _spoken_text(self, text: str) -> str:
        clean = " ".join(text.split())
        if len(clean) <= TTS_MAX_SPOKEN_CHARS:
            return clean

        sentences = []
        for part in clean.replace("?", ".").replace("!", ".").split("."):
            part = part.strip()
            if not part:
                continue
            next_text = ". ".join(sentences + [part]) + "."
            if len(next_text) > TTS_MAX_SPOKEN_CHARS:
                break
            sentences.append(part)

        if sentences:
            return ". ".join(sentences) + "."
        return clean[:TTS_MAX_SPOKEN_CHARS].rsplit(" ", 1)[0] + "."
