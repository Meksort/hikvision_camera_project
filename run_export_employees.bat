@echo off
REM Скрипт для запуска export_employees.py в Docker контейнере

if "%~1"=="" (
    echo ОШИБКА: Укажите путь к Excel файлу для экспорта
    echo.
    echo Использование: run_export_employees.bat ^<путь_к_excel_файлу^> [подразделение_id]
    echo.
    echo Примеры:
    echo   run_export_employees.bat employees_export.xlsx
    echo   run_export_employees.bat employees_export.xlsx 1
    exit /b 1
)

set EXCEL_FILE=%~1
set DEPARTMENT_ID=%~2

echo ================================================================================
echo ЭКСПОРТ СОТРУДНИКОВ В EXCEL ФАЙЛ ИЗ DOCKER КОНТЕЙНЕРА
echo ================================================================================
echo.

REM Получаем ID контейнера
for /f "tokens=*" %%i in ('docker ps -q -f "name=hikvision_web"') do set CONTAINER_ID=%%i

if "%CONTAINER_ID%"=="" (
    echo ОШИБКА: Контейнер hikvision_web не найден!
    echo Убедитесь, что контейнер запущен: docker-compose up -d
    exit /b 1
)

echo Найден контейнер: %CONTAINER_ID%
echo.

REM Получаем имя файла
for %%F in ("%EXCEL_FILE%") do set FILE_NAME=%%~nxF
set CONTAINER_FILE_PATH=/app/%FILE_NAME%

REM Копируем скрипт в контейнер
echo Копирование скрипта export_employees.py в контейнер...
docker cp export_employees.py "%CONTAINER_ID%:/app/export_employees.py"

if errorlevel 1 (
    echo ОШИБКА: Не удалось скопировать скрипт в контейнер!
    exit /b 1
)

echo Скрипт успешно скопирован
echo.

REM Формируем команду для запуска
set EXPORT_CMD=python /app/export_employees.py %CONTAINER_FILE_PATH%
if not "%DEPARTMENT_ID%"=="" (
    set EXPORT_CMD=%EXPORT_CMD% %DEPARTMENT_ID%
)

REM Запускаем скрипт в контейнере
echo Запуск экспорта...
echo.

docker exec -it %CONTAINER_ID% %EXPORT_CMD%

if errorlevel 1 (
    echo.
    echo Ошибка при выполнении экспорта!
    exit /b 1
)

echo.
echo Экспорт выполнен успешно!
echo.

REM Копируем созданный файл обратно на хост
echo Копирование файла из контейнера на хост...
docker cp "%CONTAINER_ID%:%CONTAINER_FILE_PATH%" "%EXCEL_FILE%"

if errorlevel 1 (
    echo ПРЕДУПРЕЖДЕНИЕ: Не удалось скопировать файл из контейнера!
    echo Файл может находиться в контейнере по пути: %CONTAINER_FILE_PATH%
    exit /b 1
)

echo Файл успешно скопирован: %EXCEL_FILE%
echo.
echo [OK] Экспорт завершен успешно!
