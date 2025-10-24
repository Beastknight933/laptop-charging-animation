# Laptop Charging Monitor

A Windows application that monitors your laptop's charging status and shows notifications when you plug or unplug the charger, similar to mobile phone charging notifications.

## Features

- 🔋 **Real-time battery monitoring** - Continuously monitors charging status
- ⚡ **Animated charging notifications** - Beautiful popup notifications with custom animations
- 🖥️ **System tray integration** - Runs silently in the background
- 🔒 **Lock screen support** - Shows notifications even when Windows is locked
- 📊 **Battery information** - Displays current battery percentage and estimated time remaining
- 📝 **Detailed logging** - Logs all events for debugging

## Installation

1. **Install Python** (if not already installed)
   - Download from [python.org](https://python.org)
   - Make sure to check "Add Python to PATH" during installation

2. **Install required packages**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application**
   ```bash
   python charging_popup.py
   ```
   
   Or double-click `start_charging_monitor.bat`

## Usage

- The application runs in the system tray (bottom-right corner)
- Right-click the tray icon to see status and exit options
- Notifications appear automatically when you plug/unplug the charger
- The application continues running in the background

## Auto-start with Windows

To make the application start automatically when Windows boots:

1. Press `Win + R`, type `shell:startup`, and press Enter
2. Copy `start_charging_monitor.bat` to the startup folder
3. The application will now start automatically when Windows boots

## Troubleshooting

- **No notifications appearing**: Check if the application is running in the system tray
- **Permission errors**: Run as administrator if needed
- **Battery not detected**: This application only works on laptops with batteries
- **Logs**: Check `charging_monitor.log` for detailed information

## Requirements

- Windows 10/11
- Python 3.7+
- PyQt5
- psutil

## Notes

- The application uses custom CSS-like animations instead of GIF files for better performance
- All events are logged to `charging_monitor.log` for debugging
- The application respects Windows lock screen and shows notifications appropriately
