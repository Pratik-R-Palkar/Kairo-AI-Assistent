import unittest

from config import WAKE_WORD_REQUIRED
from voice.wakeword import WakeWordDetector


class VoiceControlsTests(unittest.TestCase):
    def test_wake_word_is_not_required_by_default(self) -> None:
        detector = WakeWordDetector(required=WAKE_WORD_REQUIRED)
        accepted, command = detector.parse_utterance("hey kairo tell me the time")
        self.assertTrue(accepted)
        self.assertEqual(command, "tell me the time")


if __name__ == "__main__":
    unittest.main()
