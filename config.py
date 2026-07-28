from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")


def env(name: str, default: str) -> str:
    return os.getenv(name, default)


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def env_int(name: str, default: int) -> int:
    value = os.getenv(name)
    if value is None:
        return default
    return int(value)


def env_float(name: str, default: float) -> float:
    value = os.getenv(name)
    if value is None:
        return default
    return float(value)


@dataclass(frozen=True)
class ModelConfig:
    role: str
    repo_id: str
    filename: str
    local_path: Path
    context: int = 4096
    temperature: float = 0.55
    top_p: float = 0.9


MODELS_DIR = ROOT / "models"

# Current local defaults:
# - General: L3Cube Marathi Gemma 2B (GGUF), bilingual Marathi/English conversation.
# - Reasoning: Phi-4 Mini Instruct, compact reasoning route.
# - Research: Llama 3.2 3B Instruct, stable web-grounded summaries.
# - Coding: Qwen2.5-Coder 3B Instruct. Public Qwen3-Coder GGUFs are 30B-A3B,
#   so this keeps KAIRO genuinely low-end/local while using a 3B coder.
GENERAL_MODEL = ModelConfig(
    role="general",
    repo_id=env("KAIRO_GENERAL_REPO", "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF"),
    filename=env("KAIRO_GENERAL_FILE", "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"),
    local_path=Path(env("KAIRO_GENERAL_MODEL", str(MODELS_DIR / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"))),
)

FAST_CHAT_MODEL = ModelConfig(
    role="fast_chat",
    repo_id=env("KAIRO_FAST_CHAT_REPO", "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF"),
    filename=env("KAIRO_FAST_CHAT_FILE", "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"),
    local_path=Path(env("KAIRO_FAST_CHAT_MODEL", str(MODELS_DIR / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"))),
    temperature=0.5,
)

CODING_MODEL = ModelConfig(
    role="coding",
    repo_id=env("KAIRO_CODING_REPO", "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF"),
    filename=env("KAIRO_CODING_FILE", "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"),
    local_path=Path(env("KAIRO_CODING_MODEL", str(MODELS_DIR / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"))),
    temperature=0.25,
)

REASONING_MODEL = ModelConfig(
    role="reasoning",
    repo_id=env("KAIRO_REASONING_REPO", "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF"),
    filename=env("KAIRO_REASONING_FILE", "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"),
    local_path=Path(env("KAIRO_REASONING_MODEL", str(MODELS_DIR / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"))),
    context=4096,
    temperature=0.3,
)

RESEARCH_MODEL = ModelConfig(
    role="research",
    repo_id=env("KAIRO_RESEARCH_REPO", "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF"),
    filename=env("KAIRO_RESEARCH_FILE", "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"),
    local_path=Path(env("KAIRO_RESEARCH_MODEL", str(MODELS_DIR / "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"))),
    context=4096,
    temperature=0.35,
)

VISION_MODEL = ModelConfig(
    role="vision",
    repo_id=env("KAIRO_VISION_REPO", "moondream/moondream2-gguf"),
    filename=env("KAIRO_VISION_FILE", "moondream2-text-model-f16.gguf"),
    local_path=Path(env("KAIRO_VISION_MODEL", str(MODELS_DIR / "moondream2-text-model-f16.gguf"))),
    context=2048,
    temperature=0.2,
)

VISION_MMPROJ_PATH = Path(env("KAIRO_VISION_MMPROJ", str(MODELS_DIR / "moondream2-mmproj-f16.gguf")))

MODEL_ROUTES = {
    "fast_chat": FAST_CHAT_MODEL,
    "general": GENERAL_MODEL,
    "coding": CODING_MODEL,
    "reasoning": REASONING_MODEL,
    "research": RESEARCH_MODEL,
    "vision": VISION_MODEL,
}

ASSISTANT_NAME = env("KAIRO_NAME", "Kairo")
USER_NAME = env("KAIRO_USER_NAME", "User")
USER_TITLE = env("KAIRO_USER_TITLE", "friend")
ENABLE_WEB = env_bool("KAIRO_ENABLE_WEB", True)
MAX_WEB_RESULTS = int(env("KAIRO_MAX_WEB_RESULTS", "5"))
KAIRO_TIMING = env_bool("KAIRO_TIMING", True)
KAIRO_WARM_UP = env_bool("KAIRO_WARM_UP", True)
KAIRO_LOW_END_MODE = env_bool("KAIRO_LOW_END_MODE", True)
DATASTORM_ALWAYS_WEB = env_bool("KAIRO_DATASTORM_ALWAYS_WEB", False)
DATASTORM_MAX_SOURCES = env_int("KAIRO_DATASTORM_MAX_SOURCES", 1)
DATASTORM_SNIPPET_CHARS = env_int("KAIRO_DATASTORM_SNIPPET_CHARS", 320)
WEB_SEARCH_TIMEOUT = env_float("KAIRO_WEB_SEARCH_TIMEOUT", 3.0)

STT_MODEL = env("KAIRO_STT_MODEL", "deepdml/faster-whisper-large-v3-turbo-ct2")
# Cloud-only transcription. Groq offers a free plan but still requires its own API key.
STT_PROVIDER = env("KAIRO_STT_PROVIDER", "groq").lower().strip()
STT_CLOUD_TIMEOUT = env_float("KAIRO_STT_CLOUD_TIMEOUT", 8.0)
STT_LANGUAGE = env("KAIRO_STT_LANGUAGE", "").strip()
GROQ_STT_MODEL = env("KAIRO_GROQ_STT_MODEL", "whisper-large-v3-turbo")
OPENAI_STT_MODEL = env("KAIRO_OPENAI_STT_MODEL", "gpt-4o-mini-transcribe")
STT_DEVICE = env("KAIRO_STT_DEVICE", "cpu")
STT_COMPUTE_TYPE = env("KAIRO_STT_COMPUTE_TYPE", "int8")
STT_MAX_SECONDS = env_float("KAIRO_STT_MAX_SECONDS", 30.0)
STT_SILENCE_SECONDS = env_float("KAIRO_STT_SILENCE_SECONDS", 0.4)
STT_START_TIMEOUT_SECONDS = env_float("KAIRO_STT_START_TIMEOUT_SECONDS", 5.0)
STT_ENERGY_THRESHOLD = env_float("KAIRO_STT_ENERGY_THRESHOLD", 0.012)
STT_BEAM_SIZE = env_int("KAIRO_STT_BEAM_SIZE", 1)

TTS_VOICE = env("KAIRO_TTS_VOICE", "af_heart")
TTS_VOICE_BLEND = env("KAIRO_TTS_VOICE_BLEND", "")
TTS_SPEED = env_float("KAIRO_TTS_SPEED", 0.96)
TTS_PAUSE_PAD_MS = env_int("KAIRO_TTS_PAUSE_PAD_MS", 150)
TTS_ENABLED = env_bool("KAIRO_TTS_ENABLED", True)
# Local-first synthesis. Kokoro-82M runs on-device by default for privacy and offline use.
TTS_PROVIDER = env("KAIRO_TTS_PROVIDER", "kokoro").lower().strip()
TTS_MAX_SPOKEN_CHARS = env_int("KAIRO_TTS_MAX_SPOKEN_CHARS", 360)
TTS_MODEL_REPO = env("KAIRO_TTS_MODEL_REPO", "hexgrad/Kokoro-82M")
TTS_LANG_CODE = env("KAIRO_TTS_LANG_CODE", "a")
# Empty means auto-detect the spoken language; set this only to force a voice route.
TTS_FORCE_LANG_CODE = env("KAIRO_TTS_FORCE_LANG_CODE", "")

ELEVENLABS_VOICE_ID = env("ELEVENLABS_VOICE_ID", "1qEiC6qsybMkmnNdVMbK")
ELEVENLABS_FALLBACK_VOICE_ID = env("ELEVENLABS_FALLBACK_VOICE_ID", "EXAVITQu4vr4xnSDxMaL")
ELEVENLABS_MODEL_ID = env("ELEVENLABS_MODEL_ID", "eleven_flash_v2_5")
ELEVENLABS_EXPRESSIVE_MODEL_ID = env("ELEVENLABS_EXPRESSIVE_MODEL_ID", "eleven_v3")
ELEVENLABS_EXPRESSIVE_ENABLED = env_bool("ELEVENLABS_EXPRESSIVE_ENABLED", True)
ELEVENLABS_STABILITY = env_float("ELEVENLABS_STABILITY", 0.42)
ELEVENLABS_SIMILARITY_BOOST = env_float("ELEVENLABS_SIMILARITY_BOOST", 0.82)
ELEVENLABS_STYLE = env_float("ELEVENLABS_STYLE", 0.28)
ELEVENLABS_SPEED = env_float("ELEVENLABS_SPEED", 1.05)
ELEVENLABS_REQUEST_TIMEOUT = env_float("ELEVENLABS_REQUEST_TIMEOUT", 7.0)
ELEVENLABS_LANGUAGE_CODE = env("ELEVENLABS_LANGUAGE_CODE", "").strip()
ELEVENLABS_LOCAL_FALLBACK = env_bool("ELEVENLABS_LOCAL_FALLBACK", False)
def _parse_env_list(value: str) -> list[str]:
    if not value:
        return []
    return [item.strip() for item in re.split(r"[\s,;]+", value) if item.strip()]


raw_elevenlabs_keys = env("ELEVENLABS_API_KEYS", "")
ELEVENLABS_API_KEYS = _parse_env_list(raw_elevenlabs_keys)


WAKE_WORD_REQUIRED = env_bool("KAIRO_WAKE_WORD_REQUIRED", False)
DEFAULT_WAKE_WORDS = (
    "hey kairo",
    "ok kairo",
    "okay kairo",
    "hi kairo",
    "kairo",
    "hey cairo",
    "ok cairo",
    "okay cairo",
    "hi cairo",
    "cairo",
)
raw_wake_words = env("KAIRO_WAKE_WORDS", "")
if raw_wake_words:
    WAKE_WORDS = tuple(w.strip().lower() for w in raw_wake_words.split(",") if w.strip())
else:
    WAKE_WORDS = DEFAULT_WAKE_WORDS

WAKE_WORD_ACK = env("KAIRO_WAKE_WORD_ACK", "Ho boss, mi aiktey. Sangaa.")
# Conservative fuzzy matching catches speech-to-text variations such as Kiro,
# Kaira, Kay Ro, and Kairoo without accepting unrelated spoken sentences.
WAKEWORD_FUZZY_THRESHOLD = env_float("KAIRO_WAKEWORD_FUZZY_THRESHOLD", 0.78)

# Local-first mode. When a local model exists, KAIRO will use it before
# attempting cloud providers.
CLOUD_ONLY = env_bool("KAIRO_CLOUD_ONLY", False)
LLM_PROVIDER = env("KAIRO_LLM_PROVIDER", "openrouter").lower().strip()
raw_llm_fallbacks = env("KAIRO_LLM_FALLBACKS", "openrouter")
LLM_FALLBACKS = tuple(
    provider.strip().lower() for provider in raw_llm_fallbacks.split(",") if provider.strip()
)
LLM_REQUEST_TIMEOUT = env_float("KAIRO_LLM_REQUEST_TIMEOUT", 6.0)
GROQ_FAST_MODEL = env("KAIRO_GROQ_FAST_MODEL", "llama-3.1-8b-instant")
GROQ_COMPLEX_MODEL = env("KAIRO_GROQ_COMPLEX_MODEL", "llama-3.3-70b-versatile")
GEMINI_FAST_MODEL = env("KAIRO_GEMINI_FAST_MODEL", "gemini-2.5-flash")
OPENROUTER_FAST_MODEL = env("KAIRO_OPENROUTER_FAST_MODEL", "openrouter/free")
OPENROUTER_COMPLEX_MODEL = env("KAIRO_OPENROUTER_COMPLEX_MODEL", OPENROUTER_FAST_MODEL)
OPENAI_FAST_MODEL = env("KAIRO_OPENAI_FAST_MODEL", "gpt-4o-mini")
OPENAI_COMPLEX_MODEL = env("KAIRO_OPENAI_COMPLEX_MODEL", OPENAI_FAST_MODEL)
ANTHROPIC_FAST_MODEL = env("KAIRO_ANTHROPIC_FAST_MODEL", "claude-3-5-haiku-latest")
ANTHROPIC_COMPLEX_MODEL = env("KAIRO_ANTHROPIC_COMPLEX_MODEL", ANTHROPIC_FAST_MODEL)
DEV_AGENT_PROVIDER = env("KAIRO_DEV_AGENT_PROVIDER", "auto").lower().strip()
OPENAI_API_KEY = env("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = env("ANTHROPIC_API_KEY", "")
GROQ_API_KEY = env("GROQ_API_KEY", "")
ZLM_API_KEY = env("ZLM_API_KEY", "")
OPENROUTER_API_KEY = env("OPENROUTER_API_KEY", "")
GEMINI_API_KEY = env("GEMINI_API_KEY", "")

# Strict cloud vision, using only OpenRouter's free router by default. Camera
# and screen frames are uploaded only for an explicit request to look.
LOCAL_VISION_ENABLED = env_bool("KAIRO_LOCAL_VISION_ENABLED", False)
CLOUD_VISION_ENABLED = env_bool("KAIRO_CLOUD_VISION_ENABLED", True)
CLOUD_VISION_PROVIDER = env("KAIRO_CLOUD_VISION_PROVIDER", "openrouter").lower().strip()
OPENAI_VISION_MODEL = env("KAIRO_OPENAI_VISION_MODEL", "gpt-4o-mini")
GEMINI_VISION_MODEL = env("KAIRO_GEMINI_VISION_MODEL", GEMINI_FAST_MODEL)
OPENROUTER_VISION_MODEL = env("KAIRO_OPENROUTER_VISION_MODEL", "openrouter/free")

# Feature Flags
PROACTIVE_ENABLED = env_bool("KAIRO_PROACTIVE_ENABLED", True)
BACKGROUND_MONITOR_ENABLED = env_bool("KAIRO_BACKGROUND_MONITOR_ENABLED", True)
PARALLEL_SEARCH_ENABLED = env_bool("KAIRO_PARALLEL_SEARCH_ENABLED", True)
UI_HUD_ENABLED = env_bool("KAIRO_UI_HUD_ENABLED", False)
# A spoken confirmation is required before restart, shutdown, sleep, or sign-out.
# This prevents an accidental or overheard voice command from interrupting work.
DESKTOP_POWER_CONFIRMATION = env_bool("KAIRO_DESKTOP_POWER_CONFIRMATION", True)
