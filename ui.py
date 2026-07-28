from __future__ import annotations

import math
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
    _PSUTIL = True
except ImportError:
    _PSUTIL = False

try:
    import numpy as np
    import sounddevice as sd
    _SOUNDDEVICE = True
except ImportError:
    _SOUNDDEVICE = False

try:
    import cv2
    _CV2 = True
except ImportError:
    _CV2 = False

from PyQt6.QtCore import QObject, QPointF, QRectF, QSize, QThread, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QFont,
    QIcon,
    QImage,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMainWindow,
    QProgressBar,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from core.voice_state import voice_state
from memory.task_storage import (
    add_persistent_task,
    load_tasks,
    remove_persistent_task,
    update_task_checked,
)

ASSETS_DIR = Path(__file__).resolve().parent / "assets"


class UIBridge(QObject):
    """Thread-safe signal bridge allowing KAIRO backend to control the UI from any thread."""
    add_task_signal = pyqtSignal(str, str)
    remove_task_signal = pyqtSignal(str)
    check_task_signal = pyqtSignal(str, bool)
    update_speech_signal = pyqtSignal(str, str, bool)
    splash_progress_signal = pyqtSignal(str, int)
    splash_finished_signal = pyqtSignal()


_UI_BRIDGE = UIBridge()
_UI_INSTANCE: KairoUI | None = None
_SPLASH_INSTANCE: KairoSplashScreen | None = None


def get_ui_bridge() -> UIBridge:
    return _UI_BRIDGE


class AudioMicMonitorThread(QThread):
    """Real-time microphone listener updating mic_amplitude for the voice waves."""
    amplitude_signal = pyqtSignal(float)

    def run(self) -> None:
        if not _SOUNDDEVICE:
            return

        def audio_callback(indata, frames, time_info, status):
            try:
                rms = float(np.sqrt(np.mean(indata**2)))
                amp = min(1.0, max(0.0, rms * 18.0))
                self.amplitude_signal.emit(amp)
            except Exception:
                pass

        try:
            with sd.InputStream(channels=1, samplerate=16000, callback=audio_callback, blocksize=512):
                while not self.isInterruptionRequested():
                    self.msleep(20)
        except Exception:
            pass


class CameraPreviewThread(QThread):
    """Captures live webcam feed and emits QPixmap frames to the GUI."""
    frame_signal = pyqtSignal(QPixmap)

    def run(self) -> None:
        if not _CV2:
            return
        try:
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap = cv2.VideoCapture(0)

            while not self.isInterruptionRequested():
                if cap.isOpened():
                    ret, frame = cap.read()
                    if ret and frame is not None:
                        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        h, w, ch = rgb.shape
                        qimg = QImage(rgb.data, w, h, ch * w, QImage.Format.Format_RGB888)
                        pix = QPixmap.fromImage(qimg)
                        self.frame_signal.emit(pix)
                self.msleep(33)

            cap.release()
        except Exception:
            pass


class GoldenRadarWidget(QWidget):
    """Golden Arc Reactor HUD Radar visualizer."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.angle_fast = 0.0
        self.angle_slow = 0.0
        self.pulse = 0.0
        self.pulse_dir = 0.02
        self.wave_phase = 0.0

        self.target_mic_amp = 0.0
        self.current_mic_amp = 0.0

        self.target_speaker_amp = 0.0
        self.current_speaker_amp = 0.0

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._animate)
        self.timer.start(16)

    def set_mic_amplitude(self, amp: float) -> None:
        self.target_mic_amp = amp

    def set_speaker_amplitude(self, amp: float) -> None:
        self.target_speaker_amp = amp

    def set_kairo_speaking(self, is_speaking: bool) -> None:
        self.target_speaker_amp = 1.0 if is_speaking else 0.0

    def _animate(self) -> None:
        rot_speed = 1.2 + (self.current_speaker_amp * 2.0)
        self.angle_fast = (self.angle_fast + rot_speed) % 360.0
        self.angle_slow = (self.angle_slow - 0.4) % 360.0
        self.wave_phase = (self.wave_phase + 0.08) % (math.pi * 4.0)

        self.current_mic_amp += (self.target_mic_amp - self.current_mic_amp) * 0.25
        self.current_speaker_amp += (self.target_speaker_amp - self.current_speaker_amp) * 0.20

        self.pulse += self.pulse_dir
        if self.pulse > 1.0 or self.pulse < 0.0:
            self.pulse_dir *= -1.0
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        width = self.width()
        height = self.height()

        cx = width / 2.0
        cy = height * 0.38 if height > 220 else height / 2.0
        max_r = min(width, height * 0.8) * 0.38

        grid_pen = QPen(QColor(245, 158, 11, 12), 1, Qt.PenStyle.DashLine)
        painter.setPen(grid_pen)

        d_len = max(width, height) * 0.7
        painter.drawLine(int(cx - d_len), int(cy - d_len), int(cx + d_len), int(cy + d_len))
        painter.drawLine(int(cx - d_len), int(cy + d_len), int(cx + d_len), int(cy - d_len))

        painter.setPen(QPen(QColor(245, 158, 11, 35), 1))
        painter.drawEllipse(QPointF(cx, cy), max_r, max_r)

        for r_factor in (0.82, 0.65, 0.48, 0.32):
            r = max_r * r_factor
            painter.setPen(QPen(QColor(245, 158, 11, int(25 + r_factor * 35)), 1))
            painter.drawEllipse(QPointF(cx, cy), r, r)

        painter.setPen(QPen(QColor(251, 191, 36, 200), 2))
        num_dots = 60
        for i in range(num_dots):
            a = math.radians(i * (360.0 / num_dots))
            tx = cx + (max_r * 0.98) * math.cos(a)
            ty = cy + (max_r * 0.98) * math.sin(a)
            painter.drawPoint(QPointF(tx, ty))

        rect_outer = QRectF(cx - max_r, cy - max_r, max_r * 2, max_r * 2)
        rect_mid = QRectF(cx - max_r * 0.72, cy - max_r * 0.72, max_r * 1.44, max_r * 1.44)

        arc_pen = QPen(QColor(251, 191, 36, 240))
        arc_pen.setWidth(4)
        arc_pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen)
        painter.drawArc(rect_outer, int(-self.angle_fast * 16), int(120 * 16))

        arc_pen_mid = QPen(QColor(245, 158, 11, 220))
        arc_pen_mid.setWidth(3)
        arc_pen_mid.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(arc_pen_mid)
        painter.drawArc(rect_mid, int((self.angle_slow + 180) * 16), int(80 * 16))

        kairo_speech_expansion = self.current_speaker_amp * 12.0
        core_r = max_r * 0.18 + (self.pulse * 3.0) + kairo_speech_expansion

        grad = QRadialGradient(cx, cy, core_r * 3.0)
        grad.setColorAt(0.0, QColor(255, 255, 255, 255))
        grad.setColorAt(0.25, QColor(251, 191, 36, int(240 + self.current_speaker_amp * 15)))
        grad.setColorAt(0.55, QColor(245, 158, 11, 150))
        grad.setColorAt(0.8, QColor(217, 119, 6, 50))
        grad.setColorAt(1.0, QColor(0, 0, 0, 0))

        painter.setBrush(QBrush(grad))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(QPointF(cx, cy), core_r * 3.0, core_r * 3.0)

        if height > 220:
            wave_base_y = height * 0.82
            wave_width = width * 0.85
            wave_start_x = (width - wave_width) / 2.0

            amp_scale = 6.0 + (self.current_mic_amp * 50.0)

            for wave_idx, (color, width_pen, freq_mult, speed_shift) in enumerate([
                (QColor(217, 119, 6, 90), 1.5, 1.0, 0.0),
                (QColor(245, 158, 11, 160), 2.5, 1.5, math.pi * 0.5),
                (QColor(251, 191, 36, 230), 3.5, 2.0, math.pi),
            ]):
                path = QPainterPath()
                first = True

                for x_pos in range(int(wave_start_x), int(wave_start_x + wave_width), 3):
                    norm_x = (x_pos - wave_start_x) / wave_width
                    envelope = math.sin(norm_x * math.pi)
                    rad = norm_x * math.pi * 6.0 * freq_mult + self.wave_phase + speed_shift
                    y_val = wave_base_y + math.sin(rad) * amp_scale * envelope

                    if first:
                        path.moveTo(x_pos, y_val)
                        first = False
                    else:
                        path.lineTo(x_pos, y_val)

                pen = QPen(color, width_pen)
                pen.setCapStyle(Qt.PenCapStyle.RoundCap)
                painter.setPen(pen)
                painter.drawPath(path)


class KairoSplashScreen(QWidget):
    """Frameless Loading Screen showing spinning Arc Reactor HUD until KAIRO starts speaking."""

    def __init__(self) -> None:
        super().__init__()
        global _SPLASH_INSTANCE
        _SPLASH_INSTANCE = self

        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.SplashScreen)
        self.setFixedSize(540, 410)

        # Center on Primary Screen
        screen_geo = QApplication.primaryScreen().geometry()
        self.move((screen_geo.width() - 540) // 2, (screen_geo.height() - 410) // 2)

        self.setStyleSheet("""
            QWidget {
                background-color: #08080d;
                border: 2px solid #f59e0b;
                border-radius: 16px;
                color: #e2e8f0;
                font-family: 'Consolas', 'Segoe UI', monospace;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 28)
        layout.setSpacing(14)

        # Golden Arc Reactor Widget
        self.radar = GoldenRadarWidget()
        self.radar.setFixedSize(220, 190)
        layout.addWidget(self.radar, alignment=Qt.AlignmentFlag.AlignCenter)

        # Title
        title = QLabel("K A I R O")
        title.setStyleSheet("color: #ffffff; font-size: 28px; font-weight: 900; letter-spacing: 6px; border: none;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Status Label
        self.status_lbl = QLabel("INITIALIZING NEURAL SYSTEM CORE...")
        self.status_lbl.setStyleSheet("color: #f59e0b; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; border: none;")
        self.status_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_lbl)

        # Loading Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(10)
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #1a1714;
                border: none;
                border-radius: 4px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #fbbf24);
                border-radius: 4px;
            }
        """)
        layout.addWidget(self.progress_bar)

        _UI_BRIDGE.splash_progress_signal.connect(self.update_progress)
        _UI_BRIDGE.splash_finished_signal.connect(self.close_splash)

    def update_progress(self, text: str, percent: int) -> None:
        self.status_lbl.setText(text.upper())
        self.progress_bar.setValue(percent)

    def close_splash(self) -> None:
        self.close()


class KairoUI(QMainWindow):
    """Main KAIRO UI Dashboard."""

    def __init__(self) -> None:
        super().__init__()
        global _UI_INSTANCE
        _UI_INSTANCE = self

        self.setWindowTitle("KAIRO — Cloud AI Assistant")
        self.resize(1340, 820)
        self.setMinimumSize(1100, 680)

        self.mic_thread: AudioMicMonitorThread | None = None
        self.cam_thread: CameraPreviewThread | None = None
        self.task_widget_map: dict[str, QFrame] = {}
        self.checkbox_map: dict[str, QCheckBox] = {}

        self._init_theme()
        self._init_layout()
        self._init_clock_timer()
        self._init_mic_monitor()
        self._init_cam_monitor()
        self._connect_bridge()
        self._load_saved_tasks()
        self._maybe_show_api_setup()

    def _connect_bridge(self) -> None:
        _UI_BRIDGE.add_task_signal.connect(self._add_task_from_user)
        _UI_BRIDGE.remove_task_signal.connect(self._remove_task)
        _UI_BRIDGE.check_task_signal.connect(self._set_task_checked)
        _UI_BRIDGE.update_speech_signal.connect(self.update_speech_status)

    def _init_theme(self) -> None:
        self.setStyleSheet("""
            QMainWindow {
                background-color: #050505;
            }
            QWidget {
                color: #e2e8f0;
                font-family: 'Consolas', 'Segoe UI', 'Inter', monospace;
            }
            QFrame.card {
                background-color: #09090d;
                border: 1px solid #16161f;
                border-radius: 12px;
            }
            QLabel.section-title {
                color: #f59e0b;
                font-size: 12px;
                font-weight: 800;
                letter-spacing: 1px;
            }
            QProgressBar {
                background-color: #1a1714;
                border: none;
                border-radius: 5px;
                height: 10px;
                text-fill: transparent;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #d97706, stop:1 #fbbf24);
                border-radius: 5px;
            }
            QPushButton.quick-btn {
                background-color: #0e0e14;
                border: 1px solid #1c1c26;
                border-radius: 8px;
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 500;
                padding: 10px 14px;
                text-align: left;
            }
            QPushButton.quick-btn:hover {
                background-color: #181822;
                border: 1px solid #f59e0b;
                color: #f59e0b;
            }
            QPushButton.add-btn {
                background-color: #1a1714;
                border: 1px solid #d97706;
                border-radius: 6px;
                color: #f59e0b;
                font-size: 11px;
                font-weight: bold;
                padding: 3px 8px;
            }
            QPushButton.add-btn:hover {
                background-color: #f59e0b;
                color: #000000;
            }
            QPushButton.remove-task-btn {
                background-color: transparent;
                border: none;
                color: #64748b;
                font-size: 13px;
                font-weight: bold;
                padding: 2px 6px;
            }
            QPushButton.remove-task-btn:hover {
                color: #ef4444;
            }
            QCheckBox {
                color: #cbd5e1;
                font-size: 12px;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #332b1d;
                border-radius: 4px;
                background-color: #0d0d14;
            }
            QCheckBox::indicator:hover {
                border: 1px solid #f59e0b;
            }
            QCheckBox::indicator:checked {
                background-color: #f59e0b;
                border: 1px solid #fbbf24;
            }
        """)

    def _init_layout(self) -> None:
        main_widget = QWidget()
        main_layout = QHBoxLayout(main_widget)
        main_layout.setContentsMargins(18, 18, 18, 18)
        main_layout.setSpacing(18)

        # ---------------------------------------------------------------------
        # 1. LEFT COLUMN (~240px)
        # ---------------------------------------------------------------------
        left_col = QVBoxLayout()
        left_col.setSpacing(14)

        clock_card = QFrame()
        clock_card.setFixedWidth(240)
        clock_card.setProperty("class", "card")
        clock_layout = QVBoxLayout(clock_card)
        clock_layout.setContentsMargins(16, 14, 16, 14)
        clock_layout.setSpacing(2)

        clock_row = QHBoxLayout()
        clock_row.setSpacing(6)
        self.time_digits_lbl = QLabel("04:08")
        self.time_digits_lbl.setStyleSheet("color: #ffffff; font-size: 44px; font-weight: 800; font-family: 'Consolas', 'Segoe UI', monospace;")

        self.ampm_lbl = QLabel("PM")
        self.ampm_lbl.setStyleSheet("color: #f59e0b; font-size: 18px; font-weight: 800; font-family: 'Consolas', 'Segoe UI', monospace; margin-top: 12px;")

        clock_row.addWidget(self.time_digits_lbl)
        clock_row.addWidget(self.ampm_lbl)
        clock_row.addStretch()
        clock_layout.addLayout(clock_row)

        now = datetime.now()
        self.day_lbl = QLabel(now.strftime("%A").upper())
        self.day_lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 800; letter-spacing: 2px;")
        self.date_lbl = QLabel(now.strftime("%B %d, %Y").upper())
        self.date_lbl.setStyleSheet("color: #f59e0b; font-size: 14px; font-weight: 800; letter-spacing: 2px;")

        clock_layout.addWidget(self.day_lbl)
        clock_layout.addWidget(self.date_lbl)

        accent_line = QFrame()
        accent_line.setFixedSize(42, 3)
        accent_line.setStyleSheet("background-color: #d97706; border: none; margin-top: 6px;")
        clock_layout.addWidget(accent_line)

        left_col.addWidget(clock_card)

        weather_card = QFrame()
        weather_card.setFixedWidth(240)
        weather_card.setProperty("class", "card")
        wc_layout = QVBoxLayout(weather_card)
        wc_layout.setContentsMargins(16, 14, 16, 14)
        wc_layout.setSpacing(4)

        w_img = QLabel()
        w_pixmap = QPixmap(str(ASSETS_DIR / "weather.png"))
        if not w_pixmap.isNull():
            w_img.setPixmap(w_pixmap.scaled(44, 44, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            w_img.setText("[Weather]")
            w_img.setStyleSheet("color: #f59e0b;")
        wc_layout.addWidget(w_img, alignment=Qt.AlignmentFlag.AlignCenter)

        w_temp = QLabel("28°C")
        w_temp.setStyleSheet("color: #ffffff; font-size: 30px; font-weight: 800;")
        w_temp.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wc_layout.addWidget(w_temp)

        w_desc = QLabel("MOSTLY CLOUDY")
        w_desc.setStyleSheet("color: #f59e0b; font-size: 10px; font-weight: 800; letter-spacing: 1px;")
        w_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wc_layout.addWidget(w_desc)

        wc_layout.addSpacing(4)

        w_sub = QLabel("Humidity: 61%  |  Wind: 12 km/h")
        w_sub.setStyleSheet("color: #8e8e93; font-size: 10px;")
        w_sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        wc_layout.addWidget(w_sub)

        left_col.addWidget(weather_card)

        # CHECKLIST CARD
        chk_card = QFrame()
        chk_card.setFixedWidth(240)
        chk_card.setProperty("class", "card")
        self.chk_layout = QVBoxLayout(chk_card)
        self.chk_layout.setContentsMargins(16, 14, 16, 14)
        self.chk_layout.setSpacing(10)

        chk_title = QLabel("CHECKLIST")
        chk_title.setProperty("class", "section-title")
        self.chk_layout.addWidget(chk_title)

        self.chk_layout.addStretch()
        left_col.addWidget(chk_card, stretch=1)

        # SQUARE CAMERA PREVIEW CARD (Under Checklist)
        cam_card = QFrame()
        cam_card.setFixedWidth(240)
        cam_card.setFixedHeight(210)
        cam_card.setProperty("class", "card")
        cam_layout = QVBoxLayout(cam_card)
        cam_layout.setContentsMargins(14, 12, 14, 12)
        cam_layout.setSpacing(8)

        cam_hdr = QHBoxLayout()
        cam_title = QLabel("CAMERA FEED")
        cam_title.setProperty("class", "section-title")
        cam_status = QLabel("● LIVE")
        cam_status.setStyleSheet("color: #22c55e; font-size: 10px; font-weight: bold;")

        cam_hdr.addWidget(cam_title)
        cam_hdr.addStretch()
        cam_hdr.addWidget(cam_status)
        cam_layout.addLayout(cam_hdr)

        self.cam_feed_lbl = QLabel()
        self.cam_feed_lbl.setFixedSize(212, 150)
        self.cam_feed_lbl.setStyleSheet("""
            background-color: #06060a;
            border: 1px solid #221d14;
            border-radius: 8px;
            color: #f59e0b;
            font-size: 11px;
        """)
        self.cam_feed_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.cam_feed_lbl.setText("[ CAMERA STANDBY ]")

        cam_layout.addWidget(self.cam_feed_lbl, alignment=Qt.AlignmentFlag.AlignCenter)
        left_col.addWidget(cam_card)

        main_layout.addLayout(left_col)

        # ---------------------------------------------------------------------
        # 2. CENTER COLUMN
        # ---------------------------------------------------------------------
        center_col = QVBoxLayout()
        center_col.setContentsMargins(0, 0, 0, 0)
        center_col.setSpacing(14)

        self.radar = GoldenRadarWidget()
        center_col.addWidget(self.radar, stretch=1)

        bottom_card = QFrame()
        bottom_card.setProperty("class", "card")
        bottom_card.setStyleSheet("background-color: #08080c; border: 1px solid #16161f; border-radius: 10px;")
        bc_layout = QVBoxLayout(bottom_card)
        bc_layout.setContentsMargins(18, 12, 18, 12)
        bc_layout.setSpacing(6)

        u_row = QHBoxLayout()
        u_tag = QLabel("YOU:")
        u_tag.setStyleSheet("color: #f59e0b; font-weight: 800; font-size: 12px; min-width: 60px;")
        self.user_speech_lbl = QLabel("Tap the mic and ask anything...")
        self.user_speech_lbl.setStyleSheet("color: #64748b; font-size: 13px; font-style: italic;")
        self.u_time_lbl = QLabel(datetime.now().strftime("%I:%M %p"))
        self.u_time_lbl.setStyleSheet("color: #6b7280; font-size: 11px;")

        u_row.addWidget(u_tag)
        u_row.addWidget(self.user_speech_lbl, stretch=1)
        u_row.addWidget(self.u_time_lbl)
        bc_layout.addLayout(u_row)

        k_row = QHBoxLayout()
        k_tag = QLabel("KAIRO:")
        k_tag.setStyleSheet("color: #f59e0b; font-weight: 800; font-size: 12px; min-width: 60px;")
        self.kairo_speech_lbl = QLabel("Listening for voice commands...")
        self.kairo_speech_lbl.setStyleSheet("color: #d1d5db; font-size: 13px;")
        self.k_time_lbl = QLabel(datetime.now().strftime("%I:%M %p"))
        self.k_time_lbl.setStyleSheet("color: #6b7280; font-size: 11px;")

        k_row.addWidget(k_tag)
        k_row.addWidget(self.kairo_speech_lbl, stretch=1)
        k_row.addWidget(self.k_time_lbl)
        bc_layout.addLayout(k_row)

        center_col.addWidget(bottom_card)

        main_layout.addLayout(center_col, stretch=1)

        # ---------------------------------------------------------------------
        # 3. RIGHT SIDEBAR (~300px Width)
        # ---------------------------------------------------------------------
        right_card = QFrame()
        right_card.setProperty("class", "card")
        right_layout = QVBoxLayout(right_card)
        right_layout.setContentsMargins(18, 18, 18, 18)
        right_layout.setSpacing(18)

        sys_hdr = QHBoxLayout()
        sys_hdr.setSpacing(8)
        sys_icon = QLabel("⚡")
        sys_icon.setStyleSheet("color: #f59e0b; font-size: 13px;")
        sys_title = QLabel("SYSTEM STATUS")
        sys_title.setProperty("class", "section-title")
        sys_hdr.addWidget(sys_icon)
        sys_hdr.addWidget(sys_title)
        sys_hdr.addStretch()
        right_layout.addLayout(sys_hdr)

        self.cpu_bar, self.cpu_lbl = self._create_metric_row("CPU", right_layout)
        self.ram_bar, self.ram_lbl = self._create_metric_row("RAM", right_layout)
        self.gpu_bar, self.gpu_lbl = self._create_metric_row("GPU", right_layout)
        self.bat_bar, self.bat_lbl = self._create_metric_row("BATTERY", right_layout)

        right_layout.addSpacing(4)

        qa_hdr = QHBoxLayout()
        qa_hdr.setSpacing(8)
        qa_icon = QLabel("⊞")
        qa_icon.setStyleSheet("color: #f59e0b; font-size: 14px;")
        qa_title = QLabel("QUICK ACCESS")
        qa_title.setProperty("class", "section-title")
        qa_hdr.addWidget(qa_icon)
        qa_hdr.addWidget(qa_title)
        qa_hdr.addStretch()
        right_layout.addLayout(qa_hdr)

        qa_grid = QVBoxLayout()
        qa_grid.setSpacing(8)

        apps = [
            ("vscode.png", "VS Code", "code"),
            ("github.png", "GitHub", "https://github.com"),
            ("spotify.png", "Spotify", "spotify"),
            ("notion.png", "Notion", "https://notion.so"),
        ]
        for icon_file, name, target in apps:
            btn = QPushButton(f"  {name}")
            btn.setProperty("class", "quick-btn")
            pix = QPixmap(str(ASSETS_DIR / icon_file))
            if not pix.isNull():
                btn.setIcon(QIcon(pix))
                btn.setIconSize(QSize(18, 18))
            btn.clicked.connect(lambda _, t=target: self._launch_quick(t))
            qa_grid.addWidget(btn)

        right_layout.addLayout(qa_grid)
        right_layout.addSpacing(4)

        tr_hdr = QHBoxLayout()
        tr_hdr.setSpacing(8)
        tr_icon = QLabel("📅")
        tr_icon.setStyleSheet("color: #f59e0b; font-size: 13px;")
        tr_title = QLabel("TASKS & REMINDERS")
        tr_title.setProperty("class", "section-title")
        tr_hdr.addWidget(tr_icon)
        tr_hdr.addWidget(tr_title)
        tr_hdr.addStretch()

        add_task_btn = QPushButton("+ Add")
        add_task_btn.setProperty("class", "add-btn")
        add_task_btn.clicked.connect(self._prompt_add_task)
        tr_hdr.addWidget(add_task_btn)

        right_layout.addLayout(tr_hdr)

        self.tasks_container = QVBoxLayout()
        self.tasks_container.setSpacing(8)
        right_layout.addLayout(self.tasks_container)

        self.mic_toggle_btn = QPushButton("🎤 MIC ON")
        self.mic_toggle_btn.setProperty("class", "quick-btn")
        self.mic_toggle_btn.clicked.connect(self._toggle_mic)
        self.mic_toggle_btn.setStyleSheet(
            "QPushButton {background-color: #132218; border: 1px solid #22c55e; color: #86efac; font-weight: 700;}"
            "QPushButton:hover {background-color: #1f3a29; border: 1px solid #4ade80;}"
        )
        right_layout.addWidget(self.mic_toggle_btn)

        self.api_mode_btn = QPushButton("⚙ API / MODE")
        self.api_mode_btn.setProperty("class", "quick-btn")
        self.api_mode_btn.clicked.connect(self._show_api_setup_dialog)
        self.api_mode_btn.setStyleSheet(
            "QPushButton {background-color: #10101d; border: 1px solid #334155; color: #cbd5e1; font-weight: 700;}"
            "QPushButton:hover {background-color: #171c2c; border: 1px solid #f59e0b;}"
        )
        right_layout.addWidget(self.api_mode_btn)

        right_layout.addStretch()
        main_layout.addWidget(right_card)

        self.setCentralWidget(main_widget)

        self._build_footer_credit()

    def _build_footer_credit(self) -> None:
        self.statusBar().setStyleSheet("background-color: #050505; color: #8e8e93; border-top: 1px solid #16161f;")
        self.statusBar().showMessage("Local-first assistant • Secure by default")

    def _maybe_show_api_setup(self) -> None:
        try:
            from brain.llm import LocalLLMRouter
            router = LocalLLMRouter()
            if not router.available() and not router._internet_available():
                self._show_api_setup_dialog()
        except Exception:
            pass

    def _show_api_setup_dialog(self) -> None:
        dialog = QDialog(self)
        dialog.setWindowTitle("KAIRO AI Mode")
        dialog.resize(520, 280)
        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Choose how KAIRO should respond when you talk to it:"))
        layout.addSpacing(8)

        self.cloud_mode_btn = QRadioButton("Cloud AI mode — uses internet APIs whenever the connection is available")
        self.local_mode_btn = QRadioButton("Local AI mode — uses installed local models when offline or private")
        self.cloud_mode_btn.setChecked(True)
        layout.addWidget(self.cloud_mode_btn)
        layout.addWidget(self.local_mode_btn)
        layout.addSpacing(8)
        layout.addWidget(QLabel("Tip: if internet is unavailable, KAIRO will automatically fall back to local models. You can also switch to local mode manually for privacy."))
        layout.addStretch()

        buttons = QHBoxLayout()
        ok_btn = QPushButton("Save")
        ok_btn.clicked.connect(lambda: self._save_ai_mode(dialog))
        buttons.addStretch()
        buttons.addWidget(ok_btn)
        layout.addLayout(buttons)
        dialog.exec()

    def _save_ai_mode(self, dialog: QDialog) -> None:
        try:
            from brain.llm import LocalLLMRouter
            router = LocalLLMRouter()
            router.mode = "cloud" if self.cloud_mode_btn.isChecked() else "local"
            dialog.accept()
        except Exception:
            dialog.reject()

    def _toggle_mic(self) -> None:
        enabled = voice_state.set_enabled(not voice_state.is_enabled())
        self.mic_toggle_btn.setText("🎤 MIC ON" if enabled else "🎤 MIC OFF")
        self.mic_toggle_btn.setStyleSheet(
            "QPushButton {background-color: #132218; border: 1px solid #22c55e; color: #86efac; font-weight: 700;}"
            "QPushButton:hover {background-color: #1f3a29; border: 1px solid #4ade80;}"
            if enabled else
            "QPushButton {background-color: #22161c; border: 1px solid #ef4444; color: #fda4af; font-weight: 700;}"
            "QPushButton:hover {background-color: #311b22; border: 1px solid #fb7185;}"
        )
        if enabled:
            self.update_speech_status("Microphone enabled", "Ready for voice input")
        else:
            self.update_speech_status("Microphone disabled", "Voice input paused")

    def _init_cam_monitor(self) -> None:
        self.cam_thread = CameraPreviewThread()
        self.cam_thread.frame_signal.connect(self._update_cam_frame)
        self.cam_thread.start()

    def _update_cam_frame(self, pixmap: QPixmap) -> None:
        scaled = pixmap.scaled(
            212,
            150,
            Qt.AspectRatioMode.KeepAspectRatioByExpanding,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.cam_feed_lbl.setPixmap(scaled)

    def _load_saved_tasks(self) -> None:
        saved_tasks = load_tasks()
        for task in saved_tasks:
            title = str(task.get("title", ""))
            time_str = str(task.get("time_str", "Today • 10:00 AM"))
            checked = bool(task.get("checked", False))
            self._render_task_ui(title, time_str, is_checked=checked)

    def _add_task_from_user(self, title_text: str, time_text: str) -> None:
        add_persistent_task(title_text, time_text)
        self._render_task_ui(title_text, time_text, is_checked=False)

    def _render_task_ui(self, title_text: str, time_text: str, is_checked: bool = False) -> None:
        if title_text in self.task_widget_map:
            return

        cb = QCheckBox(title_text)
        cb.setChecked(is_checked)
        cb.toggled.connect(lambda checked, t=title_text, c=cb: self._on_task_checked(t, checked, c))
        self.chk_layout.insertWidget(self.chk_layout.count() - 1, cb)
        self.checkbox_map[title_text] = cb

        task_box = QFrame()
        task_box.setStyleSheet("background-color: #101016; border: 1px solid #1a1a24; border-radius: 8px;")
        tb_outer = QHBoxLayout(task_box)
        tb_outer.setContentsMargins(12, 10, 10, 10)

        tb_lay = QVBoxLayout()
        tb_lay.setSpacing(3)

        t_title = QLabel(title_text)
        t_title.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 600;")
        t_time = QLabel(f"• {time_text}")
        t_time.setStyleSheet("color: #6b7280; font-size: 11px;")

        tb_lay.addWidget(t_title)
        tb_lay.addWidget(t_time)

        tb_outer.addLayout(tb_lay, stretch=1)

        remove_btn = QPushButton("✕")
        remove_btn.setProperty("class", "remove-task-btn")
        remove_btn.setToolTip("Remove Task")
        remove_btn.clicked.connect(lambda _, t=title_text: self._remove_task(t))
        tb_outer.addWidget(remove_btn)

        self.tasks_container.addWidget(task_box)
        self.task_widget_map[title_text] = task_box

        if is_checked:
            task_box.hide()
            cb.setStyleSheet("color: #64748b; text-decoration: line-through;")

    def _remove_task(self, task_name: str) -> None:
        remove_persistent_task(task_name)

        match_key = None
        for key in list(self.task_widget_map.keys()):
            if key.lower().strip() == task_name.lower().strip():
                match_key = key
                break

        target = match_key or task_name

        if target in self.task_widget_map:
            widget = self.task_widget_map.pop(target)
            widget.deleteLater()
        if target in self.checkbox_map:
            cb = self.checkbox_map.pop(target)
            cb.deleteLater()

    def _set_task_checked(self, task_name: str, is_checked: bool) -> None:
        for key, cb in list(self.checkbox_map.items()):
            if key.lower().strip() == task_name.lower().strip():
                cb.setChecked(is_checked)
                break

    def _prompt_add_task(self) -> None:
        text, ok = QInputDialog.getText(self, "Add Task & Reminder", "Enter task description:")
        if ok and text.strip():
            task_title = text.strip()
            time_str = f"Today • {datetime.now().strftime('%I:%M %p')}"
            self._add_task_from_user(task_title, time_str)

    def _on_task_checked(self, task_name: str, is_checked: bool, checkbox: QCheckBox) -> None:
        update_task_checked(task_name, is_checked)
        if task_name in self.task_widget_map:
            widget = self.task_widget_map[task_name]
            if is_checked:
                widget.hide()
                checkbox.setStyleSheet("color: #64748b; text-decoration: line-through;")
            else:
                widget.show()
                checkbox.setStyleSheet("color: #cbd5e1;")

    def _init_mic_monitor(self) -> None:
        self.mic_thread = AudioMicMonitorThread()
        self.mic_thread.amplitude_signal.connect(self.radar.set_mic_amplitude)
        self.mic_thread.start()

    def update_speech_status(self, user_text: str, kairo_response: str, is_kairo_speaking: bool = False) -> None:
        now_str = datetime.now().strftime("%I:%M %p")
        if user_text:
            self.user_speech_lbl.setText(user_text)
            self.user_speech_lbl.setStyleSheet("color: #d1d5db; font-size: 13px; font-style: normal;")
            self.u_time_lbl.setText(now_str)
        if kairo_response:
            self.kairo_speech_lbl.setText(kairo_response)
            self.k_time_lbl.setText(now_str)
        self.radar.set_kairo_speaking(is_kairo_speaking)

    def _create_metric_row(self, name: str, parent_layout: QVBoxLayout) -> tuple[QProgressBar, QLabel]:
        row = QHBoxLayout()
        lbl = QLabel(name)
        lbl.setStyleSheet("color: #d1d5db; font-size: 12px; font-weight: 600; min-width: 65px;")
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(25)

        val_lbl = QLabel("25%")
        val_lbl.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 600; min-width: 40px; text-align: right;")

        row.addWidget(lbl)
        row.addWidget(bar, stretch=1)
        row.addWidget(val_lbl)
        parent_layout.addLayout(row)
        return bar, val_lbl

    def _init_clock_timer(self) -> None:
        self.metrics_timer = QTimer(self)
        self.metrics_timer.timeout.connect(self._update_metrics)
        self.metrics_timer.start(1000)

    def _update_metrics(self) -> None:
        now = datetime.now()
        self.time_digits_lbl.setText(now.strftime("%I:%M"))
        self.ampm_lbl.setText(now.strftime("%p"))
        self.day_lbl.setText(now.strftime("%A").upper())
        self.date_lbl.setText(now.strftime("%B %d, %Y").upper())

        if _PSUTIL:
            cpu = int(psutil.cpu_percent())
            ram = int(psutil.virtual_memory().percent)
            self.cpu_bar.setValue(cpu)
            self.cpu_lbl.setText(f"{cpu}%")
            self.ram_bar.setValue(ram)
            self.ram_lbl.setText(f"{ram}%")

            bat = psutil.sensors_battery()
            if bat:
                b_val = int(bat.percent)
                self.bat_bar.setValue(b_val)
                self.bat_lbl.setText(f"{b_val}%")
            else:
                self.bat_bar.setValue(100)
                self.bat_lbl.setText("100%")

            self.gpu_bar.setValue(28)
            self.gpu_lbl.setText("28%")

    def _launch_quick(self, target: str) -> None:
        import subprocess, webbrowser
        if target.startswith("http"):
            webbrowser.open(target)
        else:
            try:
                subprocess.Popen(target, shell=True)
            except Exception:
                pass

    def closeEvent(self, event) -> None:
        if self.mic_thread:
            self.mic_thread.requestInterruption()
            self.mic_thread.wait(500)
        if self.cam_thread:
            self.cam_thread.requestInterruption()
            self.cam_thread.wait(500)
        event.accept()


def launch_ui() -> None:
    app = QApplication.instance() or QApplication(sys.argv)
    window = KairoUI()
    window.showFullScreen()
    sys.exit(app.exec())


if __name__ == "__main__":
    launch_ui()
