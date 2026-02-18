@echo off
REM Скрипт для запуска import_employees.py в Docker контейнере

if "%~1"=="" (
    echo ОШИБКА: Укажите путь к Excel файлу
    echo.
    echo Использование: run_import_employees.bat ^<путь_к_excel_файлу^>
    echo.
    echo Пример:
    echo   run_import_employees.bat employee_import_template.xlsx
    exit /b 1
)

set EXCEL_FILE=%~1

REM Проверяем, существует ли файл
if not exist "%EXCEL_FILE%" (
    echo ОШИБКА: Файл не найден: %EXCEL_FILE%
    exit /b 1
)

echo ================================================================================
echo ИМПОРТ СОТРУДНИКОВ ИЗ EXCEL ФАЙЛА
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

REM Копируем Excel файл в контейнер
echo Копирование Excel файла в контейнер...
docker cp "%EXCEL_FILE%" "%CONTAINER_ID%:%CONTAINER_FILE_PATH%"

if errorlevel 1 (
    echo ОШИБКА: Не удалось скопировать файл в контейнер!
    exit /b 1
)

echo Файл успешно скопирован в контейнер: %CONTAINER_FILE_PATH%
echo.

REM Копируем скрипт в контейнер
echo Копирование скрипта import_employees.py в контейнер...
docker cp import_employees.py "%CONTAINER_ID%:/app/import_employees.py"

if errorlevel 1 (
    echo ОШИБКА: Не удалось скопировать скрипт в контейнер!
    exit /b 1
)

echo Скрипт успешно скопирован
echo.

REM Запускаем скрипт
echo Запуск импорта...
echo.

docker exec -it %CONTAINER_ID% python /app/import_employees.py %CONTAINER_FILE_PATH%

if errorlevel 1 (
    echo.
    echo Ошибка при выполнении импорта!
    exit /b 1
) else (
    echo.
    echo Импорт выполнен успешно!
)



