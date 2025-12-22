@echo off
chcp 65001 >nul 2>&1
cls

echo ========================================
echo Starting Hikvision Camera Project
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Checking virtual environment...
if not exist "venv\Scripts\python.exe" (
    echo ERROR: Virtual environment not found at venv\Scripts\python.exe
    echo Please create virtual environment first: python -m venv venv
    pause
    exit /b 1
)

set PYTHON_EXE=%~dp0venv\Scripts\python.exe

echo OK: Virtual environment found

echo.
echo [2/3] Checking Python and Django...
"%PYTHON_EXE%" --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found in virtual environment!
    pause
    exit /b 1
)

"%PYTHON_EXE%" manage.py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Django not found or manage.py not accessible!
    echo Make sure Django is installed: "%PYTHON_EXE%" -m pip install -r requirements.txt
    pause
    exit /b 1
)

echo Checking database connection...
"%PYTHON_EXE%" manage.py check --database default >nul 2>&1
if errorlevel 1 (
    echo WARNING: Database connection issues detected!
    echo Make sure PostgreSQL is running.
    echo Continuing anyway...
    echo.
)

echo.
echo [3/3] Starting Django server...
echo.
echo ========================================
echo Server will start on 0.0.0.0:8000
echo ========================================
echo.
echo Available addresses:
echo   - localhost:8000
echo   - 127.0.0.1:8000
echo   - 192.168.1.129:8000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

"%PYTHON_EXE%" manage.py runserver 0.0.0.0:8000

echo.
echo ========================================
echo Server stopped
echo ========================================
pause
