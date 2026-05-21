@echo off
REM Pendulum Tracking System - Installation Script for Windows

echo.
echo ============================================================
echo  PENDULUM TRACKING SYSTEM - SETUP
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from python.org
    pause
    exit /b 1
)

echo [1/3] Installing required packages...
pip install --upgrade pip
pip install -r requirements.txt

if errorlevel 1 (
    echo Error: Failed to install packages
    pause
    exit /b 1
)

echo.
echo [2/3] Running validation tests...
python test_integration.py --mode validate

if errorlevel 1 (
    echo Warning: Some tests may have failed, but you can still continue
)

echo.
echo [3/3] Setup complete!
echo.
echo ============================================================
echo  READY TO USE
echo ============================================================
echo.
echo Quick Start Commands:
echo.
echo 1. Interactive menu (Recommended):
echo    python menu.py
echo.
echo 2. Direct live tracking:
echo    python test_integration.py --mode live --experiment 1
echo.
echo 3. Process video:
echo    python test_integration.py --mode video --video your_video.mp4
echo.
echo For detailed help:
echo    python test_integration.py --help
echo    Read README_TRACKING.md
echo.
echo ============================================================
echo.
pause
