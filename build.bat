@echo off
title HP Charging Monitor - One-Click Builder
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║        HP Charging Monitor - One-Click Builder             ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Run as administrator!
    pause & exit /b 1
)

:: Create directories
if not exist "dist" mkdir "dist"

:: Install dependencies
echo Installing dependencies...
pip install pyinstaller PyQt5 psutil --quiet

:: Create simple icon
powershell -Command "& {$bmp = New-Object System.Drawing.Bitmap(32,32); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::Transparent); $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::White); $g.FillRectangle($brush, 4, 8, 20, 12); $g.DrawRectangle([System.Drawing.Pens]::White, 4, 8, 20, 12); $g.FillRectangle($brush, 24, 12, 2, 4); $font = New-Object System.Drawing.Font('Arial', 12, [System.Drawing.FontStyle]::Bold); $g.DrawString('⚡', $font, $brush, 8, 4); $bmp.Save('icon.ico', [System.Drawing.Imaging.ImageFormat]::Icon); $g.Dispose(); $bmp.Dispose()}" >nul 2>&1

:: Build executable
echo Building executable...
pyinstaller --onefile --windowed --name HPChargingMonitor --icon=icon.ico --clean charging_popup.py

:: Create super simple installer
echo Creating installer...
echo @echo off > "HPChargingMonitorInstaller.bat"
echo title HP Charging Monitor Installer >> "HPChargingMonitorInstaller.bat"
echo color 0A >> "HPChargingMonitorInstaller.bat"
echo. >> "HPChargingMonitorInstaller.bat"
echo echo ╔══════════════════════════════════════════════════════════════╗ >> "HPChargingMonitorInstaller.bat"
echo echo ║        HP Charging Monitor Installer                       ║ >> "HPChargingMonitorInstaller.bat"
echo echo ╚══════════════════════════════════════════════════════════════╝ >> "HPChargingMonitorInstaller.bat"
echo echo. >> "HPChargingMonitorInstaller.bat"
echo echo Installing HP Charging Monitor... >> "HPChargingMonitorInstaller.bat"
echo echo. >> "HPChargingMonitorInstaller.bat"
echo. >> "HPChargingMonitorInstaller.bat"
echo :: Check admin >> "HPChargingMonitorInstaller.bat"
echo net session ^>nul 2^>^&1 ^|^| ^(echo [ERROR] Run as administrator! ^& pause ^& exit /b 1^) >> "HPChargingMonitorInstaller.bat"
echo. >> "HPChargingMonitorInstaller.bat"
echo set "INSTALL_DIR=%%PROGRAMFILES%%\HP Charging Monitor" >> "HPChargingMonitorInstaller.bat"
echo. >> "HPChargingMonitorInstaller.bat"
echo echo [1/3] Installing files... >> "HPChargingMonitorInstaller.bat"
echo if not exist "%%INSTALL_DIR%%" mkdir "%%INSTALL_DIR%%" >> "HPChargingMonitorInstaller.bat"
echo copy "HPChargingMonitor.exe" "%%INSTALL_DIR%%\" >> "HPChargingMonitorInstaller.bat"
echo. >> "HPChargingMonitorInstaller.bat"
echo echo [2/3] Creating shortcuts... >> "HPChargingMonitorInstaller.bat"
echo powershell -Command "& {$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%%USERPROFILE%%\Desktop\HP Charging Monitor.lnk'); $Shortcut.TargetPath = '%%INSTALL_DIR%%\HPChargingMonitor.exe'; $Shortcut.Save()}" >> "HPChargingMonitorInstaller.bat"
echo. >> "HPChargingMonitorInstaller.bat"
echo echo [3/3] Setting auto-startup... >> "HPChargingMonitorInstaller.bat"
echo reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "HP Charging Monitor" /t REG_SZ /d "%%INSTALL_DIR%%\HPChargingMonitor.exe" /f >> "HPChargingMonitorInstaller.bat"
echo. >> "HPChargingMonitorInstaller.bat"
echo echo ╔══════════════════════════════════════════════════════════════╗ >> "HPChargingMonitorInstaller.bat"
echo echo ║                    Installation Complete!                  ║ >> "HPChargingMonitorInstaller.bat"
echo echo ╚══════════════════════════════════════════════════════════════╝ >> "HPChargingMonitorInstaller.bat"
echo echo. >> "HPChargingMonitorInstaller.bat"
echo echo HP Charging Monitor installed successfully! >> "HPChargingMonitorInstaller.bat"
echo echo - Desktop shortcut created >> "HPChargingMonitorInstaller.bat"
echo echo - Auto-startup enabled >> "HPChargingMonitorInstaller.bat"
echo echo. >> "HPChargingMonitorInstaller.bat"
echo echo Starting HP Charging Monitor... >> "HPChargingMonitorInstaller.bat"
echo start "" "%%INSTALL_DIR%%\HPChargingMonitor.exe" >> "HPChargingMonitorInstaller.bat"
echo echo. >> "HPChargingMonitorInstaller.bat"
echo echo Look for the battery icon in your system tray! >> "HPChargingMonitorInstaller.bat"
echo pause >> "HPChargingMonitorInstaller.bat"

:: Copy files to installer
copy "dist\HPChargingMonitor.exe" "HPChargingMonitorInstaller.bat" >nul

:: Cleanup
del "icon.ico" 2>nul
rmdir /s /q "build" 2>nul

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Build Complete!                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo ✓ Executable: dist\HPChargingMonitor.exe
echo ✓ Installer: HPChargingMonitorInstaller.bat
echo.
echo Ready for distribution! Just share HPChargingMonitorInstaller.bat
echo.

pause
