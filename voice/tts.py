from __future__ import annotations

import logging
from pathlib import Path
import re
import warnings
from typing import Iterator

import numpy as np

from config import (
    TTS_LANG_CODE,
    TTS_MODEL_REPO,
    TTS_PAUSE_PAD_MS,
    TTS_SPEED,
    TTS_VOICE,
    TTS_VOICE_BLEND,
)

logger = logging.getLogger(__name__)


ROMAN_MARATHI_MAP = {
    # --- Greetings ---
    "namaskar": "नमस्कार",
    "namaste": "नमस्ते",
    "namasthe": "नमस्ते",
    "shubhprabhat": "शुभ प्रभात",
    "shubh": "शुभ",
    "prabhat": "प्रभात",
    "sandhya": "संध्या",
    "suprabhat": "सुप्रभात",
    # --- Assistant name ---
    "kairo": "कायरो",
    # --- Pronouns ---
    "mi": "मी",
    "me": "मी",
    "mee": "मी",
    "tu": "तू",
    "tumi": "तुमी",
    "tumhi": "तुम्ही",
    "amhi": "आम्ही",
    "aahe": "आहे",
    "ahe": "आहे",
    "ahet": "आहेत",
    "aahat": "आहात",
    "hote": "होते",
    "hota": "होता",
    "hoti": "होती",
    # --- Possessives / genitive ---
    "maze": "माझे",
    "maza": "माझा",
    "mazi": "माझी",
    "majha": "माझा",
    "majhi": "माझी",
    "majhe": "माझे",
    "mazya": "माझ्या",
    "majhya": "माझ्या",
    "tumcha": "तुमचा",
    "tumchi": "तुमची",
    "tumche": "तुमचे",
    "tumchya": "तुमच्या",
    "amcha": "आमचा",
    "amchi": "आमची",
    "amche": "आमचे",
    "amchya": "आमच्या",
    "tyacha": "त्याचा",
    "tyachi": "त्याची",
    "tyache": "त्याचे",
    "tyachya": "त्याच्या",
    "ticha": "तिचा",
    "tichi": "तिची",
    "tiche": "तिचे",
    "tichya": "तिच्या",
    "yacha": "याचा",
    "yachi": "याची",
    "yache": "याचे",
    "yachya": "याच्या",
    # --- Common nouns ---
    "naav": "नाव",
    "nav": "नाव",
    "naam": "नाम",
    "ghar": "घर",
    "shahar": "शहर",
    "desh": "देश",
    "bhasha": "भाषा",
    "pan": "पण",
    "vel": "वेळ",
    "din": "दिन",
    "aaj": "आज",
    "udya": "उद्या",
    "kal": "काल",
    "sara": "सारा",
    "sarv": "सर्व",
    "sarva": "सर्व",
    "sagle": "सगळे",
    "lokani": "लोकांनी",
    "lok": "लोक",
    # --- Postpositions / particles ---
    "kade": "कडे",
    "sathi": "साठी",
    "madhe": "मध्ये",
    "madhye": "मध्ये",
    "barobar": "बरोबर",
    "saglyansathi": "सगळ्यांसाठी",
    "cha": "चा",
    "chi": "ची",
    "che": "चे",
    "la": "ला",
    "na": "ना",
    "ne": "ने",
    "ni": "नी",
    "var": "वर",
    "khali": "खाली",
    "aani": "आणि",
    "ani": "आणि",
    "anhi": "आणि",
    "tar": "तर",
    "pan": "पण",
    "mhanun": "म्हणून",
    # --- Verbs ---
    "aahe": "आहे",
    "ahe": "आहे",
    "nahi": "नाही",
    "naahi": "नाही",
    "karto": "करतो",
    "karti": "करती",
    "karte": "करते",
    "karat": "करत",
    "karuya": "करूया",
    "karu": "करू",
    "sanga": "सांगा",
    "sangto": "सांगतो",
    "sangti": "सांगती",
    "yeto": "येतो",
    "yete": "येते",
    "yeu": "येऊ",
    "jato": "जातो",
    "jate": "जाते",
    "bagha": "बघा",
    "bagh": "बघ",
    "aika": "ऐका",
    "aik": "ऐक",
    "mahit": "माहीत",
    "madat": "मदत",
    "madatila": "मदतीला",
    "tayar": "तयार",
    "bolto": "बोलतो",
    "bolte": "बोलते",
    "samajto": "समजतो",
    "samajte": "समजते",
    "suchavto": "सुचवतो",
    "japnas": "जपण्यास",
    "sugam": "सुगम",
    "karen": "करेन",
    "karein": "करेन",
    "karin": "करीन",
    "shikto": "शिकतो",
    "shikte": "शिकते",
    # --- Question words ---
    "kasa": "कसा",
    "kasi": "कशी",
    "kase": "कसे",
    "kay": "काय",
    "kiti": "किती",
    "kuthe": "कुठे",
    "keva": "केव्हा",
    "kevha": "केव्हा",
    "ka": "का",
    "kon": "कोण",
    "konata": "कोणता",
    "konti": "कोणती",
    # --- Common adjectives ---
    "changle": "चांगले",
    "changla": "चांगला",
    "changli": "चांगली",
    "sundar": "सुंदर",
    "mahan": "महान",
    "navi": "नवी",
    "nava": "नवा",
    "nave": "नवे",
    "juna": "जुना",
    "juni": "जुनी",
    "june": "जुने",
    "moti": "मोठी",
    "mota": "मोठा",
    "mote": "मोठे",
    "lahan": "लहान",
    # --- Common phrases ---
    "khup": "खूप",
    "thoda": "थोडा",
    "thodi": "थोडी",
    "thode": "थोडे",
    "atishay": "अतिशय",
    "dhanyawad": "धन्यवाद",
    "dhanyavad": "धन्यवाद",
    "shukriya": "शुक्रिया",
    "chala": "चला",
    "bagh": "बघ",
    "ho": "हो",
    "hoy": "होय",
    "nako": "नको",
    # --- Directions / places ---
    "uttar": "उत्तर",
    "uttare": "उत्तरे",
    "dakshin": "दक्षिण",
    "purva": "पूर्व",
    "pashchim": "पश्चिम",
    # --- Other useful words ---
    "prashna": "प्रश्न",
    "prashnanchi": "प्रश्नांची",
    "kamamdhe": "कामांमध्ये",
    "kamamde": "कामांमध्ये",
    "charcha": "चर्चा",
    "rozchya": "रोजच्या",
    "sangeet": "संगीत",
    "aawad": "आवड",
    "aawadiche": "आवडीचे",
    "aawadichi": "आवडीची",
    "aawadichya": "आवडीच्या",
    "aathvan": "आठवण",
    "aathvani": "आठवणी",
    "bhavishya": "भविष्य",
    "nirman": "निर्माण",
    "ektra": "एकत्र",
    "ektraritpane": "एकत्रितपणे",
    "jeevan": "जीवन",
    "aanandayi": "आनंददायी",
    "karyaksham": "कार्यक्षम",
    "sope": "सोपे",
}


def _transliterate_roman_marathi(text: str) -> str:
    """Map Romanized Marathi words to Devanagari for natural Marathi TTS pronunciation.

    Handles any mix of English and Romanized Marathi (e.g. 'maze naav kairo aahe').
    Converts all recognised Marathi tokens regardless of surrounding language.
    """
    words = text.split()
    converted = []

    for w in words:
        punct_match = re.match(r"^([\w'-]+)([^\w]*)$", w)
        if punct_match:
            word_part, trailing_punct = punct_match.group(1), punct_match.group(2)
        else:
            word_part, trailing_punct = w, ""

        clean_w = word_part.lower()
        if clean_w in ROMAN_MARATHI_MAP:
            converted.append(ROMAN_MARATHI_MAP[clean_w] + trailing_punct)
        else:
            converted.append(w)

    return " ".join(converted)


def _is_devanagari(text: str) -> bool:
    """Check if string contains Devanagari (Marathi/Hindi) characters."""
    return any("\u0900" <= char <= "\u097f" for char in text)


def _preprocess_text(text: str) -> str:
    """Format text for natural human cadence, smooth greetings, joint words, and phonetic clarity."""
    # 0. Transliterate Romanized Marathi words (e.g. 'kade' -> 'कडे', 'namaskar' -> 'नमस्कार')
    text = _transliterate_roman_marathi(text)
    # 1. Soften exclamation/period after greetings so there is no sudden silence pause
    text = re.sub(
        r"\b(नमस्कार|नमस्ते|शुभ प्रभात|शुभ संध्या|हेलो|हाय|होय|नाही)[!.]",
        r"\1,",
        text,
        flags=re.IGNORECASE,
    )

    # 2. Clean invisible Unicode characters that disrupt Devanagari conjuncts/halant
    text = text.replace("\u200b", "").replace("\u200c", "").replace("\u200d", "")

    # 3. Replace Devanagari danda '।' with '.'
    text = text.replace("।", ".")

    # 4. Rejoin separated Marathi postpositions into compound joint words (जोडशब्द)
    postposition_pattern = re.compile(
        r"(?<=[^\s,.!?])\s+(मध्ये|साठी|प्रमाणे|बद्दल|मुळे|पेक्षा)(?=\s|$)"
    )
    text = postposition_pattern.sub(r"\1", text)

    # 5. Ensure 'कडे' has space boundary so 'क' and 'डे' are spoken as distinct human syllables (kˈʌɖeː = क + डे)
    text = re.sub(r"(?<=[^\s,.!?])कडे(?=\s|$)", r" कडे", text)

    # 5. Ensure natural comma micro-pauses before common conjunctions if missing
    for conj in ["आणि", "तर", "पण", "म्हणून"]:
        pattern = re.compile(rf"(?<![,.!?])\s+{conj}(?=\s|$)")
        text = pattern.sub(f", {conj}", text)

    # 6. Marathi Schwa Syncope (मराठी जोडशब्द सलग उच्चार)
    # Fixes broken staccato syllable gaps in Marathi possessives and pronouns (e.g. तुमच्या -> तुम्च्या)
    schwa_syncope_rules = [
        (r"तुमच्या", "तुम्च्या"),
        (r"आमच्या", "आम्च्या"),
        (r"त्याच्या", "त्याच्च्या"),
        (r"याच्या", "याच्च्या"),
        (r"रोजच्या", "रोज्च्या"),
        (r"तुमचा", "तुम्चा"),
        (r"तुमची", "तुम्ची"),
        (r"तुमचे", "तुम्चे"),
        (r"आमचा", "आम्चा"),
        (r"आमची", "आम्ची"),
        (r"आमचे", "आम्चे"),
        (r"त्याचा", "त्याच्चा"),
        (r"त्याची", "त्याच्ची"),
        (r"त्याचे", "त्याच्चे"),
        (r"याचा", "याच्चा"),
        (r"याची", "याच्ची"),
        (r"याचे", "याच्चे"),
    ]
    for pattern, replacement in schwa_syncope_rules:
        text = re.sub(pattern, replacement, text)

    return " ".join(text.split())


class KokoroTTS:
    """Official Kokoro-82M Text-to-Speech Engine using hexgrad/Kokoro-82M."""

    def __init__(
        self,
        voice: str = TTS_VOICE,
        voice_blend: str = TTS_VOICE_BLEND,
        speed: float = TTS_SPEED,
        pause_pad_ms: int = TTS_PAUSE_PAD_MS,
        repo_id: str = TTS_MODEL_REPO,
        lang_code: str = TTS_LANG_CODE,
    ) -> None:
        self.voice = voice
        self.voice_blend = voice_blend
        self.speed = speed
        self.pause_pad_ms = pause_pad_ms
        self.repo_id = repo_id
        self.default_lang_code = lang_code
        # Forced language code (e.g., "h" for Marathi) – if set, overrides auto-detection
        from config import TTS_FORCE_LANG_CODE
        self.force_lang_code = TTS_FORCE_LANG_CODE or None
        self._pipelines: dict[str, any] = {}
        self._loaded_voices: dict[tuple[str, str], any] = {}

    def _get_pipeline(self, lang_code: str):
        if lang_code not in self._pipelines:
            logging.getLogger("huggingface_hub").setLevel(logging.ERROR)
            logging.getLogger("transformers").setLevel(logging.ERROR)
            from kokoro import KPipeline

            with warnings.catch_warnings():
                warnings.filterwarnings("ignore", category=UserWarning, module="torch")
                warnings.filterwarnings("ignore", category=FutureWarning, module="torch")
                self._pipelines[lang_code] = KPipeline(
                    lang_code=lang_code,
                    repo_id=self.repo_id,
                )
        return self._pipelines[lang_code]

    def _resolve_voice(self, pipeline: any, voice_spec: str):
        """Resolve single voice name or blend multiple voices (e.g., 'hf_alpha:0.6,hf_beta:0.4')."""
        if ":" not in voice_spec:
            return voice_spec

        cache_key = (pipeline.lang_code, voice_spec)
        if cache_key in self._loaded_voices:
            return self._loaded_voices[cache_key]

        try:
            blended = None
            for item in voice_spec.split(","):
                name, weight_str = item.split(":")
                weight = float(weight_str)
                v_tensor = pipeline.load_voice(name.strip())
                if blended is None:
                    blended = weight * v_tensor
                else:
                    blended += weight * v_tensor
            self._loaded_voices[cache_key] = blended
            return blended
        except Exception as exc:
            logger.warning("Failed to resolve blended voice '%s': %s. Falling back to '%s'.", voice_spec, exc, self.voice)
            return self.voice

    def _split_text(self, text: str) -> list[str]:
        cleaned = _preprocess_text(text)
        parts = re.split(r"(?<=[.!?])\s+", cleaned)
        return [p.strip() for p in parts if p.strip()]

    def _detect_lang_code(self, text: str) -> str:
        if any("\u0900" <= c <= "\u097f" for c in text):
            return "h"  # Hindi / Marathi Devanagari
        if any("\u4e00" <= c <= "\u9fff" for c in text):
            return "z"  # Chinese
        if any("\u3040" <= c <= "\u30ff" for c in text):
            return "j"  # Japanese
        return self.default_lang_code

    def _generate_audio_chunks(self, text: str) -> Iterator[np.ndarray]:
        # Determine language pipeline: forced > auto-detection > default
        if self.force_lang_code:
            target_lang = self.force_lang_code
        else:
            target_lang = self._detect_lang_code(text)
        pipeline = self._get_pipeline(target_lang)
        voice_target = self._resolve_voice(pipeline, self.voice_blend or self.voice)
        sentences = self._split_text(text)

        pause_samples = int((self.pause_pad_ms / 1000.0) * 24000)
        silence_pad = np.zeros(pause_samples, dtype=np.float32) if pause_samples > 0 else None

        for idx, chunk in enumerate(sentences):
            try:
                for _g, _p, audio in pipeline(chunk, voice=voice_target, speed=self.speed):
                    if audio is not None:
                        if hasattr(audio, "numpy"):
                            audio = audio.numpy()
                        yield audio

                # Add natural breathing pause between sentences
                if silence_pad is not None and idx < len(sentences) - 1:
                    yield silence_pad
            except Exception as exc:
                logger.error("Kokoro-82M TTS chunk generation failed: %s", exc)

    def speak(self, text: str, mood: str | None = None) -> None:
        try:
            import sounddevice as sd
        except ImportError as exc:
            raise RuntimeError(
                "sounddevice is not installed. Run `pip install -r requirements.txt`."
            ) from exc

        for audio in self._generate_audio_chunks(text):
            sd.play(audio, 24000)
            sd.wait()

    def save(self, text: str, path: str | Path) -> Path:
        try:
            import soundfile as sf
        except ImportError as exc:
            raise RuntimeError(
                "soundfile is not installed. Run `pip install -r requirements.txt`."
            ) from exc

        output = Path(path)
        chunks = list(self._generate_audio_chunks(text))
        if chunks:
            full_audio = np.concatenate(chunks)
            sf.write(output, full_audio, 24000)
        return output


class ElevenLabsTTS:
    """Low-latency ElevenLabs TTS with selective, human-like expressive delivery."""

    def __init__(
        self,
        api_keys: list[str] | None = None,
        voice_id: str | None = None,
        fallback_voice_id: str | None = None,
        model_id: str | None = None,
    ) -> None:
        from config import (
            ELEVENLABS_API_KEYS,
            ELEVENLABS_EXPRESSIVE_ENABLED,
            ELEVENLABS_EXPRESSIVE_MODEL_ID,
            ELEVENLABS_FALLBACK_VOICE_ID,
            ELEVENLABS_LANGUAGE_CODE,
            ELEVENLABS_LOCAL_FALLBACK,
            ELEVENLABS_MODEL_ID,
            ELEVENLABS_REQUEST_TIMEOUT,
            ELEVENLABS_SIMILARITY_BOOST,
            ELEVENLABS_SPEED,
            ELEVENLABS_STABILITY,
            ELEVENLABS_STYLE,
            ELEVENLABS_VOICE_ID,
        )

        self.api_keys = api_keys or ELEVENLABS_API_KEYS
        self.voice_id = voice_id or ELEVENLABS_VOICE_ID
        self.fallback_voice_id = fallback_voice_id or ELEVENLABS_FALLBACK_VOICE_ID
        self.model_id = model_id or ELEVENLABS_MODEL_ID
        self.expressive_model_id = ELEVENLABS_EXPRESSIVE_MODEL_ID
        self.expressive_enabled = ELEVENLABS_EXPRESSIVE_ENABLED
        self.language_code = ELEVENLABS_LANGUAGE_CODE
        self.request_timeout = ELEVENLABS_REQUEST_TIMEOUT
        self.local_fallback = ELEVENLABS_LOCAL_FALLBACK
        self.voice_settings = {
            "stability": ELEVENLABS_STABILITY,
            "similarity_boost": ELEVENLABS_SIMILARITY_BOOST,
            "style": ELEVENLABS_STYLE,
            "use_speaker_boost": True,
            "speed": ELEVENLABS_SPEED,
        }
        self.active_voice_id = self.voice_id
        self.current_key_index = 0
        self._kokoro_backup: KokoroTTS | None = None

    def _get_kokoro(self) -> KokoroTTS:
        if self._kokoro_backup is None:
            self._kokoro_backup = KokoroTTS()
        return self._kokoro_backup

    def _delivery(self, text: str, mood: str | None = None) -> tuple[str, str]:
        """Use Eleven v3 only when a reply benefits from an audible emotion.

        Flash remains the default for low-latency conversational turn taking.
        V3 is selected for a short laugh, a supportive/sad response, or a
        celebration; its audio tags are never shown in Kairo's text response.
        """
        lowered = text.lower()
        tags = ""
        if mood == "sad" or any(word in lowered for word in ("sorry", "loss", "passed away", "sad", "heartbroken", "condolence")):
            tags = "[sadly]"
        elif mood == "playful" or any(word in lowered for word in ("joke", "funny", "hilarious", "haha", "made me laugh")):
            tags = "[laughs softly]"
        elif mood == "happy" or any(word in lowered for word in ("congratulations", "great news", "amazing news", "celebrate", "excited")):
            tags = "[happily]"

        if tags and self.expressive_enabled:
            return self.expressive_model_id, f"{tags} {text}"
        return self.model_id, text

    def _rotate_key(self, reason: str) -> None:
        if not self.api_keys:
            return
        old_idx = self.current_key_index
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        logger.warning(
            "ElevenLabs key %d failed (%s); trying key %d.",
            old_idx + 1,
            reason,
            self.current_key_index + 1,
        )

    def _stream_response(self, text: str, mood: str | None = None):
        if not self.api_keys:
            raise RuntimeError("No ElevenLabs API keys configured.")

        import requests

        model_id, spoken_text = self._delivery(text, mood=mood)
        # When V3 is unavailable for the account, retain a natural voice and
        # fast playback by retrying the exact reply on Flash without its tag.
        model_attempts = [(model_id, spoken_text)]
        if model_id != self.model_id:
            model_attempts.append((self.model_id, text))

        failures: list[str] = []
        voice_ids = tuple(dict.fromkeys((self.active_voice_id, self.fallback_voice_id)))
        for attempt_model, attempt_text in model_attempts:
            for voice_id in voice_ids:
                for _ in range(len(self.api_keys)):
                    key = self.api_keys[self.current_key_index]
                    url = (
                        f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"
                        "?output_format=pcm_24000"
                    )
                    payload = {
                        "text": attempt_text,
                        "model_id": attempt_model,
                        "voice_settings": self.voice_settings,
                    }
                    # Leaving language_code empty lets Flash identify the reply
                    # language; V3 detects it itself.
                    if self.language_code and attempt_model != self.expressive_model_id:
                        payload["language_code"] = self.language_code
                    try:
                        response = requests.post(
                            url,
                            json=payload,
                            headers={"xi-api-key": key, "Content-Type": "application/json"},
                            timeout=(3, self.request_timeout),
                            stream=True,
                        )
                        if response.status_code == 200:
                            self.active_voice_id = voice_id
                            return response
                        detail = response.text[:140]
                        response.close()
                        failures.append(f"HTTP {response.status_code}: {detail}")
                        self._rotate_key(failures[-1])
                    except Exception as exc:
                        failures.append(str(exc))
                        self._rotate_key(str(exc))
        raise RuntimeError("ElevenLabs synthesis unavailable: " + "; ".join(failures[-3:]))

    def _synthesize(self, text: str) -> bytes:
        response = self._stream_response(text)
        try:
            return b"".join(chunk for chunk in response.iter_content(chunk_size=8192) if chunk)
        finally:
            response.close()

    def speak(self, text: str, mood: str | None = None) -> None:
        """Begin playback as soon as ElevenLabs sends the first PCM audio chunk."""
        try:
            import sounddevice as sd

            response = self._stream_response(text, mood=mood)
            pending = b""
            try:
                with sd.RawOutputStream(samplerate=24000, channels=1, dtype="int16") as stream:
                    for chunk in response.iter_content(chunk_size=4096):
                        if not chunk:
                            continue
                        pending += chunk
                        aligned = len(pending) - (len(pending) % 2)
                        if aligned:
                            stream.write(pending[:aligned])
                            pending = pending[aligned:]
            finally:
                response.close()
        except Exception as exc:
            logger.error("ElevenLabs TTS failed: %s", exc)
            if self.local_fallback:
                logger.warning("KAIRO_TTS_LOCAL_FALLBACK is enabled; using Kokoro.")
                self._get_kokoro().speak(text)

    def save(self, text: str, path: str | Path) -> Path:
        output = Path(path)
        pcm_bytes = self._synthesize(text)
        import soundfile as sf

        audio_np = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        sf.write(output, audio_np, 24000)
        return output
