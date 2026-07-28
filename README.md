<div align="center">

<img src="assets/kairo_logo.png" alt="KAIRO Logo" width="120" />

<h1>
  <img src="https://readme-typing-svg.demolab.com?font=Orbitron&weight=700&size=36&pause=1000&color=F59E0B&center=true&vCenter=true&width=600&lines=KAIRO+AI+Assistant;Voice+%2B+Vision+%2B+Control;Local-First.+Privacy-First." alt="Typing SVG" />
</h1>

<p><em>A production-ready desktop AI assistant with voice, vision, and full Windows automation — powered by local-first AI.</em></p>

<br/>

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-UI-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-Local_LLM-orange?style=for-the-badge)](https://github.com/ggerganov/llama.cpp)
[![Whisper](https://img.shields.io/badge/Whisper-STT-00B4D8?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![Kokoro](https://img.shields.io/badge/Kokoro-TTS-blueviolet?style=for-the-badge)](https://huggingface.co/hexgrad/Kokoro-82M)
[![Windows](https://img.shields.io/badge/Windows-10%2F11-0078D6?style=for-the-badge&logo=windows&logoColor=white)](https://microsoft.com/windows)

<br/>

[![Stars](https://img.shields.io/github/stars/Pratik-R-Palkar/Kairo-AI-Assistent?style=social)](https://github.com/Pratik-R-Palkar/Kairo-AI-Assistent/stargazers)
[![Forks](https://img.shields.io/github/forks/Pratik-R-Palkar/Kairo-AI-Assistent?style=social)](https://github.com/Pratik-R-Palkar/Kairo-AI-Assistent/network/members)
[![Issues](https://img.shields.io/github/issues/Pratik-R-Palkar/Kairo-AI-Assistent?style=flat-square&color=F59E0B)](https://github.com/Pratik-R-Palkar/Kairo-AI-Assistent/issues)
[![License](https://img.shields.io/github/license/Pratik-R-Palkar/Kairo-AI-Assistent?style=flat-square)](LICENSE)

</div>

---

## ✨ Live Preview

<div align="center">
  <img src="assets/kairo_screenshot.png" alt="KAIRO HUD Dashboard" width="90%" />
  <br/>
  <sub>⚡ KAIRO HUD — Real-time system monitor, Arc Reactor core, voice waveform, and quick-launch panel</sub>
</div>

---

## 🚀 Features at a Glance

<div align="center">

| 🎙️ Voice Control | 👁️ Vision AI | 🧠 Local LLM | 🖥️ Desktop Automation |
|:-:|:-:|:-:|:-:|
| Wake-word detection | Screen & camera analysis | Offline GGUF models | App launch & control |
| Groq Whisper STT | Cloud vision fallback | Multi-model routing | Keyboard & mouse |
| ElevenLabs TTS | Object & text detection | Reasoning chains | Volume & brightness |
| Kokoro local voice | Privacy-first by default | Fast cloud fallback | Power management |

</div>

---

## ⚡ Quick Start (Windows Installer)

<div align="center">

```
1. Download setup.exe from Releases
2. Install → Launch KAIRO
3. Enter your API keys once in the setup screen
4. Done — KAIRO is ready to use 🎉
```

[![Download](https://img.shields.io/badge/⬇️_Download-setup.exe-F59E0B?style=for-the-badge)](../../releases)

</div>

> ⚠️ **Never commit your `.env` file or any API keys.** Use `.env.example` as a template.

> To Close Kairo Press: alt+f4

---

## 🔑 API Keys — Where to Get Them

KAIRO uses several cloud services for voice and AI. Here are direct links to sign up and get your keys:

### 1. 🟠 OpenRouter — Main AI Brain
Used for cloud LLM responses (GPT, Claude, Gemini, Llama, and more via one key).

[![OpenRouter](https://img.shields.io/badge/Get_Key-openrouter.ai%2Fkeys-orange?style=flat-square)](https://openrouter.ai/keys)

```
Sign up free → Create API Key → Copy key starting with sk-or-v1-...
Free tier: many open-source models available at no cost
```

### 2. 🟢 Groq — Voice Transcription (STT)
Used for ultra-fast speech-to-text via Whisper Large v3.

[![Groq](https://img.shields.io/badge/Get_Key-console.groq.com%2Fkeys-00A67E?style=flat-square)](https://console.groq.com/keys)

```
Sign up free → API Keys → Create API Key → Copy key starting with gsk_...
Free tier: 7,200 seconds/day of audio transcription
```

### 3. 🔵 ElevenLabs — Voice Synthesis (TTS)
Used for realistic, expressive AI voice output.

[![ElevenLabs](https://img.shields.io/badge/Get_Key-elevenlabs.io%2Fsettings-5B4FF7?style=flat-square)](https://elevenlabs.io/app/settings/api-keys)

```
Sign up free → Profile → API Keys → Copy key starting with sk_...
Free tier: 10,000 characters/month
```

### 4. 🔴 Gemini — Optional Google AI
Used as an optional AI provider or fallback.

[![Gemini](https://img.shields.io/badge/Get_Key-aistudio.google.com-EA4335?style=flat-square&logo=google&logoColor=white)](https://aistudio.google.com/apikey)

```
Sign in with Google → Create API Key → Copy key starting with AIzaSy...
Free tier: 15 requests/minute with Gemini Flash
```

### 5. ⚫ OpenAI — Optional GPT Models
Used if you prefer GPT models directly.

[![OpenAI](https://img.shields.io/badge/Get_Key-platform.openai.com-412991?style=flat-square&logo=openai&logoColor=white)](https://platform.openai.com/api-keys)

```
Sign up → API Keys → Create secret key → Copy key starting with sk-...
Requires billing — strong GPT-4o-mini tier available
```

### 6. 🟤 Anthropic — Optional Claude Models
Used if you prefer Claude models directly.

[![Anthropic](https://img.shields.io/badge/Get_Key-console.anthropic.com-D97706?style=flat-square)](https://console.anthropic.com/settings/keys)

```
Sign up → API Keys → Create Key → Copy key starting with sk-ant-...
Requires billing
```

---

## 🖥️ System Requirements

<div align="center">

| Spec | Minimum | Recommended |
|:-----|:-------:|:-----------:|
| 🪟 OS | Windows 10 | Windows 11 |
| 🧠 RAM | 8 GB | 16 GB+ |
| ⚙️ CPU | 4-core | 8-core |
| 🎮 GPU | Optional | NVIDIA (CUDA) |
| 🐍 Python | 3.10+ | 3.12 |

</div>

---

## 🤖 AI Modes

<details>
<summary><b>☁️ Cloud AI Mode</b> — Click to expand</summary>
<br/>

- Uses internet APIs when available
- Best for fast responses and large-context tasks
- Requires at minimum an **OpenRouter** or **Groq** API key
- Automatic fallback to local models when offline

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

</details>

<details>
<summary><b>💻 Local / Offline Mode</b> — Click to expand</summary>
<br/>

- Full offline capability — zero data sent to cloud
- Privacy-first by design
- Works with just RAM — no GPU required

```env
KAIRO_CLOUD_ONLY=false
KAIRO_LLM_PROVIDER=local
KAIRO_LLM_FALLBACKS=
KAIRO_STT_PROVIDER=local
KAIRO_TTS_PROVIDER=kokoro
KAIRO_TTS_MODEL_REPO=hexgrad/Kokoro-82M
```

</details>

---

## 🏗️ Developer Setup

<details>
<summary><b>Manual Setup Instructions</b> — Click to expand</summary>
<br/>

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
# Requires Inno Setup 6: https://jrsoftware.org/isdl.php
.\build.ps1
# Output: dist\setup.exe
```

</details>

---

## 🎤 Desktop Voice Control

<div align="center">

| Command Category | Example Commands |
|:----------------|:----------------|
| 🖥️ **App Control** | `Kairo, open Chrome` · `minimize this window` · `snap window left` |
| ⌨️ **Typing** | `type hello world and press enter` · `press control shift T` |
| 🖱️ **Mouse** | `move cursor to 800 450` · `double click at 800 450` · `click Settings` |
| 🔊 **System** | `set volume to 40` · `mute` · `set brightness to 70` |
| 🎵 **Media** | `play` · `pause` · `fullscreen` · `skip` · `take a screenshot` |
| ⚡ **Power** | `lock my PC` · `restart` · `shutdown` *(requires spoken confirm)* |

</div>

> 🔒 Power commands (restart, shutdown, sleep, sign-out) require a second spoken `confirm` by default.
> Set `KAIRO_DESKTOP_POWER_CONFIRMATION=false` to disable this safeguard.

---

## 📦 Recommended Local Models

<div align="center">

| 💻 System | 🧠 RAM | 🤖 Recommended Model |
|:---------:|:------:|:-------------------:|
| Low-end laptop | 8 GB | Qwen2.5-Coder 1.5B *(bundled)* |
| Mid-range desktop | 16 GB | Qwen2.5-Coder 1.5B or 3B-class |
| High-end desktop | 32 GB+ | 7B+ class GGUF models |

</div>

---

## 🔒 Privacy & Security

<div align="center">

```
🔐 API keys stored locally in %LocalAppData%\KAIRO\.env — never in install directory
🚫 Local mode sends ZERO data to any cloud service
👁️ Screen & camera only uploaded on explicit user request
🔊 Power commands always require spoken confirmation
```

</div>

---

## 🛠️ Built With

<div align="center">

[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-41CD52?style=for-the-badge&logo=qt&logoColor=white)](https://riverbankcomputing.com/software/pyqt/)
[![llama.cpp](https://img.shields.io/badge/llama.cpp-F59E0B?style=for-the-badge)](https://github.com/ggerganov/llama.cpp)
[![OpenAI Whisper](https://img.shields.io/badge/Whisper-412991?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![Kokoro TTS](https://img.shields.io/badge/Kokoro_TTS-blueviolet?style=for-the-badge)](https://huggingface.co/hexgrad/Kokoro-82M)
[![ElevenLabs](https://img.shields.io/badge/ElevenLabs-000000?style=for-the-badge)](https://elevenlabs.io)
[![Groq](https://img.shields.io/badge/Groq-00A67E?style=for-the-badge)](https://groq.com)
[![OpenRouter](https://img.shields.io/badge/OpenRouter-FF6B35?style=for-the-badge)](https://openrouter.ai)

</div>

---

<div align="center">

<img src="https://readme-typing-svg.demolab.com?font=Fira+Code&size=14&pause=1000&color=F59E0B&center=true&vCenter=true&width=500&lines=Built+with+Python%2C+PyQt6%2C+and+%E2%9D%A4%EF%B8%8F;Local-first+%E2%80%A2+Privacy-first+%E2%80%A2+Offline-capable;Star+%E2%AD%90+the+repo+if+you+find+it+useful!" alt="Footer typing" />

[![Star this repo](https://img.shields.io/badge/⭐_Star_this_repo-F59E0B?style=for-the-badge)](https://github.com/Pratik-R-Palkar/Kairo-AI-Assistent)

</div>
