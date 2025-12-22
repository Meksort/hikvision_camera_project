@echo off
cd /d "%~dp0"
echo ========================================
echo СОЗДАНИЕ МИГРАЦИЙ
echo ========================================
echo.
venv\Scripts\python.exe manage.py makemigrations camera_events
echo.
echo ========================================
echo ГОТОВО!
echo ========================================
pause

