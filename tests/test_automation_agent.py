from __future__ import annotations

import unittest

from agents.automation_agent import AutomationAgent


class _Keyboard:
    def type_text(self, text: str, press_enter_after: bool = False) -> str:
        return f"typed:{text}:{press_enter_after}"


class _Mouse:
    def double_click(self, x: int, y: int) -> str:
        return f"double:{x},{y}"


class _Engine:
    def __init__(self) -> None:
        self.keyboard = _Keyboard()
        self.mouse = _Mouse()
        self.calls: list[tuple] = []

    def open_settings(self, page: str | None = None) -> str:
        self.calls.append(("settings", page))
        return f"settings:{page}"

    def power_action(self, action: str) -> str:
        self.calls.append(("power", action))
        return f"power:{action}"

    def hotkey(self, *keys: str) -> str:
        self.calls.append(("hotkey", *keys))
        return "hotkey"

    def press_key(self, key: str) -> str:
        self.calls.append(("key", key))
        return "key"

    def mouse_move(self, x: int, y: int) -> str:
        self.calls.append(("move", x, y))
        return "move"

    def mouse_click(self, x: int, y: int, button: str) -> str:
        self.calls.append(("click", x, y, button))
        return "click"


class TestAutomationAgent(unittest.TestCase):
    def setUp(self) -> None:
        self.engine = _Engine()
        self.agent = AutomationAgent(engine=self.engine)

    def test_settings_is_handled_before_generic_app_launch(self) -> None:
        self.assertEqual(self.agent.handle("open wifi settings"), "settings:wifi")
        self.assertEqual(self.engine.calls, [("settings", "wifi")])

    def test_power_action_needs_confirmation(self) -> None:
        self.assertEqual(self.agent.handle("restart my pc"), "Boss, say 'confirm' to restart.")
        self.assertEqual(self.agent.handle("confirm"), "power:restart")
        self.assertEqual(self.engine.calls, [("power", "restart")])

    def test_voice_shortcuts_and_pointer_coordinates(self) -> None:
        self.assertEqual(self.agent.handle("press ctrl+shift+t"), "[SILENT] hotkey")
        self.assertEqual(self.engine.calls[-1], ("hotkey", "ctrl", "shift", "t"))
        self.assertEqual(self.agent.handle("move cursor to 120, 400"), "[SILENT] move")
        self.assertEqual(self.engine.calls[-1], ("move", 120, 400))
        self.assertEqual(self.agent.handle("right click at 120 400"), "[SILENT] click")
        self.assertEqual(self.engine.calls[-1], ("click", 120, 400, "right"))


if __name__ == "__main__":
    unittest.main()
