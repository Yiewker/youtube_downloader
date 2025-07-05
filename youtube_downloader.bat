@echo off
chcp 65001 >nul
title YouTube Downloader

echo ========================================
echo    YouTube Downloader Startup Check
echo ========================================
echo.

:: Set config file path
set CONFIG_FILE=youtube_downloader_config.yaml
set PYTHON_PATH=

:: Check if config file exists
if not exist "%CONFIG_FILE%" (
    echo [ERROR] Config file %CONFIG_FILE% not found!
    echo Please ensure config file is in current directory.
    pause
    exit /b 1
)

:: Read Python path from YAML config file (simple parsing)
for /f "tokens=2* delims=:" %%a in ('findstr "python_path:" "%CONFIG_FILE%"') do (
    set PYTHON_PATH=%%b
)

:: Clean quotes and spaces from Python path
set PYTHON_PATH=%PYTHON_PATH:"=%
set PYTHON_PATH=%PYTHON_PATH: =%

echo [INFO] Python path from config: %PYTHON_PATH%

:: Check if Python exists
if not exist "%PYTHON_PATH%" (
    echo [ERROR] Python interpreter not found: %PYTHON_PATH%
    echo Please check python_path setting in config file.
    pause
    exit /b 1
)

echo [OK] Python interpreter check passed

:: Test proxy connection
echo [INFO] Testing proxy connection (port 7890)...

:: Use PowerShell to test proxy connection to Google
powershell -Command "try { $response = Invoke-WebRequest -Uri 'https://www.google.com' -Proxy 'http://127.0.0.1:7890' -TimeoutSec 10 -UseBasicParsing; exit 0 } catch { exit 1 }" >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] Proxy connection test successful - port 7890 available
    echo.
    echo [INFO] Starting YouTube downloader...
    echo.

    :: Start Python program
    "%PYTHON_PATH%" youtube_downloader.py

    if %errorlevel% neq 0 (
        echo.
        echo [ERROR] YouTube downloader failed to run
        pause
    )
) else (
    echo [FAIL] Proxy connection test failed
    echo.
    echo ========================================
    echo           Proxy Setup Instructions
    echo ========================================
    echo Please ensure the following conditions are met:
    echo 1. Clash or other proxy software is running
    echo 2. Proxy software listens on 127.0.0.1:7890
    echo 3. Proxy software allows LAN connections
    echo 4. Proxy can access foreign websites normally
    echo.
    echo Common solutions:
    echo - Start Clash and ensure port is set to 7890
    echo - Check if firewall blocks proxy software
    echo - Try restarting proxy software
    echo.
    echo If proxy is not needed, set proxy.enabled to false in config
    echo ========================================
    echo.
    pause
    exit /b 1
)

echo.
echo Program exited, press any key to close window...
pause >nul
