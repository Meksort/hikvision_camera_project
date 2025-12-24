@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Restore PostgreSQL Database
echo ========================================
echo.

set BACKUP_DIR=%~dp0backups
set DB_NAME=hikvision_db

echo Available backups:
dir /b "%BACKUP_DIR%\*.dump" 2>nul
echo.

set /p BACKUP_FILE="Enter backup filename (or full path): "

if not exist "%BACKUP_FILE%" (
    if not exist "%BACKUP_DIR%\%BACKUP_FILE%" (
        echo ERROR: File not found!
        pause
        exit /b 1
    ) else (
        set BACKUP_FILE=%BACKUP_DIR%\%BACKUP_FILE%
    )
)

echo.
echo WARNING: This will replace existing database!
echo Database: %DB_NAME%
echo Backup file: %BACKUP_FILE%
echo.
set /p CONFIRM="Are you sure? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Dropping existing database (if exists)...
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "DROP DATABASE IF EXISTS %DB_NAME%;"

echo Creating new database...
"C:\Program Files\PostgreSQL\18\bin\psql.exe" -U postgres -c "CREATE DATABASE %DB_NAME%;"

echo Restoring from backup...
"C:\Program Files\PostgreSQL\18\bin\pg_restore.exe" -U postgres -h localhost -d %DB_NAME% -v "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Database restored successfully!
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ERROR: Restore failed!
    echo ========================================
)

pause

