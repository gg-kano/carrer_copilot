@echo off
REM Career Copilot - Quick Setup Script for Windows
REM This script helps you set up Career Copilot quickly

echo ========================================
echo Career Copilot - Quick Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.12+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [1/4] Python detected
python --version

echo.
echo [2/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [3/4] Setting up environment variables...
if not exist .env (
    copy .env.example .env
    echo [INFO] Created .env file from .env.example
    echo [ACTION REQUIRED] Please edit .env and add your GOOGLE_API_KEY
    echo.
    notepad .env
) else (
    echo [INFO] .env file already exists
)

echo.
echo [4/4] Setup complete!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Make sure you've added your GOOGLE_API_KEY to .env
echo 2. Run: run.bat
echo    OR
echo    Run: streamlit run app.py
echo.
echo ========================================

pause
