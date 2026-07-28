from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch
import numpy as np

from voice.tts import KokoroTTS, _is_devanagari, _preprocess_text, _transliterate_roman_marathi


class TestTTS(unittest.TestCase):

    def test_is_devanagari(self) -> None:
        # Marathi test cases
        self.assertTrue(_is_devanagari("नमस्कार"))
        self.assertTrue(_is_devanagari("मी कायरो आहे."))
        self.assertTrue(_is_devanagari("शुभ प्रभात, तुम्ही कसे आहात?"))
        
        # Hindi test cases
        self.assertTrue(_is_devanagari("नमस्ते, आप कैसे हैं?"))
        
        # Mixed script test cases (contains at least one Devanagari character)
        self.assertTrue(_is_devanagari("Hello नमस्कार"))

        # English / Non-Devanagari test cases
        self.assertFalse(_is_devanagari("Hello, how are you?"))
        self.assertFalse(_is_devanagari("Kairo voice assistant 123!"))
        self.assertFalse(_is_devanagari(""))

    def test_transliterate_roman_marathi(self) -> None:
        roman_text = "namaskar, me kairo ahe. mazya kade tumchya sathi uttar ahe."
        transliterated = _transliterate_roman_marathi(roman_text)
        self.assertIn("नमस्कार,", transliterated)
        self.assertIn("मी", transliterated)
        self.assertIn("माझ्या", transliterated)
        self.assertIn("कडे", transliterated)
        self.assertIn("उत्तर", transliterated)

    def test_preprocess_text_greetings_and_pauses(self) -> None:
        raw_text = "नमस्कार! मी कायरो आहे आणि मी मदत करू शकतो।"
        processed = _preprocess_text(raw_text)
        self.assertIn("नमस्कार,", processed)
        self.assertNotIn("नमस्कार!", processed)
        self.assertIn(".", processed)
        self.assertNotIn("।", processed)
        self.assertIn(", आणि", processed)

    def test_preprocess_text_joint_words(self) -> None:
        raw_text = "कामांच्या मध्ये आणि ऑपरेशन्स मध्ये समस्या आहे"
        processed = _preprocess_text(raw_text)
        self.assertIn("कामांच्यामध्ये", processed)
        self.assertIn("ऑपरेशन्समध्ये", processed)

    def test_preprocess_text_kade_separation(self) -> None:
        raw_text = "माझ्याकडे सर्व माहिती आहे"
        processed = _preprocess_text(raw_text)
        self.assertIn("माझ्या कडे", processed)
        self.assertNotIn("माझ्याकडे", processed)

    def test_preprocess_text_schwa_syncope(self) -> None:
        raw_text = "मी तुमच्या रोजच्या कामात तुमच्यासोबत आहे"
        processed = _preprocess_text(raw_text)
        self.assertIn("तुम्च्या", processed)
        self.assertIn("रोज्च्या", processed)
        self.assertNotIn("तुमच्या", processed)
        self.assertNotIn("रोजच्या", processed)

    def test_split_text(self) -> None:
        tts = KokoroTTS(voice_blend="")
        text = "Hello there. How are you doing today? I am fine!"
        parts = tts._split_text(text)
        self.assertEqual(parts, ["Hello there.", "How are you doing today?", "I am fine!"])

    def test_split_text_marathi(self) -> None:
        tts = KokoroTTS(voice_blend="")
        text = "नमस्कार, मी कायरो आहे. तुम्ही कसे आहात?"
        parts = tts._split_text(text)
        self.assertEqual(parts, ["नमस्कार, मी कायरो आहे.", "तुम्ही कसे आहात?"])

    @patch("voice.tts.KokoroTTS._get_pipeline")
    def test_generate_audio_chunks_language_routing(self, mock_get_pipeline: MagicMock) -> None:
        mock_pipeline = MagicMock()
        mock_pipeline.lang_code = "a"
        dummy_audio = np.zeros(24000, dtype=np.float32)
        mock_pipeline.return_value = [("g", "p", dummy_audio)]
        mock_get_pipeline.return_value = mock_pipeline

        tts = KokoroTTS(lang_code="a", voice_blend="")

        # Test English routing -> should request 'a' pipeline
        list(tts._generate_audio_chunks("Hello world"))
        mock_get_pipeline.assert_called_with("a")

        # Test Marathi Devanagari routing -> should request 'h' pipeline
        list(tts._generate_audio_chunks("नमस्कार कायरो"))
        mock_get_pipeline.assert_called_with("h")



if __name__ == "__main__":
    unittest.main()
