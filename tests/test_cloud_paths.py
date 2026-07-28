from __future__ import annotations

import unittest
from unittest.mock import MagicMock, patch

from brain.llm import CloudLLMUnavailable, LocalLLMRouter
from voice.tts import ElevenLabsTTS


class TestCloudRouting(unittest.TestCase):
    def test_fails_over_without_loading_a_local_model(self) -> None:
        router = LocalLLMRouter()
        router._provider_order = MagicMock(return_value=("groq", "gemini"))
        router._generate_cloud = MagicMock(side_effect=[RuntimeError("quota"), "Cloud reply"])
        router._generate_local = MagicMock()

        with patch("brain.llm.CLOUD_ONLY", True):
            reply = router.generate("Hello")

        self.assertEqual(reply, "Cloud reply")
        router._generate_local.assert_not_called()
        self.assertEqual(router._generate_cloud.call_count, 2)

    def test_cloud_only_reports_outage_instead_of_falling_back_local(self) -> None:
        router = LocalLLMRouter()
        router._provider_order = MagicMock(return_value=("groq",))
        router._generate_cloud = MagicMock(side_effect=RuntimeError("quota"))
        router._generate_local = MagicMock()

        with patch("brain.llm.CLOUD_ONLY", True):
            with self.assertRaises(CloudLLMUnavailable):
                router.generate("Hello")

        router._generate_local.assert_not_called()


class TestElevenLabsDelivery(unittest.TestCase):
    def setUp(self) -> None:
        self.tts = ElevenLabsTTS(api_keys=["test-key"], model_id="eleven_flash_v2_5")
        self.tts.expressive_enabled = True
        self.tts.expressive_model_id = "eleven_v3"

    def test_normal_reply_stays_on_fast_flash_model(self) -> None:
        model, spoken = self.tts._delivery("I have opened the browser, boss.")
        self.assertEqual(model, "eleven_flash_v2_5")
        self.assertEqual(spoken, "I have opened the browser, boss.")

    def test_joke_uses_private_expressive_tag(self) -> None:
        model, spoken = self.tts._delivery("That was a funny joke, boss.")
        self.assertEqual(model, "eleven_v3")
        self.assertTrue(spoken.startswith("[laughs softly]"))

    def test_supportive_reply_uses_sad_delivery(self) -> None:
        model, spoken = self.tts._delivery("I am sorry you are feeling sad, boss.")
        self.assertEqual(model, "eleven_v3")
        self.assertTrue(spoken.startswith("[sadly]"))


if __name__ == "__main__":
    unittest.main()
