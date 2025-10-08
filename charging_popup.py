import sys
import psutil
import ctypes
import time
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui import QMovie, QFont

# Check if Windows is locked
def is_locked():
    user32 = ctypes.windll.user32
    return user32.GetForegroundWindow() == 0

# Convert seconds to H:M format
def format_time_left(secs):
    if secs == psutil.POWER_TIME_UNLIMITED or secs < 0:
        return "estimating..."
    h, m = divmod(secs // 60, 60)
    if h > 0:
        return f"{h}h {m}m left"
    else:
        return f"{m}m left"

class ChargingPopup(QWidget):
    def __init__(self, battery_percent, time_left, position="right"):
        super().__init__()

        # Transparent window
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        # Layout
        layout = QVBoxLayout(self)

        # Animation
        self.label_anim = QLabel(self)
        self.movie = QMovie("charging.gif")  # <-- your charging GIF here
        self.label_anim.setMovie(self.movie)
        self.movie.start()
        layout.addWidget(self.label_anim, alignment=Qt.AlignCenter)

        # Battery info text
        self.label_text = QLabel(self)
        self.label_text.setText(f"{battery_percent}% Charging • {time_left}")
        self.label_text.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.label_text.setStyleSheet("color: white;")
        layout.addWidget(self.label_text, alignment=Qt.AlignCenter)

        self.adjustSize()

        # Screen positioning
        screen = QApplication.desktop().screenGeometry()
        if position == "right":  # bottom-right corner
            self.final_x = screen.width() - self.width() - 30
            self.final_y = screen.height() - self.height() - 60
        elif position == "center":  # bottom-center
            self.final_x = (screen.width() - self.width()) // 2
            self.final_y = screen.height() - self.height() - 60

        # Start off-screen (for slide-in animation)
        self.move(self.final_x, screen.height())

        # Slide-in animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(500)
        self.anim.setStartValue(QRect(self.final_x, screen.height(), self.width(), self.height()))
        self.anim.setEndValue(QRect(self.final_x, self.final_y, self.width(), self.height()))
        self.anim.start()

        # Fade-out after 3 sec
        self.fade_timer = QTimer(self)
        self.fade_timer.timeout.connect(self.fade_out)
        self.fade_timer.start(2500)  # start fading after 2.5 sec

    def fade_out(self):
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(500)
        self.fade_anim.setStartValue(1)
        self.fade_anim.setEndValue(0)
        self.fade_anim.finished.connect(self.close)
        self.fade_anim.start()
        self.fade_timer.stop()

def main():
    app = QApplication(sys.argv)

    last_state = psutil.sensors_battery().power_plugged

    while True:
        battery = psutil.sensors_battery()
        if battery.power_plugged and not last_state:
            # Charger just plugged in
            time_left = format_time_left(battery.secsleft)
            if is_locked():
                popup = ChargingPopup(battery_percent=int(battery.percent), time_left=time_left, position="center")
            else:
                popup = ChargingPopup(battery_percent=int(battery.percent), time_left=time_left, position="right")
            popup.show()
            app.processEvents()

        last_state = battery.power_plugged
        time.sleep(2)  # check every 2 sec

if __name__ == "__main__":
    main()

