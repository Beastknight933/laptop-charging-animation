@echo off
title HP Charging Monitor - Complete Installer Builder
color 0A

echo.
echo  ╔══════════════════════════════════════════════════════════════╗
echo  ║                                                              ║
echo  ║        HP Charging Monitor - Complete Installer Builder      ║
echo  ║                                                              ║
echo  ╚══════════════════════════════════════════════════════════════╝
echo.

:: Check for administrator privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [ERROR] Administrator privileges required!
    echo.
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

echo [INFO] Running with administrator privileges ✓
echo.

:: Create build directory structure
echo [STEP 1] Creating build directories...
if not exist "build" mkdir "build"
if not exist "dist" mkdir "dist"
if not exist "installer" mkdir "installer"
echo [OK] Build directories created ✓

:: Install required packages
echo.
echo [STEP 2] Installing build dependencies...
pip install pyinstaller PyQt5 psutil
if %errorLevel% neq 0 (
    echo [ERROR] Failed to install dependencies!
    pause
    exit /b 1
)
echo [OK] Dependencies installed ✓

:: Create a simple icon (if not exists)
echo.
echo [STEP 3] Creating application icon...
if not exist "icon.ico" (
    echo [INFO] Creating default icon...
    :: Create a simple ICO file using PowerShell
    powershell -Command "& {Add-Type -AssemblyName System.Drawing; $bmp = New-Object System.Drawing.Bitmap(32,32); $g = [System.Drawing.Graphics]::FromImage($bmp); $g.Clear([System.Drawing.Color]::White); $brush = New-Object System.Drawing.SolidBrush([System.Drawing.Color]::Blue); $g.FillEllipse($brush, 4, 4, 24, 24); $font = New-Object System.Drawing.Font('Arial', 16, [System.Drawing.FontStyle]::Bold); $g.DrawString('⚡', $font, $brush, 8, 4); $bmp.Save('icon.ico', [System.Drawing.Imaging.ImageFormat]::Icon); $g.Dispose(); $bmp.Dispose()}"
    echo [OK] Default icon created ✓
) else (
    echo [OK] Icon file already exists ✓
)

:: Build the executable
echo.
echo [STEP 4] Building executable...
pyinstaller --onefile --windowed --name HPChargingMonitor --icon=icon.ico --add-data "README.md;." charging_popup.py
if %errorLevel% neq 0 (
    echo [ERROR] Failed to build executable!
    pause
    exit /b 1
)
echo [OK] Executable built successfully ✓

:: Copy files to installer directory
echo.
echo [STEP 5] Preparing installer files...
copy "dist\HPChargingMonitor.exe" "installer\"
copy "icon.ico" "installer\"
copy "README.md" "installer\"
echo [OK] Installer files prepared ✓

:: Create license file
echo.
echo [STEP 6] Creating license file...
echo MIT License > "installer\LICENSE.txt"
echo. >> "installer\LICENSE.txt"
echo Copyright ^(c^) 2024 HP Charging Monitor >> "installer\LICENSE.txt"
echo. >> "installer\LICENSE.txt"
echo Permission is hereby granted, free of charge, to any person obtaining a copy >> "installer\LICENSE.txt"
echo of this software and associated documentation files ^(the "Software"^), to deal >> "installer\LICENSE.txt"
echo in the Software without restriction, including without limitation the rights >> "installer\LICENSE.txt"
echo to use, copy, modify, merge, publish, distribute, sublicense, and/or sell >> "installer\LICENSE.txt"
echo copies of the Software, and to permit persons to whom the Software is >> "installer\LICENSE.txt"
echo furnished to do so, subject to the following conditions: >> "installer\LICENSE.txt"
echo. >> "installer\LICENSE.txt"
echo The above copyright notice and this permission notice shall be included in all >> "installer\LICENSE.txt"
echo copies or substantial portions of the Software. >> "installer\LICENSE.txt"
echo [OK] License file created ✓

:: Check for NSIS
echo.
echo [STEP 7] Checking for NSIS installer...
where makensis >nul 2>&1
if %errorLevel% neq 0 (
    echo [WARNING] NSIS not found! Creating alternative installer...
    call :create_alternative_installer
) else (
    echo [OK] NSIS found, creating professional installer...
    call :create_nsis_installer
)

echo.
echo ╔══════════════════════════════════════════════════════════════╗
echo ║                    Build Complete!                          ║
echo ╚══════════════════════════════════════════════════════════════╝
echo.
echo ✓ Executable: dist\HPChargingMonitor.exe
echo ✓ Installer files: installer\
echo ✓ Ready for distribution!
echo.

:: Ask if user wants to test the installer
set /p choice="Do you want to test the installer now? (y/n): "
if /i "%choice%"=="y" (
    echo.
    echo [INFO] Starting installer test...
    if exist "installer\HPChargingMonitorSetup.exe" (
        start "" "installer\HPChargingMonitorSetup.exe"
    ) else (
        start "" "installer\install.bat"
    )
)

echo.
pause
exit /b 0

:: Function to create NSIS installer
:create_nsis_installer
echo [INFO] Creating NSIS installer...
copy "installer.nsi" "installer\"
cd installer
makensis installer.nsi
if %errorLevel% == 0 (
    echo [OK] Professional installer created: HPChargingMonitorSetup.exe ✓
) else (
    echo [WARNING] NSIS build failed, falling back to batch installer
    call :create_alternative_installer
)
cd ..
goto :eof

:: Function to create alternative installer
:create_alternative_installer
echo [INFO] Creating batch-based installer...
echo @echo off > "installer\install.bat"
echo title HP Charging Monitor Installer >> "installer\install.bat"
echo color 0A >> "installer\install.bat"
echo. >> "installer\install.bat"
echo echo ╔══════════════════════════════════════════════════════════════╗ >> "installer\install.bat"
echo echo ║        HP Laptop Charging Monitor Installer              ║ >> "installer\install.bat"
echo echo ╚══════════════════════════════════════════════════════════════╝ >> "installer\install.bat"
echo echo. >> "installer\install.bat"
echo. >> "installer\install.bat"
echo :: Check for administrator privileges >> "installer\install.bat"
echo net session ^>nul 2^>^&1 >> "installer\install.bat"
echo if %%errorLevel%% neq 0 ^( >> "installer\install.bat"
echo     echo [ERROR] Administrator privileges required! >> "installer\install.bat"
echo     pause >> "installer\install.bat"
echo     exit /b 1 >> "installer\install.bat"
echo ^) >> "installer\install.bat"
echo. >> "installer\install.bat"
echo set "INSTALL_DIR=%%PROGRAMFILES%%\HP Charging Monitor" >> "installer\install.bat"
echo set "STARTUP_DIR=%%APPDATA%%\Microsoft\Windows\Start Menu\Programs\Startup" >> "installer\install.bat"
echo. >> "installer\install.bat"
echo echo [STEP 1/5] Creating installation directory... >> "installer\install.bat"
echo if not exist "%%INSTALL_DIR%%" mkdir "%%INSTALL_DIR%%" >> "installer\install.bat"
echo. >> "installer\install.bat"
echo echo [STEP 2/5] Copying application files... >> "installer\install.bat"
echo copy "HPChargingMonitor.exe" "%%INSTALL_DIR%%\" >> "installer\install.bat"
echo copy "README.md" "%%INSTALL_DIR%%\" >> "installer\install.bat"
echo copy "LICENSE.txt" "%%INSTALL_DIR%%\" >> "installer\install.bat"
echo. >> "installer\install.bat"
echo echo [STEP 3/5] Creating shortcuts... >> "installer\install.bat"
echo :: Desktop shortcut >> "installer\install.bat"
echo powershell -Command "& {$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%%USERPROFILE%%\Desktop\HP Charging Monitor.lnk'); $Shortcut.TargetPath = '%%INSTALL_DIR%%\HPChargingMonitor.exe'; $Shortcut.Description = 'HP Laptop Charging Monitor'; $Shortcut.Save()}" >> "installer\install.bat"
echo :: Start Menu shortcut >> "installer\install.bat"
echo if not exist "%%SMPROGRAMS%%\HP Charging Monitor" mkdir "%%SMPROGRAMS%%\HP Charging Monitor" >> "installer\install.bat"
echo powershell -Command "& {$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%%SMPROGRAMS%%\HP Charging Monitor\HP Charging Monitor.lnk'); $Shortcut.TargetPath = '%%INSTALL_DIR%%\HPChargingMonitor.exe'; $Shortcut.Description = 'HP Laptop Charging Monitor'; $Shortcut.Save()}" >> "installer\install.bat"
echo. >> "installer\install.bat"
echo echo [STEP 4/5] Setting up auto-startup... >> "installer\install.bat"
echo reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "HP Charging Monitor" /t REG_SZ /d "%%INSTALL_DIR%%\HPChargingMonitor.exe" /f >> "installer\install.bat"
echo. >> "installer\install.bat"
echo echo [STEP 5/5] Creating uninstaller... >> "installer\install.bat"
echo echo @echo off > "%%INSTALL_DIR%%\Uninstall.bat" >> "installer\install.bat"
echo echo echo Uninstalling HP Charging Monitor... >> "installer\install.bat"
echo echo taskkill /f /im HPChargingMonitor.exe 2^>nul >> "installer\install.bat"
echo echo reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v "HP Charging Monitor" /f 2^>nul >> "installer\install.bat"
echo echo del "%%USERPROFILE%%\Desktop\HP Charging Monitor.lnk" 2^>nul >> "installer\install.bat"
echo echo rmdir /s /q "%%SMPROGRAMS%%\HP Charging Monitor" 2^>nul >> "installer\install.bat"
echo echo rmdir /s /q "%%INSTALL_DIR%%" 2^>nul >> "installer\install.bat"
echo echo echo Uninstallation complete! >> "installer\install.bat"
echo echo pause >> "installer\install.bat"
echo. >> "installer\install.bat"
echo echo ╔══════════════════════════════════════════════════════════════╗ >> "installer\install.bat"
echo echo ║                    Installation Complete!                  ║ >> "installer\install.bat"
echo echo ╚══════════════════════════════════════════════════════════════╝ >> "installer\install.bat"
echo echo. >> "installer\install.bat"
echo echo HP Charging Monitor has been installed successfully! >> "installer\install.bat"
echo echo. >> "installer\install.bat"
echo echo Features: >> "installer\install.bat"
echo echo - Desktop shortcut created >> "installer\install.bat"
echo echo - Start Menu shortcut created >> "installer\install.bat"
echo echo - Auto-startup enabled >> "installer\install.bat"
echo echo - Uninstaller available in installation folder >> "installer\install.bat"
echo echo. >> "installer\install.bat"
echo set /p choice="Start HP Charging Monitor now? (y/n): " >> "installer\install.bat"
echo if /i "%%choice%%"=="y" start "" "%%INSTALL_DIR%%\HPChargingMonitor.exe" >> "installer\install.bat"
echo echo. >> "installer\install.bat"
echo pause >> "installer\install.bat"
echo exit /b 0 >> "installer\install.bat"

echo [OK] Alternative installer created: install.bat ✓
goto :eof
