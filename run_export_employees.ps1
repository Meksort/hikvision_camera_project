# Скрипт для запуска export_employees.py в Docker контейнере

param(
    [Parameter(Mandatory=$true)]
    [string]$ExcelFile,
    
    [Parameter(Mandatory=$false)]
    [int]$DepartmentId
)

Write-Host ("=" * 80) -ForegroundColor Cyan
Write-Host "ЭКСПОРТ СОТРУДНИКОВ В EXCEL ФАЙЛ ИЗ DOCKER КОНТЕЙНЕРА" -ForegroundColor Cyan
Write-Host ("=" * 80) -ForegroundColor Cyan
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

# Получаем имя файла для пути в контейнере
$fileName = Split-Path -Leaf $ExcelFile
$containerFilePath = "/app/$fileName"

# Копируем скрипт в контейнер
Write-Host "Копирование скрипта export_employees.py в контейнер..." -ForegroundColor Yellow
docker cp export_employees.py "${containerId}:/app/export_employees.py"

if ($LASTEXITCODE -ne 0) {
    Write-Host "ОШИБКА: Не удалось скопировать скрипт в контейнер!" -ForegroundColor Red
    exit 1
}

Write-Host "[OK] Скрипт успешно скопирован" -ForegroundColor Green
Write-Host ""

# Формируем команду для запуска
$exportCmd = "python /app/export_employees.py $containerFilePath"
if ($DepartmentId) {
    $exportCmd += " $DepartmentId"
}

# Запускаем скрипт в контейнере
Write-Host "Запуск экспорта..." -ForegroundColor Cyan
Write-Host ""

docker exec -it $containerId $exportCmd

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Ошибка при выполнении экспорта!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[OK] Экспорт выполнен успешно!" -ForegroundColor Green
Write-Host ""

# Копируем созданный файл обратно на хост
Write-Host "Копирование файла из контейнера на хост..." -ForegroundColor Yellow
docker cp "${containerId}:${containerFilePath}" $ExcelFile

if ($LASTEXITCODE -ne 0) {
    Write-Host "[WARNING] Не удалось скопировать файл из контейнера!" -ForegroundColor Yellow
    Write-Host "Файл может находиться в контейнере по пути: $containerFilePath" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Файл успешно скопирован: $ExcelFile" -ForegroundColor Green
Write-Host ""
Write-Host "[OK] Экспорт завершен успешно!" -ForegroundColor Green
