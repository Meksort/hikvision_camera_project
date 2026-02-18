# Скрипт для запуска import_employees.py в Docker контейнере

param(
    [Parameter(Mandatory=$true)]
    [string]$ExcelFile
)

Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host "ИМПОРТ СОТРУДНИКОВ ИЗ EXCEL ФАЙЛА" -ForegroundColor Cyan
Write-Host "=" * 80 -ForegroundColor Cyan
Write-Host ""

# Проверяем, существует ли файл
if (-not (Test-Path $ExcelFile)) {
    Write-Host "ОШИБКА: Файл не найден: $ExcelFile" -ForegroundColor Red
    exit 1
}

Write-Host "Файл для импорта: $ExcelFile" -ForegroundColor Green
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

# Получаем имя файла для копирования в контейнер
$fileName = Split-Path -Leaf $ExcelFile
$containerFilePath = "/app/$fileName"

# Копируем Excel файл в контейнер
Write-Host "Копирование Excel файла в контейнер..." -ForegroundColor Yellow
docker cp $ExcelFile "${containerId}:${containerFilePath}"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ОШИБКА: Не удалось скопировать файл в контейнер!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Файл успешно скопирован в контейнер: $containerFilePath" -ForegroundColor Green
Write-Host ""

# Копируем скрипт в контейнер (если его там нет)
Write-Host "Копирование скрипта import_employees.py в контейнер..." -ForegroundColor Yellow
docker cp import_employees.py "${containerId}:/app/import_employees.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ОШИБКА: Не удалось скопировать скрипт в контейнер!" -ForegroundColor Red
    exit 1
}

Write-Host "✓ Скрипт успешно скопирован" -ForegroundColor Green
Write-Host ""

# Запускаем скрипт
Write-Host "Запуск импорта..." -ForegroundColor Cyan
Write-Host ""

docker exec -it $containerId python /app/import_employees.py $containerFilePath

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "✓ Импорт выполнен успешно!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "✗ Ошибка при выполнении импорта!" -ForegroundColor Red
}



