@echo off
REM Скрипт для копирования check_and_fix_schedules.py в Docker контейнер

echo Копирование check_and_fix_schedules.py в контейнер...
docker cp check_and_fix_schedules.py 99e80b98a056:/app/check_and_fix_schedules.py

if %ERRORLEVEL% EQU 0 (
    echo Файл успешно скопирован!
    echo Теперь можно запустить скрипт в контейнере:
    echo docker exec -it 99e80b98a056 python /app/check_and_fix_schedules.py
) else (
    echo Ошибка при копировании файла!
    echo Убедитесь, что:
    echo   1. Docker запущен
    echo   2. Контейнер 99e80b98a056 существует и запущен
    echo   3. Файл check_and_fix_schedules.py существует в текущей директории
)

pause

