from __future__ import annotations

import time
from time import perf_counter

from automation.proactive import ProactiveEngine
from brain.conversation import ConversationEngine
from config import BACKGROUND_MONITOR_ENABLED, KAIRO_TIMING, KAIRO_WARM_UP, PROACTIVE_ENABLED, USER_TITLE, WAKE_WORD_ACK, WAKE_WORD_REQUIRED
from core.logger import setup_logger
from core.voice_state import voice_state
from memory.session_memory import format_briefing_prefix, save_session_summary
from tools.background_monitor import check_all_monitors
from tools.system import SystemMonitor
from voice.speaker import Speaker
from voice.stt import SpeechRecognizer
from voice.wakeword import WakeWordDetector


class Kairo:
    def __init__(self) -> None:
        self.logger = setup_logger()
        self.conversation = ConversationEngine()
        self.speaker = Speaker()
        self.recognizer = SpeechRecognizer()
        self.system = SystemMonitor()
        self.wakeword = WakeWordDetector()
        self.proactive = ProactiveEngine()
        self.last_user_speech = time.monotonic()

    def ask(self, text: str) -> str:
        self.last_user_speech = time.monotonic()
        started_at = perf_counter()
        self.logger.info("User: %s", text)

        try:
            from ui import get_ui_bridge
            get_ui_bridge().update_speech_signal.emit(text, "", False)
        except Exception:
            pass

        # Explicit local vision requests. Background capture never uploads frames.
        lowered = text.lower()
        if any(v_kw in lowered for v_kw in ("screen", "camera", "look at", "what do you see", "what is on my screen", "read screen")):
            ack_msg = f"Looking at your {'camera' if 'camera' in lowered else 'screen'} now, {USER_TITLE}..."
            print(f"Kairo: {ack_msg}")
            try:
                from ui import get_ui_bridge
                get_ui_bridge().update_speech_signal.emit(text, ack_msg, True)
            except Exception:
                pass
            self.speaker.say(ack_msg)

            try:
                from vision.vision_agent import VisionAgent
                va = VisionAgent()
                v_res = va.describe_screen_and_cam() if ("camera" in lowered or "cam" in lowered or "see me" in lowered or "both" in lowered) else va.answer_screen_question(text)
                if v_res:
                    self.logger.info("Kairo (Local Vision): %s", v_res)
                    print(f"Kairo (Local Vision): {v_res}")
                    try:
                        from ui import get_ui_bridge
                        get_ui_bridge().update_speech_signal.emit(text, v_res, True)
                    except Exception:
                        pass
                    self.speaker.say(v_res)
                    return v_res
            except Exception as exc:
                print(f"[Vision Engine Note] {exc}")

        answer = self.conversation.reply(text)

        try:
            from ui import get_ui_bridge
            get_ui_bridge().update_speech_signal.emit(text, answer, True)
        except Exception:
            pass

        if answer.startswith("[SILENT]"):
            clean_answer = answer.replace("[SILENT]", "").strip()
            self.logger.info("Kairo (Silent): %s", clean_answer)
            print(f"Kairo: {clean_answer}")
            if KAIRO_TIMING:
                print("[timing] tts: skipped (silent automation)")
                print(f"[timing] total reply: {perf_counter() - started_at:.2f}s")
            return clean_answer

        self.logger.info("Kairo: %s", answer)
        tts_started = perf_counter()
        self.speaker.say(answer, mood=self._speech_mood(text, answer))
        if KAIRO_TIMING:
            print(f"[timing] tts: {perf_counter() - tts_started:.2f}s")
            print(f"[timing] total reply: {perf_counter() - started_at:.2f}s")
        return answer

    @staticmethod
    def _speech_mood(user_text: str, answer: str = "") -> str | None:
        """Select a safe, audible delivery cue from the conversation text."""
        lowered = f"{user_text} {answer}".lower()
        if any(word in lowered for word in ("joke", "funny", "make me laugh", "humour", "humor", "haha", "hahaha")):
            return "playful"
        if any(word in lowered for word in ("sad", "upset", "heartbroken", "loss", "passed away", "condolence", "sorry", "grief")):
            return "sad"
        if any(word in lowered for word in ("congratulate", "celebrate", "great news", "excited", "amazing", "wonderful")):
            return "happy"
        return None

    def run_voice(self) -> None:
        try:
            from ui import get_ui_bridge
            get_ui_bridge().splash_progress_signal.emit("Connecting Kairo's cloud fast lane...", 35)
        except Exception:
            pass

        if KAIRO_WARM_UP:
            warm_started = perf_counter()
            self.conversation.warm_up()
            if KAIRO_TIMING:
                print(f"[timing] startup warmup: {perf_counter() - warm_started:.2f}s")

        try:
            from ui import get_ui_bridge
            get_ui_bridge().splash_progress_signal.emit("Initializing voice & camera perception...", 70)
        except Exception:
            pass

        # Session memory morning briefing & Spoken Greeting
        briefing = format_briefing_prefix()
        greeting_text = f"{briefing} {self.system.greeting()}".strip()

        try:
            from ui import get_ui_bridge
            get_ui_bridge().splash_progress_signal.emit("KAIRO Online!", 100)
            get_ui_bridge().splash_finished_signal.emit()
        except Exception:
            pass

        self.speaker.say(greeting_text)

        # Check background topic monitors
        if BACKGROUND_MONITOR_ENABLED:
            alerts = check_all_monitors()
            for alert in alerts:
                print(f"Kairo Monitor Alert: {alert}")
                self.speaker.say(alert)

        while True:
            try:
                if not voice_state.is_enabled():
                    time.sleep(0.2)
                    continue

                if WAKE_WORD_REQUIRED:
                    _, command = self.wakeword.wait_for_wakeword(self.recognizer)
                    self.speaker.say(WAKE_WORD_ACK)
                    if not command:
                        text = self.recognizer.listen_once()
                    else:
                        text = command
                else:
                    text = self.recognizer.listen_once()

                if not text:
                    # Check proactive trigger on idle silence or camera person detection
                    if PROACTIVE_ENABLED and self.proactive.should_trigger(self.last_user_speech):
                        self.proactive.mark_triggered()
                        p_msg = self.proactive.build_prompt()
                        if p_msg:
                            print(f"Kairo (Proactive): {p_msg}")
                            self.speaker.say(p_msg)
                            try:
                                from ui import get_ui_bridge
                                get_ui_bridge().update_speech_signal.emit("", p_msg, True)
                            except Exception:
                                pass
                    continue

                if text.lower() in {"exit", "quit", "bye", "stop listening"}:
                    save_session_summary("User ended conversation session gracefully.")
                    self.speaker.say(f"Standing by, {USER_TITLE}.")
                    break

                self.ask(text)
            except KeyboardInterrupt:
                save_session_summary("Session ended via keyboard interrupt.")
                print()
                break
            except Exception as exc:
                self.logger.exception("Voice loop error")
                print(f"Kairo: Voice loop problem: {exc}")
