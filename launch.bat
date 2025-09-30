@echo off
REM YouTube Highlighter - Windows Double-Click Launcher
REM This file can be double-clicked in Windows Explorer to launch the application

setlocal EnableDelayedExpansion
cd /d "%~dp0"

title YouTube Highlighter Launcher

echo.
echo ╔══════════════════════════════════════╗
echo ║     YouTube Highlighter Launcher    ║
echo ╚══════════════════════════════════════╝
echo.

echo [LAUNCHER] Starting YouTube Highlighter...
echo [LAUNCHER] Working directory: %CD%
echo.

REM Check if Python is available
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    echo.
    pause
    exit /b 1
)

REM Check if setup is needed
if not exist "venv" (
    echo ⚠️ First time setup required!
    echo [LAUNCHER] Running automated setup...
    echo.
    
    if exist "setup.bat" (
        call setup.bat
        if !errorlevel! neq 0 (
            echo.
            echo ❌ Setup failed!
            echo Please check the error messages above.
            echo.
            pause
            exit /b 1
        )
    ) else (
        echo ❌ setup.bat not found!
        echo Please ensure you're in the YouTube Highlighter directory.
        echo.
        pause
        exit /b 1
    )
) else (
    echo ✅ Environment already set up!
)

REM Activate environment
echo [LAUNCHER] Activating virtual environment...
call venv\Scripts\activate.bat
set PYTHONPATH=.

REM Quick health check
echo [LAUNCHER] Performing health check...
python -c "from moviepy.editor import VideoFileClip" 2>nul
if %errorlevel% neq 0 (
    echo ❌ Environment health check failed!
    echo Try running setup again or check the logs above.
    echo.
    pause
    exit /b 1
)

echo ✅ Health check passed!
echo.

REM Show launch info
echo ✅ 🚀 Starting YouTube Highlighter web server...
echo ✅ 🌐 Browser will open automatically at: http://localhost:5000
echo ⚠️ 📋 Keep this window open while using the application
echo ⚠️ 🛑 Press Ctrl+C to stop the server
echo.

REM Start browser opener in background (after 3 seconds)
start /b cmd /c "timeout /t 3 >nul 2>&1 && start http://localhost:5000"

echo Ready! Starting server...
echo.

REM Start the server
python app\web\server.py

REM Server stopped
echo.
echo [LAUNCHER] Server stopped.
echo [LAUNCHER] Thank you for using YouTube Highlighter!
echo.
pause