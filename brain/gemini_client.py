from __future__ import annotations

import time
import requests
from config import GEMINI_API_KEY, USER_TITLE


class GeminiTokenOptimizedClient:
    """Token-optimized Gemini Flash Client for Free-Trial API Accounts."""

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or GEMINI_API_KEY
        self.model_name = "gemini-2.5-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent"

    def generate(self, prompt: str, system_instruction: str | None = None, max_tokens: int = 200) -> str | None:
        if not self.api_key:
            return None

        url = f"{self.base_url}?key={self.api_key}"
        parts = []
        if system_instruction:
            parts.append({"text": f"System: {system_instruction}\n\nUser: {prompt}"})
        else:
            parts.append({"text": prompt})

        payload = {
            "contents": [{"parts": parts}],
            "generationConfig": {
                "maxOutputTokens": min(max_tokens, 250),  # Preserve free-trial quota
                "temperature": 0.3,
            },
        }

        try:
            start_t = time.time()
            res = requests.post(url, json=payload, timeout=6)
            if res.status_code == 200:
                data = res.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                elapsed = time.time() - start_t
                print(f"[Gemini 2.5 Flash] Responded in {elapsed:.2f}s (Tokens preserved)")
                return text
            elif res.status_code == 429:
                print("[Gemini API] Rate limit hit. The cloud router will try the next configured provider.")
                return None
            else:
                print(f"[Gemini API Note] Status {res.status_code}: {res.text[:100]}")
        except Exception as exc:
            print(f"[Gemini API Error] {exc}")

        return None


_GEMINI_CLIENT: GeminiTokenOptimizedClient | None = None


def get_gemini_client() -> GeminiTokenOptimizedClient:
    global _GEMINI_CLIENT
    if _GEMINI_CLIENT is None:
        _GEMINI_CLIENT = GeminiTokenOptimizedClient()
    return _GEMINI_CLIENT
