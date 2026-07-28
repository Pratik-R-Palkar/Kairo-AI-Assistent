from __future__ import annotations

import unittest
from unittest.mock import MagicMock

from vision.vision_agent import VisionAgent


class _LocalVision:
    def describe_screen(self) -> str:
        return "A YouTube window is open."

    def describe_screen_and_camera(self) -> str:
        return "I can see one person in the camera frame."

    def answer_visual_question(self, question: str) -> str:
        return f"local answer: {question}"


class TestLocalVisionAgent(unittest.TestCase):
    def setUp(self) -> None:
        # Avoid starting capture threads or loading a model in command-routing tests.
        self.agent = VisionAgent.__new__(VisionAgent)
        self.agent.local = _LocalVision()
        self.agent.cloud = MagicMock()
        self.agent.cloud.available.return_value = False

    def test_descriptions_use_local_perception(self) -> None:
        self.assertEqual(self.agent.describe_screen(), "A YouTube window is open.")
        self.assertEqual(
            self.agent.describe_screen_and_cam(),
            "I can see one person in the camera frame.",
        )
        self.assertEqual(self.agent.answer_screen_question("What is open?"), "local answer: What is open?")

    def test_click_does_not_claim_success_when_locator_fails(self) -> None:
        self.agent.finder = MagicMock()
        self.agent.finder.find_element_center.return_value = None
        self.agent.windows = MagicMock()
        self.agent.windows.get_active_window_title.return_value = "YouTube - Chrome"
        self.agent.mouse = MagicMock()

        answer = self.agent.see_and_click("Your videos")

        self.assertIn("could not locate", answer)
        self.assertIn("YouTube window", answer)
        self.agent.mouse.click.assert_not_called()


if __name__ == "__main__":
    unittest.main()
