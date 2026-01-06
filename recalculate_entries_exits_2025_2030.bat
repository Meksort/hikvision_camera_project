@echo off
chcp 65001 >nul
echo ========================================
echo Пересчет EntryExit из CameraEvent
echo Период: с 2025-12-01 по 2030-12-01
echo ========================================
echo.

REM Активируем виртуальное окружение, если оно существует
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
)

REM Запускаем скрипт пересчета с фиксированным диапазоном дат
python recalculate_entries_exits.py --start-date 2025-12-01 --end-date 2030-12-01

if errorlevel 1 (
    echo.
    echo ОШИБКА при выполнении пересчета!
    pause
    exit /b 1
)

echo.
echo Пересчет завершен успешно!
pause






