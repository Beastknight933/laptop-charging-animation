@echo off
title HP Charging Monitor Installer
color 0A

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║        HP Charging Monitor Installer                       ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo Installing HP Charging Monitor...
echo.

:: Check admin
net session >nul 2>&1 || (echo [ERROR] Run as administrator! & pause & exit /b 1)

set "INSTALL_DIR=%PROGRAMFILES%\HP Charging Monitor"

echo [1/3] Installing files...
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy "HPChargingMonitor.exe" "%INSTALL_DIR%\"

echo [2/3] Creating shortcuts...
powershell -Command "& {$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\HP Charging Monitor.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\HPChargingMonitor.exe'; $Shortcut.Save()}"

echo [3/3] Setting auto-startup...
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "HP Charging Monitor" /t REG_SZ /d "%INSTALL_DIR%\HPChargingMonitor.exe" /f

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Installation Complete!                  ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo HP Charging Monitor installed successfully!
echo - Desktop shortcut created
echo - Auto-startup enabled
echo.
echo Starting HP Charging Monitor...
start "" "%INSTALL_DIR%\HPChargingMonitor.exe"
echo.
echo Look for the battery icon in your system tray!
pause
