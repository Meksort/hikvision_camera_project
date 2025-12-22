@echo off
chcp 65001 >nul
echo ========================================
echo Остановка проекта Hikvision Camera
echo ========================================
echo.

cd /d "%~dp0"

docker-compose down

echo.
echo Контейнеры остановлены.
pause

















