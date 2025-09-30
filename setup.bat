@echo off
REM YouTube Highlighter - Windows Setup Script
REM This script sets up the development environment with all dependencies

echo.
echo ╔══════════════════════════════════════╗
echo ║     YouTube Highlighter Setup       ║
echo ╚══════════════════════════════════════╝
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found

REM Check if pip is available
python -m pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip is not available
    echo Please ensure pip is installed with Python
    pause
    exit /b 1
)
echo ✅ pip found

REM Remove old virtual environment if it exists
if exist "venv" (
    echo ⚠️ Removing existing virtual environment...
    rmdir /s /q venv
)

REM Create virtual environment
echo 📋 Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ❌ Failed to create virtual environment
    pause
    exit /b 1
)
echo ✅ Virtual environment created

REM Activate virtual environment and install dependencies
echo 📋 Activating virtual environment and installing dependencies...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip

REM Install specific moviepy version first to avoid conflicts
echo 📋 Installing moviepy (specific version)...
pip install moviepy==1.0.3

REM Install other dependencies
if exist "requirements-lock.txt" (
    echo 📋 Installing from requirements-lock.txt...
    pip install -r requirements-lock.txt
) else (
    echo 📋 Installing from requirements.txt...
    pip install -r requirements.txt
)

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

REM Test installation
echo 📋 Testing installation...
python -c "from moviepy.editor import VideoFileClip; import torch; import flask; print('✅ Critical modules imported successfully!')"
if %errorlevel% neq 0 (
    echo ❌ Installation validation failed
    pause
    exit /b 1
)

REM Test CLI
python app\cli.py --help >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ CLI test failed
    pause
    exit /b 1
)
echo ✅ CLI is working

REM Create activation script
echo @echo off > activate.bat
echo call venv\Scripts\activate.bat >> activate.bat
echo set PYTHONPATH=. >> activate.bat
echo echo YouTube Highlighter environment activated! >> activate.bat
echo echo Usage: >> activate.bat
echo echo   python app\cli.py --help              # Show CLI help >> activate.bat
echo echo   python app\web\server.py              # Start web server >> activate.bat
echo echo   deactivate                            # Exit virtual environment >> activate.bat

echo.
echo ╔══════════════════════════════════════╗
echo ║         Setup Complete! 🎉          ║
echo ╚══════════════════════════════════════╝
echo.
echo ✅ YouTube Highlighter is ready to use!
echo.
echo Quick Start:
echo   1. Activate environment:  activate.bat
echo   2. Start web server:      python app\web\server.py
echo   3. Open browser:          http://localhost:5000
echo.
echo CLI Usage:
echo   • Show help:              python app\cli.py --help
echo   • Download transcript:    python app\cli.py download-transcript URL
echo   • Generate highlights:    python app\cli.py generate URL transcript.vtt
echo.
echo Development:
echo   • Run tests:              python -m pytest
echo   • Validate install:       python validate.py
echo.
echo ⚠️ Note: FFmpeg is recommended for video processing
echo Install from: https://ffmpeg.org/download.html
echo.
pause