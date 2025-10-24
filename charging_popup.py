import sys
import psutil
import ctypes
from PyQt5.QtWidgets import QApplication, QLabel, QWidget, QVBoxLayout, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer, QPropertyAnimation, QRect, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QPixmap, QIcon, QPainter, QColor, QBrush
import os
import time
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('charging_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


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


class AnimatedChargingWidget(QLabel):
    """Custom widget that creates a CSS-like charging animation"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_step = 0
        self.setFixedSize(80, 80)
        self.setStyleSheet("""
            QLabel {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    stop:0 rgba(255, 255, 255, 0.9),
                    stop:0.3 rgba(255, 255, 255, 0.7),
                    stop:0.6 rgba(255, 255, 255, 0.4),
                    stop:1 rgba(255, 255, 255, 0.1));
                border-radius: 40px;
                border: 3px solid rgba(255, 255, 255, 0.8);
            }
        """)
        
    def start_animation(self):
        """Start the charging animation"""
        self.animation_timer.start(100)  # Update every 100ms
        
    def stop_animation(self):
        """Stop the charging animation"""
        self.animation_timer.stop()
        
    def update_animation(self):
        """Update the animation frame"""
        self.animation_step = (self.animation_step + 1) % 20
        
        # Create pulsing effect
        intensity = 0.3 + 0.7 * (1 + (self.animation_step % 10) / 10)
        opacity = 0.4 + 0.6 * (1 + (self.animation_step % 15) / 15)
        
        self.setStyleSheet(f"""
            QLabel {{
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    stop:0 rgba(255, 255, 255, {opacity}),
                    stop:0.3 rgba(255, 255, 255, {opacity * 0.7}),
                    stop:0.6 rgba(255, 255, 255, {opacity * 0.4}),
                    stop:1 rgba(255, 255, 255, {opacity * 0.1}));
                border-radius: 40px;
                border: 3px solid rgba(255, 255, 255, {intensity});
            }}
        """)
        
        # Add charging bolt symbol
        self.setText("⚡")
        self.setFont(QFont("Segoe UI", 32, QFont.Bold))
        self.setAlignment(Qt.AlignCenter)


class ChargingPopup(QWidget):
    def __init__(self, battery_percent, time_left, position="right"):
        super().__init__()

        # Transparent window with proper flags
        self.setWindowFlags(
            Qt.FramelessWindowHint | 
            Qt.WindowStaysOnTopHint | 
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_DeleteOnClose)  # Auto cleanup

        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # Use custom animated charging widget instead of GIF
        self.label_anim = AnimatedChargingWidget(self)
        self.label_anim.start_animation()
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
        self.fade_anim.finished.connect(self.cleanup_and_close)
        self.fade_anim.start()

    def cleanup_and_close(self):
        """Cleanup resources before closing"""
        # Stop the animation
        if hasattr(self, 'label_anim'):
            self.label_anim.stop_animation()
        self.close()


class BatteryMonitor(QWidget):
    def __init__(self):
        super().__init__()
        
        # Hide the monitor widget (we only need it for the timer)
        self.hide()
        
        # Initialize system tray
        self.setup_system_tray()
        
        # Track charging state
        battery = psutil.sensors_battery()
        self.last_plugged = battery.power_plugged if battery else False
        self.last_percent = int(battery.percent) if battery else 0
        
        # Setup timer to check battery status
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.check_battery)
        self.timer.start(1000)  # Check every 1 second for better responsiveness
        
        # Keep track of active popup
        self.active_popup = None
        
        logger.info("Battery monitor started. Waiting for charger plug-in events...")
        
    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        if not QSystemTrayIcon.isSystemTrayAvailable():
            logger.warning("System tray is not available")
            return
            
        # Create tray icon
        self.tray_icon = QSystemTrayIcon(self)
        
        # Create a simple icon (battery symbol)
        pixmap = QPixmap(32, 32)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QBrush(QColor(255, 255, 255)))
        painter.setPen(QColor(255, 255, 255))
        painter.drawEllipse(4, 4, 24, 24)
        painter.end()
        
        self.tray_icon.setIcon(QIcon(pixmap))
        self.tray_icon.setToolTip("Laptop Charging Monitor")
        
        # Create context menu
        menu = QMenu()
        
        # Status action
        self.status_action = QAction("Status: Monitoring...", self)
        self.status_action.setEnabled(False)
        menu.addAction(self.status_action)
        
        menu.addSeparator()
        
        # Exit action
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.exit_app)
        menu.addAction(exit_action)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        
        # Show message when started
        self.tray_icon.showMessage(
            "Charging Monitor",
            "Battery monitoring started",
            QSystemTrayIcon.Information,
            2000
        )
        
    def exit_app(self):
        """Exit the application"""
        logger.info("Exiting application...")
        QApplication.quit()

    def check_battery(self):
        """Check battery status and show popup if just plugged in"""
        try:
            battery = psutil.sensors_battery()
            if not battery:
                logger.warning("No battery information available")
                return
            
            current_plugged = battery.power_plugged
            current_percent = int(battery.percent)
            
            # Update tray status
            if hasattr(self, 'status_action'):
                status_text = f"Status: {'Charging' if current_plugged else 'Discharging'} - {current_percent}%"
                self.status_action.setText(status_text)
            
            # Charger just plugged in
            if current_plugged and not self.last_plugged:
                logger.info(f"Charger plugged in! Battery: {current_percent}%")
                
                # Clean up old popup if exists
                if self.active_popup:
                    self.active_popup.close()
                    self.active_popup = None
                
                # Get battery info with retry for time estimation
                percent = current_percent
                time_left = format_time_left(battery.secsleft)
                
                # If time is not available yet, wait and retry
                if battery.secsleft == psutil.POWER_TIME_UNLIMITED or battery.secsleft < 0:
                    # Retry after 1 second to get accurate time
                    QTimer.singleShot(1000, lambda: self.show_popup_with_retry(percent))
                else:
                    # Show popup immediately with time info
                    position = "center" if is_locked() else "right"
                    self.active_popup = ChargingPopup(percent, time_left, position)
                    self.active_popup.show()
                    
                # Show tray notification
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.showMessage(
                        "Charging Started",
                        f"Battery: {percent}% • {time_left}",
                        QSystemTrayIcon.Information,
                        3000
                    )
            
            # Charger just unplugged
            elif not current_plugged and self.last_plugged:
                logger.info(f"Charger unplugged! Battery: {current_percent}%")
                
                # Show tray notification for unplugging
                if hasattr(self, 'tray_icon'):
                    self.tray_icon.showMessage(
                        "Charging Stopped",
                        f"Battery: {current_percent}%",
                        QSystemTrayIcon.Warning,
                        2000
                    )
            
            self.last_plugged = current_plugged
            self.last_percent = current_percent
            
        except Exception as e:
            logger.error(f"Error checking battery: {e}")
    
    def show_popup_with_retry(self, initial_percent):
        """Show popup after retrying to get accurate battery time"""
        try:
            battery = psutil.sensors_battery()
            if not battery:
                return
            
            percent = int(battery.percent)
            time_left = format_time_left(battery.secsleft)
            
            logger.info(f"Battery info: {percent}%, Time left: {time_left}, Raw seconds: {battery.secsleft}")
            
            # Determine position based on lock state
            position = "center" if is_locked() else "right"
            
            # Show popup
            self.active_popup = ChargingPopup(percent, time_left, position)
            self.active_popup.show()
            
        except Exception as e:
            logger.error(f"Error showing popup with retry: {e}")


def main():
    logger.info("Starting Laptop Charging Monitor...")
    
    # Check if we can access battery information
    try:
        battery = psutil.sensors_battery()
        if not battery:
            logger.error("No battery information available. This program requires a laptop with battery.")
            return
        logger.info(f"Battery detected: {int(battery.percent)}% - {'Charging' if battery.power_plugged else 'Discharging'}")
    except Exception as e:
        logger.error(f"Error accessing battery information: {e}")
        return
    
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)  # Keep running when windows are closed
    
    # Create battery monitor
    monitor = BatteryMonitor()
    
    logger.info("Application started successfully. Running in background...")
    
    # Run the application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
