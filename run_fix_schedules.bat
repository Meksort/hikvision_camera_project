@echo off
REM Скрипт для запуска check_and_fix_schedules.py в Docker контейнере

echo Запуск скрипта проверки и исправления графиков в Docker контейнере...
echo.

REM Получаем ID контейнера
for /f "tokens=*" %%i in ('docker ps -q -f "name=hikvision_web"') do set CONTAINER_ID=%%i

if "%CONTAINER_ID%"=="" (
    echo ОШИБКА: Контейнер hikvision_web не найден!
    echo Убедитесь, что контейнер запущен: docker-compose up -d
    pause
    exit /b 1
)

echo Найден контейнер: %CONTAINER_ID%
echo.

REM Копируем файл в контейнер (если его там нет)
echo Копирование файла в контейнер...
docker cp check_and_fix_schedules.py %CONTAINER_ID%:/app/check_and_fix_schedules.py

if %ERRORLEVEL% NEQ 0 (
    echo Предупреждение: Не удалось скопировать файл. Возможно, он уже есть в контейнере.
    echo.
)

REM Запускаем скрипт
echo Запуск скрипта...
echo.
docker exec -it %CONTAINER_ID% python /app/check_and_fix_schedules.py %*

if %ERRORLEVEL% EQU 0 (
    echo.
    echo Скрипт выполнен успешно!
) else (
    echo.
    echo Ошибка при выполнении скрипта!
)

pause

