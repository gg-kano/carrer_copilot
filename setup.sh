#!/bin/bash
# Career Copilot - Quick Setup Script for Linux/Mac
# This script helps you set up Career Copilot quickly

echo "========================================"
echo "Career Copilot - Quick Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.12+ from https://www.python.org/downloads/"
    exit 1
fi

echo "[1/4] Python detected"
python3 --version

echo ""
echo "[2/4] Installing dependencies..."
if command -v uv &> /dev/null; then
    echo "Using uv (faster)..."
    uv sync
else
    echo "Using pip..."
    pip install -r requirements.txt
fi

if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

echo ""
echo "[3/4] Setting up environment variables..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "[INFO] Created .env file from .env.example"
    echo "[ACTION REQUIRED] Please edit .env and add your GOOGLE_API_KEY"
    echo ""
    echo "Opening .env file in default editor..."
    ${EDITOR:-nano} .env
else
    echo "[INFO] .env file already exists"
fi

echo ""
echo "[4/4] Making scripts executable..."
chmod +x run.sh setup.sh

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo "Next Steps:"
echo "1. Make sure you've added your GOOGLE_API_KEY to .env"
echo "2. Run: ./run.sh"
echo "   OR"
echo "   Run: streamlit run app.py"
echo ""
echo "========================================"
