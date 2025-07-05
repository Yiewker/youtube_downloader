@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title YouTube Downloader

echo ========================================
echo    YouTube Downloader Startup Check
echo ========================================
echo.

:: Set config file path
set CONFIG_FILE=youtube_downloader_config.yaml
set PYTHON_PATH=
set PROXY_TEST_ENABLED=false

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

:: Read proxy test setting from YAML config file (simple check)
findstr /C:"test_on_startup: true" "%CONFIG_FILE%" >nul 2>&1
if %errorlevel% equ 0 (
    set PROXY_TEST_ENABLED=true
) else (
    set PROXY_TEST_ENABLED=false
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

:: Check if proxy test is enabled
if "%PROXY_TEST_ENABLED%"=="true" goto :test_proxy
echo [SKIP] Proxy test disabled (test_on_startup: false)
goto :start_app

:test_proxy
echo [INFO] Testing proxy connection (port 7890)...

:: Use faster curl command with shorter timeout
curl -s --proxy http://127.0.0.1:7890 --connect-timeout 2 --max-time 3 https://httpbin.org/ip >nul 2>&1

if %errorlevel% equ 0 (
    echo [OK] Proxy connection test successful - port 7890 available
) else (
    echo [WARN] Proxy connection test failed - continuing anyway
    echo [HINT] You can enable/disable proxy testing in config: test_on_startup
)

:start_app

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

echo.
echo Program exited, press any key to close window...
pause >nul
