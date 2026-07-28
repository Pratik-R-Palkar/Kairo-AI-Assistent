from __future__ import annotations

import sys
import threading
from PyQt6.QtWidgets import QApplication

from core.kairo import Kairo
from tools.clean_storage import start_10min_autocleaner
from ui import KairoSplashScreen, KairoUI, get_ui_bridge


def run_voice_loop() -> None:
    try:
        kairo = Kairo()
        kairo.run_voice()
    except Exception as exc:
        print(f"[KAIRO Voice Engine] Note: {exc}")


def main() -> None:
    # 1. Start 10-Minute Auto-Cleaner Thread
    start_10min_autocleaner()

    app = QApplication.instance() or QApplication(sys.argv)

    # 2. Show Loading Splash Screen with Golden Arc Reactor
    splash = KairoSplashScreen()
    splash.show()

    main_window = None

    def on_kairo_ready() -> None:
        nonlocal main_window
        splash.close()
        main_window = KairoUI()
        main_window.showFullScreen()

    get_ui_bridge().splash_finished_signal.connect(on_kairo_ready)

    # 3. Launch KAIRO Voice Engine in Background Worker Thread
    voice_thread = threading.Thread(target=run_voice_loop, daemon=True)
    voice_thread.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
