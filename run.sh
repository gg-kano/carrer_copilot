#!/bin/bash
# Career Copilot - Quick Launch Script for Linux/Mac

echo "========================================"
echo "Career Copilot - Starting Application"
echo "========================================"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "[ERROR] .env file not found!"
    echo "Please run ./setup.sh first or copy .env.example to .env"
    echo ""
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    exit 1
fi

echo "Starting Career Copilot..."
echo "The application will open in your default browser"
echo ""
echo "Press Ctrl+C to stop the application"
echo ""

streamlit run app.py
