import importlib
import os
import sys
import unittest


class ElevenLabsConfigTests(unittest.TestCase):
    def test_parse_env_list_supports_newlines_and_commas(self):
        os.environ["ELEVENLABS_API_KEYS"] = "sk_a,\nsk_b\nsk_c;sk_d"
        sys.modules.pop("config", None)
        config = importlib.import_module("config")

        self.assertEqual(config.ELEVENLABS_API_KEYS, ["sk_a", "sk_b", "sk_c", "sk_d"])


if __name__ == "__main__":
    unittest.main()
