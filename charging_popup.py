import sys
import psutil
import ctypes
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect
from PyQt5.QtGui import QMovie, QFont


def is_locked():
    """Check if Windows is locked using proper API"""
    try:
        # Check if workstation is locked
        user32 = ctypes.windll.User32
        # OpenInputDesktop returns NULL if desktop is locked
        hDesk = user32.OpenInputDesktop(0, False, 0)
        if hDesk == 0:
            return True
        user32.CloseDesktop(hDesk)
        return False
    except:
        return False


def format_time_left(secs):
    """Convert seconds to H:M format"""
    if secs == psutil.POWER_TIME_UNLIMITED or secs < 0:
        return "Estimating..."
    h, m = divmod(secs // 60, 60)
    if h > 0:
        return f"{h}h {m}m left"
    elif m > 0:
        return f"{m}m left"
    else:
        return "Almost done"


class ChargingPopup(QWidget):
    def __init__(self, battery_percent, time_left, position="right"):
        super().__init__()

        # Transparent window with proper flags
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool |
            Qt.WindowTransparentForInput  # Allow clicks to pass through
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)  # Auto cleanup

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Animation
        self.label_anim = QLabel(self)
        self.movie = QMovie("charging.gif")
        if not self.movie.isValid():
            print("Warning: charging.gif not found or invalid")
        self.label_anim.setMovie(self.movie)
        self.movie.start()
        layout.addWidget(self.label_anim, alignment=Qt.AlignCenter)

        # Battery info text
        self.label_text = QLabel(self)
        self.label_text.setText(f"{battery_percent}% Charging • {time_left}")
        self.label_text.setFont(QFont("Segoe UI", 14, QFont.Bold))
        self.label_text.setStyleSheet("color: white; background: transparent;")
        self.label_text.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label_text)

        self.adjustSize()

        # Screen positioning
        screen = QApplication.desktop().availableGeometry()
        
        if position == "center":  # bottom-center (lockscreen)
            self.final_x = (screen.width() - self.width()) // 2
            self.final_y = screen.height() - self.height() - 100
        else:  # bottom-right (desktop)
            self.final_x = screen.width() - self.width() - 40
            self.final_y = screen.height() - self.height() - 80

        # Start off-screen (for slide-in animation)
        self.move(self.final_x, screen.height())

        # Slide-in animation
        self.anim = QPropertyAnimation(self, b"geometry")
        self.anim.setDuration(600)
        self.anim.setStartValue(QRect(self.final_x, screen.height(), self.width(), self.height()))
        self.anim.setEndValue(QRect(self.final_x, self.final_y, self.width(), self.height()))
        self.anim.start()

        # Auto fade-out after 3 seconds
        QTimer.singleShot(3000, self.fade_out)

    def fade_out(self):
        """Fade out and close the popup"""
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(500)
        self.fade_anim.setStartValue(1.0)
        self.fade_anim.setEndValue(0.0)
        self.fade_anim.finished.connect(self.close)
        self.fade_anim.start()


class BatteryMonitor(QWidget):
    def __init__(self):
        super().__init__()
        
        # Hide the monitor widget (we only need it for the timer)
        self.hide()
        
        # Track charging state
        battery = psutil.sensors_battery()
        self.last_plugged = battery.power_plugged if battery else False
        
        # Setup timer to check battery status
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_battery)
        self.timer.start(2000)  # Check every 2 seconds
        
        # Keep track of active popup
        self.active_popup = None

    def check_battery(self):
        """Check battery status and show popup if just plugged in"""
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return
            
            current_plugged = battery.power_plugged
            
            # Charger just plugged in
            if current_plugged and not self.last_plugged:
                # Clean up old popup if exists
                if self.active_popup:
                    self.active_popup.close()
                
                # Get battery info
                percent = int(battery.percent)
                time_left = format_time_left(battery.secsleft)
                
                # Determine position based on lock state
                position = "center" if is_locked() else "right"
                
                # Show new popup
                self.active_popup = ChargingPopup(percent, time_left, position)
                self.active_popup.show()
            
            self.last_plugged = current_plugged
            
        except Exception as e:
            print(f"Error checking battery: {e}")


def main():
    app = QApplication(sys.argv)
    
    # Create battery monitor
    monitor = BatteryMonitor()
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
