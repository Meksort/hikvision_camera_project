@echo off
chcp 65001 >nul
echo ========================================
echo Пересчет EntryExit из CameraEvent
echo ========================================
echo.

REM Активируем виртуальное окружение, если оно существует
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Запускаем скрипт пересчета
python recalculate_entries_exits.py %*

if errorlevel 1 (
    echo.
    echo ОШИБКА при выполнении пересчета!
    pause
    exit /b 1
)

echo.
echo Пересчет завершен успешно!
pause


