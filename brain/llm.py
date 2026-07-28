from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import requests
from requests.adapters import HTTPAdapter

from config import (
    ANTHROPIC_API_KEY,
    ANTHROPIC_COMPLEX_MODEL,
    ANTHROPIC_FAST_MODEL,
    CLOUD_ONLY,
    GEMINI_API_KEY,
    GEMINI_FAST_MODEL,
    GROQ_API_KEY,
    GROQ_COMPLEX_MODEL,
    GROQ_FAST_MODEL,
    LLM_FALLBACKS,
    LLM_PROVIDER,
    LLM_REQUEST_TIMEOUT,
    MODEL_ROUTES,
    OPENAI_API_KEY,
    OPENAI_COMPLEX_MODEL,
    OPENAI_FAST_MODEL,
    OPENROUTER_API_KEY,
    OPENROUTER_COMPLEX_MODEL,
    OPENROUTER_FAST_MODEL,
    ModelConfig,
)

logger = logging.getLogger(__name__)


class CloudLLMUnavailable(RuntimeError):
    """Raised only when every configured cloud provider is unavailable."""


@dataclass
class GenerationOptions:
    max_tokens: int = 512
    temperature: float | None = None
    top_p: float | None = None


class LocalLLMRouter:
    """Cloud-first LLM router with fast, credit-aware provider failover.

    The historical class name is kept so the rest of Kairo continues to work.
    With ``KAIRO_CLOUD_ONLY=true`` (the default), it never loads a local GGUF
    model after a cloud failure.
    """

    _COMPLEX_ROUTES = frozenset({"coding", "reasoning", "research"})

    def __init__(self) -> None:
        self._models: Dict[str, Any] = {}
        self.provider = LLM_PROVIDER or "auto"
        self.mode = "auto"
        self._session = requests.Session()
        self._session.mount("https://", HTTPAdapter(pool_connections=4, pool_maxsize=4))

    def available(self, route: str = "general") -> bool:
        return bool(self._provider_order()) or (
            not CLOUD_ONLY and Path(MODEL_ROUTES.get(route, MODEL_ROUTES["general"]).local_path).exists()
        )

    def _internet_available(self) -> bool:
        try:
            requests.get("https://api.openrouter.ai", timeout=2.5)
            return True
        except Exception:
            return False

    def _should_use_cloud(self) -> bool:
        if self.mode == "cloud":
            return True
        if self.mode == "local":
            return False
        return self._internet_available() and not CLOUD_ONLY

    def warm_up(self, route: str = "fast_chat") -> None:
        # Do not make paid warm-up requests. The persistent Session preserves
        # connections once the first real request is made.
        providers = self._provider_order()
        if providers:
            logger.info("Cloud fast lane ready: %s", ", ".join(providers))
            return
        if not CLOUD_ONLY:
            config = MODEL_ROUTES.get(route, MODEL_ROUTES["general"])
            if Path(config.local_path).exists():
                self._load(config)

    def generate(
        self,
        messages: list[dict[str, str]] | str,
        route: str = "general",
        options: GenerationOptions | None = None,
    ) -> str:
        options = options or GenerationOptions()
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]

        if self._should_use_cloud():
            failures: list[str] = []
            for provider in self._provider_order():
                try:
                    text = self._generate_cloud(provider, messages, route, options)
                    if text:
                        return self._clean_output(text)
                except Exception as exc:
                    failures.append(f"{provider}: {exc}")
                    logger.warning("%s LLM failed: %s", provider, exc)

        if not CLOUD_ONLY or self.mode == "local":
            return self._generate_local(messages, route, options)

        detail = "; ".join(failures) or "no configured cloud API key"
        raise CloudLLMUnavailable(f"Cloud AI is unavailable ({detail}).")

    def _provider_order(self) -> tuple[str, ...]:
        configured = {
            "groq": bool(GROQ_API_KEY),
            "gemini": bool(GEMINI_API_KEY),
            "openrouter": bool(OPENROUTER_API_KEY),
            "openai": bool(OPENAI_API_KEY),
            "anthropic": bool(ANTHROPIC_API_KEY),
        }
        requested = list(LLM_FALLBACKS)
        if self.provider and self.provider != "auto":
            requested = [self.provider, *[p for p in requested if p != self.provider]]
        return tuple(provider for provider in requested if configured.get(provider, False))

    def _generate_cloud(
        self,
        provider: str,
        messages: list[dict[str, str]],
        route: str,
        options: GenerationOptions,
    ) -> str:
        if provider == "groq":
            return self._generate_openai_compatible(
                "https://api.groq.com/openai/v1/chat/completions",
                GROQ_API_KEY,
                self._model_for("groq", route),
                messages,
                options,
            )
        if provider == "openrouter":
            return self._generate_openai_compatible(
                "https://openrouter.ai/api/v1/chat/completions",
                OPENROUTER_API_KEY,
                self._model_for("openrouter", route),
                messages,
                options,
                extra_headers={"HTTP-Referer": "https://github.com/kairo", "X-Title": "Kairo"},
            )
        if provider == "openai":
            return self._generate_openai_compatible(
                "https://api.openai.com/v1/chat/completions",
                OPENAI_API_KEY,
                self._model_for("openai", route),
                messages,
                options,
            )
        if provider == "gemini":
            return self._generate_gemini(messages, options)
        if provider == "anthropic":
            return self._generate_anthropic(messages, route, options)
        raise ValueError(f"Unsupported cloud provider: {provider}")

    def _generate_openai_compatible(
        self,
        url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        options: GenerationOptions,
        extra_headers: dict[str, str] | None = None,
    ) -> str:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Kairo/2.0",
        }
        if extra_headers:
            headers.update(extra_headers)
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
            "max_tokens": options.max_tokens,
            "temperature": options.temperature if options.temperature is not None else 0.45,
        }
        if options.top_p is not None:
            payload["top_p"] = options.top_p
        response = self._session.post(url, json=payload, headers=headers, timeout=LLM_REQUEST_TIMEOUT)
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:180]}")
        data = response.json()
        return str(data["choices"][0]["message"]["content"] or "")

    def _generate_gemini(
        self,
        messages: list[dict[str, str]],
        options: GenerationOptions,
    ) -> str:
        system_parts = [m.get("content", "") for m in messages if m.get("role") == "system"]
        content = [
            {"role": "model" if m.get("role") == "assistant" else "user", "parts": [{"text": m.get("content", "")}]} 
            for m in messages
            if m.get("role") != "system"
        ]
        payload: dict[str, Any] = {
            "contents": content or [{"role": "user", "parts": [{"text": "Hello"}]}],
            "generationConfig": {
                "maxOutputTokens": options.max_tokens,
                "temperature": options.temperature if options.temperature is not None else 0.45,
            },
        }
        if system_parts:
            payload["systemInstruction"] = {"parts": [{"text": "\n".join(system_parts)}]}
        url = (
            "https://generativelanguage.googleapis.com/v1beta/models/"
            f"{GEMINI_FAST_MODEL}:generateContent?key={GEMINI_API_KEY}"
        )
        response = self._session.post(url, json=payload, timeout=LLM_REQUEST_TIMEOUT)
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:180]}")
        parts = response.json()["candidates"][0]["content"]["parts"]
        return "".join(str(part.get("text", "")) for part in parts)

    def _generate_anthropic(
        self,
        messages: list[dict[str, str]],
        route: str,
        options: GenerationOptions,
    ) -> str:
        system = "\n".join(m.get("content", "") for m in messages if m.get("role") == "system")
        payload: dict[str, Any] = {
            "model": self._model_for("anthropic", route),
            "max_tokens": options.max_tokens,
            "temperature": options.temperature if options.temperature is not None else 0.45,
            "messages": [m for m in messages if m.get("role") != "system"],
        }
        if system:
            payload["system"] = system
        response = self._session.post(
            "https://api.anthropic.com/v1/messages",
            json=payload,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
                "User-Agent": "Kairo/2.0",
            },
            timeout=LLM_REQUEST_TIMEOUT,
        )
        if response.status_code != 200:
            raise RuntimeError(f"HTTP {response.status_code}: {response.text[:180]}")
        return "".join(str(part.get("text", "")) for part in response.json().get("content", []))

    def _model_for(self, provider: str, route: str) -> str:
        complex_request = route in self._COMPLEX_ROUTES
        models = {
            "groq": (GROQ_FAST_MODEL, GROQ_COMPLEX_MODEL),
            "openrouter": (OPENROUTER_FAST_MODEL, OPENROUTER_COMPLEX_MODEL),
            "openai": (OPENAI_FAST_MODEL, OPENAI_COMPLEX_MODEL),
            "anthropic": (ANTHROPIC_FAST_MODEL, ANTHROPIC_COMPLEX_MODEL),
        }
        fast, complex_model = models[provider]
        return complex_model if complex_request else fast

    def _generate_local(
        self,
        messages: list[dict[str, str]],
        route: str,
        options: GenerationOptions,
    ) -> str:
        config = MODEL_ROUTES.get(route, MODEL_ROUTES["general"])
        model = self._load(config)
        result = model.create_chat_completion(
            messages=messages,
            max_tokens=options.max_tokens,
            temperature=options.temperature if options.temperature is not None else config.temperature,
            top_p=options.top_p if options.top_p is not None else config.top_p,
        )
        return self._clean_output(result["choices"][0]["message"]["content"])

    @staticmethod
    def _clean_output(text: str) -> str:
        return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

    def _load(self, config: ModelConfig) -> Any:
        key = str(config.local_path)
        if key in self._models:
            return self._models[key]
        if not Path(config.local_path).exists():
            raise FileNotFoundError(f"Missing {config.role} model at {config.local_path}.")
        from llama_cpp import Llama

        self._models[key] = Llama(
            model_path=str(config.local_path),
            n_ctx=config.context,
            n_threads=None,
            n_gpu_layers=-1,
            verbose=False,
        )
        return self._models[key]


LLMRouter = LocalLLMRouter
