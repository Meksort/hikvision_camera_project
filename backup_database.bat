@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Backup PostgreSQL Database
echo ========================================
echo.

set BACKUP_DIR=%~dp0backups
set DB_NAME=hikvision_db
set DATE=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set DATE=%DATE: =0%

mkdir "%BACKUP_DIR%" 2>nul

echo Creating backup...
"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" -U postgres -h localhost -d %DB_NAME% -F c -f "%BACKUP_DIR%\hikvision_db_%DATE%.dump"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Backup created successfully!
    echo Location: %BACKUP_DIR%\hikvision_db_%DATE%.dump
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ERROR: Backup failed!
    echo ========================================
)

pause

