@echo off
chcp 65001 >nul
echo Проверка данных за 20 и 21 декабря для сотрудника "Абай Нурлан"
echo.

REM Проверяем, запущен ли Docker
docker ps >nul 2>&1
if %errorlevel% == 0 (
    echo Запуск через Docker...
    docker-compose exec web python check_employee_dec_20_21.py
) else (
    echo Запуск локально...
    python check_employee_dec_20_21.py
)

pause

