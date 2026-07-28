from __future__ import annotations

import re
import string
import unicodedata
from difflib import SequenceMatcher
from typing import Sequence

from config import WAKE_WORDS, WAKE_WORD_REQUIRED, WAKEWORD_FUZZY_THRESHOLD


# Additional phonetic/mishearing mappings for Whisper output when listening to "Kairo" or "Cairo"
PHONETIC_VARIANTS = (
    "chairo",
    "kyro",
    "kayro",
    "karo",
    "cero",
    "cayro",
    "khairo",
    "kiro",
    "kira",
    "kaira",
    "kairoo",
    "cairoo",
    "kaero",
    "केरो",
    "कायरो",
)

PREFIX_TRIGGERS = (
    "hey",
    "ok",
    "okay",
    "hi",
    "hello",
    "listen",
)


class WakeWordDetector:
    """Detects custom wake word triggers (Kairo / Cairo) in text and audio streams."""

    def __init__(
        self,
        wake_words: Sequence[str] = WAKE_WORDS,
        required: bool = WAKE_WORD_REQUIRED,
    ) -> None:
        self.wake_words = tuple(w.lower().strip() for w in wake_words)
        self.required = required
        self.fuzzy_threshold = WAKEWORD_FUZZY_THRESHOLD
        self._regex_pattern = self._build_regex()
        self._wake_names = tuple(dict.fromkeys(("kairo", "cairo", *PHONETIC_VARIANTS)))

    def _build_regex(self) -> re.Pattern:
        """Build regex pattern covering all wake word combinations and mishearings."""
        # Target names: kairo, cairo, chairo, kyro, etc.
        names = ["kairo", "cairo"] + list(PHONETIC_VARIANTS)
        names_pattern = "|".join(re.escape(name) for name in names)
        prefixes_pattern = "|".join(re.escape(p) for p in PREFIX_TRIGGERS)

        # Matches: (hey/ok/hi/etc.)? (kairo/cairo/etc.)
        pattern_str = r"^(?:\b(?:%s)\b\s+)?\b(?:%s)\b" % (prefixes_pattern, names_pattern)
        return re.compile(pattern_str, re.IGNORECASE)

    def is_wake_word(self, text: str) -> bool:
        """Check if text contains or begins with a valid wake word phrase."""
        has_wake, _ = self.extract_command(text)
        return has_wake

    def extract_command(self, text: str) -> tuple[bool, str]:
        """
        Parses text for wake word trigger.
        Returns:
            (has_wake_word: bool, remaining_command: str)
        """
        if not text:
            return False, ""

        normalized = self._normalize(text)

        match = self._regex_pattern.search(normalized)
        if match:
            # Wake word matched at start of sentence
            matched_len = match.end()
            # Map back to clean_text approx location or strip leading match
            remaining = normalized[matched_len:].strip()
            return True, remaining

        fuzzy_command = self._extract_fuzzy_start(normalized)
        if fuzzy_command is not None:
            return True, fuzzy_command

        # Secondary check: check if any explicit configured wake word is in text
        lowered = normalized.lower()
        for ww in self.wake_words:
            if lowered.startswith(ww):
                remaining = normalized[len(ww):].strip()
                return True, remaining
            if ww in lowered:
                # Wake word embedded in text (e.g. "could you please kairo tell me a joke")
                idx = lowered.index(ww)
                remaining = (normalized[:idx] + " " + normalized[idx + len(ww):]).strip()
                return True, remaining

        return False, text.strip()

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize STT punctuation, casing, and repeated whitespace safely."""
        text = unicodedata.normalize("NFKC", text).lower().strip()
        # Keep Unicode letters (including Marathi) and digits; punctuation does
        # not carry wake-word meaning and often differs between STT providers.
        text = "".join(" " if (char in string.punctuation or unicodedata.category(char).startswith("P")) else char for char in text)
        return re.sub(r"\s+", " ", text).strip()

    def _extract_fuzzy_start(self, normalized: str) -> str | None:
        """Recognize likely Kairo pronunciations only at an utterance start.

        Restricting fuzzy matching to the first word (or the word after a
        greeting) prevents ordinary sentences from being treated as commands.
        """
        words = normalized.split()
        if not words:
            return None
        index = 1 if words[0] in PREFIX_TRIGGERS else 0
        if index >= len(words):
            return None

        candidates: list[tuple[str, int]] = [(words[index], 1)]
        if index + 1 < len(words):
            # Whisper sometimes separates a name as "Kay Ro".
            candidates.append((words[index] + words[index + 1], 2))

        for candidate, consumed in candidates:
            if len(candidate) < 3:
                continue
            score = max(SequenceMatcher(None, candidate, name).ratio() for name in self._wake_names)
            if score >= self.fuzzy_threshold:
                return " ".join(words[index + consumed:]).strip()
        return None

    def parse_utterance(self, text: str) -> tuple[bool, str]:
        """
        Helper method to filter user prompt based on requirement setting.
        - If wake word is required and missing: returns (False, "").
        - If wake word is present: returns (True, extracted_command).
        - If wake word is NOT required: returns (True, original_text).
        """
        has_wake, command = self.extract_command(text)
        if has_wake:
            return True, command
        if not self.required:
            return True, text
        return False, ""

    def wait_for_wakeword(self, recognizer) -> tuple[bool, str]:
        """
        Continuously listens via STT until a wake word (Kairo/Cairo) is detected.
        Returns (True, remaining_inline_command).
        """
        print("Listening for wake word ('Hey Kairo', 'OK Cairo', 'Cairo')...")
        while True:
            text = recognizer.listen_once()
            if not text:
                continue

            has_wake, command = self.extract_command(text)
            if has_wake:
                print(f"[wake_word] Wake word detected: '{text}'")
                return True, command
            elif not self.required:
                return True, text
