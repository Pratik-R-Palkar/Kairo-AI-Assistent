from __future__ import annotations

import threading


class VoiceState:
    """Shared, thread-safe switch for whether the assistant should listen."""

    def __init__(self, enabled: bool = True) -> None:
        self._lock = threading.Lock()
        self._enabled = enabled

    def is_enabled(self) -> bool:
        with self._lock:
            return self._enabled

    def set_enabled(self, enabled: bool) -> bool:
        with self._lock:
            self._enabled = enabled
            return self._enabled


voice_state = VoiceState()
