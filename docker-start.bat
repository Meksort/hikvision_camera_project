@echo off
chcp 65001 >nul
echo ========================================
echo Запуск проекта Hikvision Camera в Docker
echo ========================================
echo.

cd /d "%~dp0"

echo [1/3] Проверка Docker...
docker --version >nul 2>&1
if errorlevel 1 (
    echo ОШИБКА: Docker не установлен или не запущен!
    echo Установите Docker Desktop: https://www.docker.com/products/docker-desktop
    pause
    exit /b 1
)

echo [2/3] Сборка и запуск контейнеров...
docker-compose up --build -d

if errorlevel 1 (
    echo ОШИБКА: Не удалось запустить контейнеры!
    pause
    exit /b 1
)

echo [3/3] Ожидание готовности базы данных...
timeout /t 5 /nobreak >nul

echo.
echo ========================================
echo Сервер запущен в Docker!
echo ========================================
echo.
echo Доступные адреса:
echo   - http://localhost:8000/
echo   - http://127.0.0.1:8000/
echo   - http://192.168.1.129:8000/ (для доступа из локальной сети)
echo.
echo Админка: http://192.168.1.129:8000/admin/ (admin/admin123)
echo Отчеты: http://192.168.1.129:8000/report/
echo Статистика: http://192.168.1.129:8000/attendance-stats/
echo.
echo API:
echo   - http://192.168.1.129:8000/api/camera-events/
echo   - http://192.168.1.129:8000/api/entries-exits/
echo   - http://192.168.1.129:8000/api/attendance-stats/
echo.
echo Управление контейнерами:
echo   - Просмотр логов: docker-compose logs -f
echo   - Остановка: docker-compose down
echo   - Перезапуск: docker-compose restart
echo.
pause




















