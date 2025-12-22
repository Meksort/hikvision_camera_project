@echo off
chcp 65001 >nul
set PYTHONIOENCODING=utf-8
echo ======================================================================
echo Пересчет статистики посещаемости с 1 декабря
echo ======================================================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat
python recalculate_attendance_stats.py

pause



