# KAIRO

KAIRO is a production-ready desktop AI assistant with local-first voice and vision capabilities, a polished PyQt interface, and deployable packaging support.

> Important: never commit your `.env` file or any API keys. Use `.env.example` as a template.

## Deployment
- Install dependencies with `pip install -r requirements.txt`
- Launch with `python main.py`
- For Windows packaging, run `build.ps1` to produce a distributable executable in the `dist` folder
- If you prefer manual packaging, use `pyinstaller --onefile --noconsole --icon assets/icon.ico main.py`

## System requirements
- Windows 10/11 recommended
- 8 GB RAM minimum, 16 GB recommended
- 4-core CPU minimum
- NVIDIA GPU optional, CPU-only works for local models
- Python 3.10+ and a virtual environment recommended

## AI modes
KAIRO supports two modes:

1. Cloud AI mode
- Uses internet APIs when the network is available.
- Best for fast responses and large-context tasks.
- Requires API keys such as OpenRouter, Groq, or OpenAI.

2. Local AI mode
- Uses installed local GGUF models when internet is unavailable or when you prefer privacy.
- Best for offline use and private work.
- Works well on systems with enough RAM and disk space.

The app will automatically fall back to local models when internet is unavailable, unless you explicitly force cloud mode.

## Recommended local models by system
- Low-end laptop / 8 GB RAM
  - Use the bundled 1.5B Qwen model for everyday chat and light coding.
  - Good balance of speed and memory use.
- Mid-range desktop / 16 GB RAM
  - Use the same 1.5B model for comfort, or a larger 3B-class local model if available.
  - Better for longer conversations and coding tasks.
- High-end desktop / 32 GB+ RAM
  - Prefer larger 7B+ local models if available.
  - Best for more detailed reasoning and document-heavy tasks.

## API setup guide
Create a `.env` file from `.env.example` and fill in only the providers you want to use.

### Cloud mode
```text
KAIRO_CLOUD_ONLY=false
KAIRO_LLM_PROVIDER=openrouter
KAIRO_LLM_FALLBACKS=openrouter
KAIRO_STT_PROVIDER=groq
KAIRO_TTS_PROVIDER=elevenlabs
GROQ_API_KEY=...
OPENROUTER_API_KEY=...
ELEVENLABS_API_KEYS=...
```

### Local mode
```text
KAIRO_CLOUD_ONLY=false
KAIRO_LLM_PROVIDER=local
KAIRO_LLM_FALLBACKS=
KAIRO_STT_PROVIDER=local
KAIRO_TTS_PROVIDER=kokoro
KAIRO_TTS_MODEL_REPO=hexgrad/Kokoro-82M
```

## Run
```powershell
.\.venv\Scripts\python.exe main.py
```

## Desktop voice control
Kairo can control the active Windows desktop by voice. Examples:

- `Kairo, open Chrome`, `focus VS Code`, `minimize this window`, `snap window left`
- `type hello world and press enter`, `press control shift t`, `new tab`, `next tab`
- `move cursor to 800, 450`, `double click at 800 450`, `click Settings`
- `set volume to 40`, `mute`, `set brightness to 70`, `open WiFi settings`
- `play`, `pause`, `fullscreen`, `skip`, `take a screenshot`, `lock my PC`

Restart, shutdown, sleep, and sign-out require a second spoken `confirm` by default. Set `KAIRO_DESKTOP_POWER_CONFIRMATION=false` only if you intentionally want to disable that safeguard.
