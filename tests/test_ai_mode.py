import unittest

from brain.llm import LocalLLMRouter


class AIModeTests(unittest.TestCase):
    def test_auto_mode_falls_back_to_local_when_offline(self) -> None:
        router = LocalLLMRouter()
        router._internet_available = lambda: False  # type: ignore[assignment]
        self.assertFalse(router._should_use_cloud())

    def test_cloud_mode_forces_cloud_path(self) -> None:
        router = LocalLLMRouter()
        router._internet_available = lambda: False  # type: ignore[assignment]
        router.mode = "cloud"
        self.assertTrue(router._should_use_cloud())


if __name__ == "__main__":
    unittest.main()
