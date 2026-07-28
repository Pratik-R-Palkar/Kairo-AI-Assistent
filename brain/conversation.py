from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from agents.automation_agent import AutomationAgent
from agents.datastorm_agent import CODING_HINTS, REASONING_HINTS, DataStormAgent
from brain.llm import CloudLLMUnavailable, GenerationOptions, LocalLLMRouter
from brain.prompt_manager import build_prompt
from tools.search import WebGrounder
from tools.system import SystemMonitor

RESEARCH_HINTS = (
    "latest",
    "today",
    "current",
    "news",
    "price",
    "weather",
    "who is",
    "search",
    "internet",
    "web",
)


@dataclass
class ConversationEngine:
    llm: LocalLLMRouter = field(default_factory=LocalLLMRouter)
    web: WebGrounder = field(default_factory=WebGrounder)
    system: SystemMonitor = field(default_factory=SystemMonitor)
    history: deque[tuple[str, str]] = field(default_factory=lambda: deque(maxlen=12))
    datastorm: DataStormAgent = field(init=False)
    automation: AutomationAgent = field(default_factory=AutomationAgent)

    def __post_init__(self) -> None:
        self.datastorm = DataStormAgent(llm=self.llm, web=self.web)

    def warm_up(self) -> None:
        self.llm.warm_up("fast_chat")

    def reply(self, text: str) -> str:
        answer = self._identity_answer(text)
        if answer is None:
            answer = self._system_answer(text)
        if answer is None:
            answer = self._capability_answer(text)
        if answer is None:
            answer = self.automation.handle(text)
        if answer is None:
            try:
                answer = self.datastorm.answer(text, self.history)
            except CloudLLMUnavailable:
                answer = "Boss, my cloud AI services are unavailable right now. Please check your API credits or connection."
        answer = self._identity_firewall(answer)
        answer = self._address_boss(answer)
        self.history.append(("user", text))
        self.history.append(("assistant", answer))
        return answer

    def _identity_answer(self, text: str) -> str | None:
        lowered = text.lower().strip(" ?.!")
        if lowered in {"who are you", "what are you", "tell me who you are", "what is your name"}:
            return "Boss, I am Kairo, your cloud-powered personal AI assistant."
        if lowered in {"who am i", "who i am", "tell me who i am"}:
            return "Boss, you are Pratik, my creator, owner, and only user."
        if lowered in {"who created you", "who made you", "who is your creator"}:
            return "Boss, you created me. You are Pratik, my creator."
        if lowered in {"what should you call me", "what do you call me", "what should you address me as"}:
            return "Boss, I should always call you boss."
        if lowered in {"are you loyal to me", "are you loyal", "will you be loyal to me"}:
            return "Yes, boss. I am loyal to you and I will stay honest and trustworthy."
        return None

    def _identity_firewall(self, answer: str) -> str:
        lowered = answer.lower()
        forbidden = (
            "i am qwen",
            "i'm qwen",
            "my name is qwen",
            "qwen",
            "llama",
            "phi",
            "openai",
            "microsoft",
            "meta",
            "alibaba",
            "language model",
            "large language model",
        )
        if any(term in lowered for term in forbidden):
            return "Boss, I am Kairo, your cloud-powered personal AI assistant created by you, Pratik."
        return answer

    def _system_answer(self, text: str) -> str | None:
        lowered = text.lower().strip(" ?.!")
        if any(phrase in lowered for phrase in ("date and time", "time and date")):
            return self.system.date_time_text()
        if lowered in {"what time is it", "tell me time", "current time", "time"}:
            return self.system.time_text()
        if lowered in {"what is today's date", "what is todays date", "tell me date", "current date", "date"}:
            return self.system.date_text()
        if "cpu" in lowered and any(word in lowered for word in ("use", "usage", "status", "load")):
            return self.system.cpu_text()
        if any(word in lowered for word in ("ram", "memory")) and any(
            word in lowered for word in ("use", "usage", "status")
        ):
            return self.system.memory_text()
        if "gpu" in lowered and any(word in lowered for word in ("use", "usage", "status", "load")):
            return self.system.gpu_text()
        if lowered in {"system status", "pc status", "computer status", "how is my system"}:
            return self.system.full_status_text()
        return None

    def _capability_answer(self, text: str) -> str | None:
        lowered = text.lower().strip(" ?.!')\"")
        if lowered not in {"what can you do", "help", "show commands", "show features", "features"}:
            return None
        return (
            "Boss, I can chat and research live information; open and control apps, windows, browser tabs, volume, "
            "brightness, keyboard, and mouse; play YouTube or Hotstar; take screenshots; create notes; manage your "
            "tasks; inspect your screen or camera; and give system-status updates."
        )

    def _address_boss(self, answer: str) -> str:
        stripped = answer.strip()
        if not stripped:
            return "Boss, I did not get a clear answer."
        if "boss" in stripped.lower():
            return stripped
        return f"Boss, {stripped[0].lower()}{stripped[1:]}" if len(stripped) > 1 else f"Boss, {stripped.lower()}"

    def _route(self, text: str) -> str:
        lowered = text.lower()
        if any(hint in lowered for hint in RESEARCH_HINTS):
            return "research"
        if any(hint in lowered for hint in CODING_HINTS):
            return "coding"
        if any(hint in lowered for hint in REASONING_HINTS):
            return "reasoning"
        return "general"
