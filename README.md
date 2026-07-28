# KAIRO — Desktop AI Assistant

KAIRO is a production-ready desktop AI assistant with local-first voice and vision capabilities, a polished PyQt6 HUD interface, and deployable Windows packaging support.

> ⚠️ **Never commit your `.env` file or any API keys.** Use `.env.example` as a template.

---

## ⚡ Quick Start (Windows Installer)

1. Download and run `kairo setup.exe` from [Releases](../../releases)
2. On first launch, KAIRO shows a **one-time API setup screen**
3. Paste your API keys and click **Save & Launch**
4. Done — KAIRO remembers your keys and never asks again

---

## 🔑 API Keys — Where to Get Them

KAIRO uses several cloud services for voice and AI. Here are direct links to sign up and get your keys:

### 1. OpenRouter (Main AI Brain)
Used for cloud LLM responses (GPT, Claude, Gemini, Llama, and more via one key).
- 🔗 **Get your key:** https://openrouter.ai/keys
- Sign up free → Create API Key → Copy key starting with `sk-or-v1-...`
- Free tier available with many open-source models

### 2. Groq (Voice Transcription / STT)
Used for ultra-fast speech-to-text via Whisper Large v3.
- 🔗 **Get your key:** https://console.groq.com/keys
- Sign up free → API Keys → Create API Key → Copy key starting with `gsk_...`
- Free tier: 7,200 seconds/day of audio transcription

### 3. ElevenLabs (Voice Synthesis / TTS)
Used for realistic, expressive AI voice output.
- 🔗 **Get your key:** https://elevenlabs.io/app/settings/api-keys
- Sign up free → Profile → API Keys → Copy key starting with `sk_...`
- Free tier: 10,000 characters/month

### 4. Gemini (Optional — Google AI)
Used as an optional AI provider or fallback.
- 🔗 **Get your key:** https://aistudio.google.com/apikey
- Sign in with Google → Create API Key → Copy key starting with `AIzaSy...`
- Free tier: 15 requests/minute with Gemini Flash

### 5. OpenAI (Optional)
Used if you prefer GPT models directly.
- 🔗 **Get your key:** https://platform.openai.com/api-keys
- Sign up → API Keys → Create secret key → Copy key starting with `sk-...`
- Requires billing, but offers strong GPT-4o-mini tier

### 6. Anthropic (Optional)
Used if you prefer Claude models directly.
- 🔗 **Get your key:** https://console.anthropic.com/settings/keys
- Sign up → API Keys → Create Key → Copy key starting with `sk-ant-...`
- Requires billing

---

## 🖥️ System Requirements

| Spec | Minimum | Recommended |
|------|---------|-------------|
| OS | Windows 10 | Windows 11 |
| RAM | 8 GB | 16 GB+ |
| CPU | 4-core | 8-core |
| GPU | Optional | NVIDIA (CUDA) |
| Python | 3.10+ | 3.12 |

---

## 🤖 AI Modes

### Cloud AI Mode
- Uses internet APIs when available
- Best for fast responses and large-context tasks
- Requires at minimum an **OpenRouter** or **Groq** API key

### Local AI Mode
- Uses installed GGUF models on-device
- Full offline capability, zero data sent to cloud
- Works with just RAM — no GPU required

KAIRO automatically falls back to local models when offline, unless cloud-only mode is forced.

---

## 🏗️ Manual Setup (Developers)

```powershell
# 1. Create a virtual environment
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
copy .env.example .env
# Edit .env and fill in your API keys

# 4. Run KAIRO
python main.py
```

### Build Windows Installer

```powershell
# Requires Inno Setup 6 installed: https://jrsoftware.org/isdl.php
.\build.ps1
# Output: dist\setup.exe
```

---

## 🔧 Environment Configuration (`.env`)

### Cloud Mode Example
```env
KAIRO_CLOUD_ONLY=false
KAIRO_LLM_PROVIDER=openrouter
KAIRO_LLM_FALLBACKS=groq,openrouter
KAIRO_STT_PROVIDER=groq
KAIRO_TTS_PROVIDER=elevenlabs
GROQ_API_KEY=gsk_...
OPENROUTER_API_KEY=sk-or-v1-...
ELEVENLABS_API_KEYS=sk_...
GEMINI_API_KEY=AIzaSy...
```

### Local / Offline Mode Example
```env
KAIRO_CLOUD_ONLY=false
KAIRO_LLM_PROVIDER=local
KAIRO_LLM_FALLBACKS=
KAIRO_STT_PROVIDER=local
KAIRO_TTS_PROVIDER=kokoro
KAIRO_TTS_MODEL_REPO=hexgrad/Kokoro-82M
```

---

## 🎤 Desktop Voice Control

KAIRO can control your Windows desktop entirely by voice:

| Command | Example |
|---------|---------|
| App control | `Kairo, open Chrome`, `minimize this window`, `snap window left` |
| Typing | `type hello world and press enter`, `press control shift T` |
| Mouse | `move cursor to 800 450`, `double click at 800 450`, `click Settings` |
| System | `set volume to 40`, `mute`, `set brightness to 70` |
| Media | `play`, `pause`, `fullscreen`, `skip`, `take a screenshot` |
| Power | `lock my PC`, `restart`, `shutdown` *(requires spoken confirm)* |

> Power commands (restart, shutdown, sleep, sign-out) require a second spoken `confirm` by default.
> Set `KAIRO_DESKTOP_POWER_CONFIRMATION=false` to disable this safeguard.

---

## 📦 Recommended Local Models

| System | RAM | Recommended Model |
|--------|-----|-------------------|
| Low-end laptop | 8 GB | Qwen2.5-Coder 1.5B (bundled) |
| Mid-range desktop | 16 GB | Qwen2.5-Coder 1.5B or 3B-class |
| High-end desktop | 32 GB+ | 7B+ class GGUF models |

---

## 🔒 Privacy & Security

- API keys are stored locally in `%LocalAppData%\KAIRO\.env` (never in the install directory)
- Local mode sends **zero data** to any cloud
- Screen and camera data is only uploaded on explicit user request ("Kairo, look at my screen")
- Power/destructive commands require spoken confirmation

---

*Built with Python, PyQt6, llama.cpp, Kokoro TTS, Whisper STT, and ❤️*
