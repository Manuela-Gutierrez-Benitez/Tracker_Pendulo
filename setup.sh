#!/bin/bash
# Pendulum Tracking System - Installation Script for Linux/Mac

echo ""
echo "============================================================"
echo "  PENDULUM TRACKING SYSTEM - SETUP"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

echo "[1/3] Installing required packages..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install packages"
    exit 1
fi

echo ""
echo "[2/3] Running validation tests..."
python3 test_integration.py --mode validate

if [ $? -ne 0 ]; then
    echo "Warning: Some tests may have failed, but you can still continue"
fi

echo ""
echo "[3/3] Setup complete!"
echo ""
echo "============================================================"
echo "  READY TO USE"
echo "============================================================"
echo ""
echo "Quick Start Commands:"
echo ""
echo "1. Interactive menu (Recommended):"
echo "   python3 menu.py"
echo ""
echo "2. Direct live tracking:"
echo "   python3 test_integration.py --mode live --experiment 1"
echo ""
echo "3. Process video:"
echo "   python3 test_integration.py --mode video --video your_video.mp4"
echo ""
echo "For detailed help:"
echo "   python3 test_integration.py --help"
echo "   cat README_TRACKING.md"
echo ""
echo "============================================================"
echo ""
