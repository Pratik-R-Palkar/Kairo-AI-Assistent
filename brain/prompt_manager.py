from __future__ import annotations

from datetime import datetime
from typing import Iterable

from brain.personality import SYSTEM_PROMPT


def build_prompt(
    user_message: str,
    history: Iterable[tuple[str, str]],
    web_context: str | None = None,
) -> list[dict[str, str]]:
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if web_context:
        now = datetime.now().strftime("%Y-%m-%d %H:%M")
        messages.append(
            {
                "role": "system",
                "content": (
                    f"Live web context gathered at {now}. Use it as source material, "
                    "but do not copy long passages verbatim.\n\n"
                    f"{web_context}"
                ),
            }
        )

    for role, content in history:
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_message})
    return messages
