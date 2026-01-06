# Скрипт для копирования check_and_fix_schedules.py в Docker контейнер

Write-Host "Копирование check_and_fix_schedules.py в контейнер..." -ForegroundColor Yellow

$containerId = "99e80b98a056"
$sourceFile = "check_and_fix_schedules.py"
$destPath = "/app/check_and_fix_schedules.py"

if (-not (Test-Path $sourceFile)) {
    Write-Host "ОШИБКА: Файл $sourceFile не найден в текущей директории!" -ForegroundColor Red
    Write-Host "Текущая директория: $(Get-Location)" -ForegroundColor Yellow
    exit 1
}

try {
    docker cp $sourceFile "${containerId}:${destPath}"
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Файл успешно скопирован в контейнер!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Теперь в контейнере выполните:" -ForegroundColor Cyan
        Write-Host "  python /app/check_and_fix_schedules.py" -ForegroundColor White
        Write-Host ""
        Write-Host "Или с параметрами:" -ForegroundColor Cyan
        Write-Host "  python /app/check_and_fix_schedules.py --check-only" -ForegroundColor White
        Write-Host "  python /app/check_and_fix_schedules.py --create-only" -ForegroundColor White
    } else {
        Write-Host "ОШИБКА при копировании файла!" -ForegroundColor Red
        Write-Host "Убедитесь, что:" -ForegroundColor Yellow
        Write-Host "  1. Docker запущен" -ForegroundColor Yellow
        Write-Host "  2. Контейнер $containerId существует и запущен" -ForegroundColor Yellow
        Write-Host "  3. Файл $sourceFile существует в текущей директории" -ForegroundColor Yellow
    }
} catch {
    Write-Host "ОШИБКА: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "Проверьте, что Docker установлен и доступен в PATH" -ForegroundColor Yellow
}

