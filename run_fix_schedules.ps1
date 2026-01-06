# Скрипт для запуска check_and_fix_schedules.py в Docker контейнере

Write-Host "Запуск скрипта проверки и исправления графиков в Docker контейнере..." -ForegroundColor Cyan
Write-Host ""

# Получаем ID контейнера
$containerId = docker ps -q -f "name=hikvision_web"

if (-not $containerId) {
    Write-Host "ОШИБКА: Контейнер hikvision_web не найден!" -ForegroundColor Red
    Write-Host "Убедитесь, что контейнер запущен: docker-compose up -d" -ForegroundColor Yellow
    exit 1
}

Write-Host "Найден контейнер: $containerId" -ForegroundColor Green
Write-Host ""

# Копируем файл в контейнер (если его там нет)
Write-Host "Копирование файла в контейнер..." -ForegroundColor Yellow
docker cp check_and_fix_schedules.py "${containerId}:/app/check_and_fix_schedules.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Предупреждение: Не удалось скопировать файл. Возможно, он уже есть в контейнере." -ForegroundColor Yellow
    Write-Host ""
}

# Запускаем скрипт
Write-Host "Запуск скрипта..." -ForegroundColor Cyan
Write-Host ""

# Передаем все аргументы скрипту
$argsString = $args -join " "
docker exec -it $containerId python /app/check_and_fix_schedules.py $argsString

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "Скрипт выполнен успешно!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "Ошибка при выполнении скрипта!" -ForegroundColor Red
}

