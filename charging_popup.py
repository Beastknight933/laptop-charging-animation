"""
Laptop Charging Monitor with Custom Time Estimation

CONFIGURATION REQUIRED:
Update the LAPTOP_CONFIG section below with your laptop's specifications:
- battery_capacity_wh: Battery capacity in Watt-hours (check laptop specs or battery label)
- charger_wattage: Charger power in Watts (check charger label)
- charging_efficiency: Usually 0.85 (85%) for most laptops
- model_name: Your laptop model name (for logging)

Example: Dell XPS 13 might have 52Wh battery and 45W charger
"""

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

# Laptop-specific charging configuration
# Update these values for your specific laptop model
LAPTOP_CONFIG = {
    "battery_capacity_wh": 56.04,  # HP Li-Polymer battery (56.04Wh, 11.58Vdc, 4646mAh)
    "charger_wattage": 65,          # HP 65W charger (20VDC 3.25A)
    "charging_efficiency": 0.85,    # Charging efficiency (85% is typical)
    "model_name": "HP Laptop"        # HP laptop with 65W charger and 56.04Wh battery
}

def calculate_charging_time(battery_percent, battery_capacity_wh, charger_wattage, efficiency):
    """
    Calculate estimated charging time based on laptop specifications
    
    Args:
        battery_percent: Current battery percentage (0-100)
        battery_capacity_wh: Battery capacity in Watt-hours
        charger_wattage: Charger power in Watts
        efficiency: Charging efficiency (0.0-1.0)
    
    Returns:
        Estimated time in seconds, or None if calculation not possible
    """
    try:
        # Calculate remaining capacity to charge
        remaining_percent = 100 - battery_percent
        if remaining_percent <= 0:
            return 0  # Already fully charged
        
        # Calculate remaining energy to charge (in Wh)
        remaining_energy_wh = (remaining_percent / 100) * battery_capacity_wh
        
        # Calculate effective charging power (accounting for efficiency)
        effective_power_w = charger_wattage * efficiency
        
        # Calculate time in hours
        time_hours = remaining_energy_wh / effective_power_w
        
        # Convert to seconds
        time_seconds = int(time_hours * 3600)
        
        logger.info(f"Charging calculation: {remaining_percent}% remaining, "
                   f"{remaining_energy_wh:.1f}Wh to charge, "
                   f"{effective_power_w:.1f}W effective power, "
                   f"{time_hours:.2f}h estimated")
        
        return time_seconds
        
    except Exception as e:
        logger.error(f"Error calculating charging time: {e}")
        return None


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


def format_time_left(secs, battery_percent=None):
    """Convert seconds to H:M format, with custom calculation fallback"""
    if secs == psutil.POWER_TIME_UNLIMITED or secs < 0:
        # Try custom calculation if Windows can't provide time
        if battery_percent is not None:
            custom_time = calculate_charging_time(
                battery_percent,
                LAPTOP_CONFIG["battery_capacity_wh"],
                LAPTOP_CONFIG["charger_wattage"],
                LAPTOP_CONFIG["charging_efficiency"]
            )
            if custom_time is not None and custom_time > 0:
                secs = custom_time
            else:
                return ""  # No time available
        else:
            return ""  # No time available
    
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
        if time_left:
            self.label_text.setText(f"{battery_percent}% Charging • {time_left}")
        else:
            self.label_text.setText(f"{battery_percent}% Charging")
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
                time_left = format_time_left(battery.secsleft, percent)
                
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
                    if time_left:
                        message = f"Battery: {percent}% • {time_left}"
                    else:
                        message = f"Battery: {percent}%"
                    self.tray_icon.showMessage(
                        "Charging Started",
                        message,
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
            time_left = format_time_left(battery.secsleft, percent)
            
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
    logger.info(f"Configuration: {LAPTOP_CONFIG['model_name']} - "
               f"{LAPTOP_CONFIG['battery_capacity_wh']}Wh battery, "
               f"{LAPTOP_CONFIG['charger_wattage']}W charger, "
               f"{LAPTOP_CONFIG['charging_efficiency']*100:.0f}% efficiency")
    
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
