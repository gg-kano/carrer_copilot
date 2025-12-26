@echo off
REM Career Copilot - Quick Launch Script for Windows

echo ========================================
echo Career Copilot - Starting Application
echo ========================================
echo.

REM Check if .env exists
if not exist .env (
    echo [ERROR] .env file not found!
    echo Please run setup.bat first or copy .env.example to .env
    echo.
    pause
    exit /b 1
)

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    pause
    exit /b 1
)

echo Starting Career Copilot...
echo The application will open in your default browser
echo.
echo Press Ctrl+C to stop the application
echo.

streamlit run app.py

pause
