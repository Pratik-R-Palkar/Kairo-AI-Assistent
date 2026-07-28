from __future__ import annotations

import unittest
from voice.wakeword import WakeWordDetector


class TestWakeWordDetector(unittest.TestCase):

    def setUp(self) -> None:
        self.detector = WakeWordDetector()

    def test_kairo_variants(self) -> None:
        test_cases = [
            ("hey kairo", True, ""),
            ("ok kairo", True, ""),
            ("kairo", True, ""),
            ("okay kairo", True, ""),
            ("hi kairo", True, ""),
        ]
        for text, expected_has_wake, _ in test_cases:
            has_wake, command = self.detector.extract_command(text)
            self.assertTrue(has_wake, f"Failed wake word detection for: '{text}'")

    def test_cairo_variants(self) -> None:
        test_cases = [
            ("hey cairo", True, ""),
            ("ok cairo", True, ""),
            ("cairo", True, ""),
            ("okay cairo", True, ""),
            ("hi cairo", True, ""),
        ]
        for text, expected_has_wake, _ in test_cases:
            has_wake, command = self.detector.extract_command(text)
            self.assertTrue(has_wake, f"Failed wake word detection for: '{text}'")

    def test_mishearing_phonetics(self) -> None:
        test_cases = ["chairo", "ok chairo", "kyro", "kayro", "kiro", "kaira", "kairoo", "hey kay ro"]
        for text in test_cases:
            has_wake, _ = self.detector.extract_command(text)
            self.assertTrue(has_wake, f"Failed phonetic wake word detection for: '{text}'")

    def test_fuzzy_start_matching_keeps_inline_command(self) -> None:
        has_wake, command = self.detector.extract_command("Hey Kiaro open Chrome")
        self.assertTrue(has_wake)
        self.assertEqual(command, "open chrome")

    def test_inline_commands(self) -> None:
        test_cases = [
            ("Hey Kairo what time is it?", True, "what time is it"),
            ("OK Cairo search for python tutorials", True, "search for python tutorials"),
            ("Cairo tell me a joke", True, "tell me a joke"),
            ("ok cairo play music", True, "play music"),
        ]
        for text, expected_has_wake, expected_command in test_cases:
            has_wake, command = self.detector.extract_command(text)
            self.assertTrue(has_wake, f"Failed wake word detection in inline command: '{text}'")
            self.assertEqual(
                command.lower().strip("?."),
                expected_command.lower(),
                f"Extracted command mismatch for '{text}'. Got '{command}'",
            )

    def test_non_wake_word_inputs(self) -> None:
        non_wake_words = [
            "what is the weather today",
            "open google chrome",
            "hello world",
        ]
        for text in non_wake_words:
            has_wake, command = self.detector.extract_command(text)
            self.assertFalse(has_wake, f"False positive wake word detection for: '{text}'")


if __name__ == "__main__":
    unittest.main()
