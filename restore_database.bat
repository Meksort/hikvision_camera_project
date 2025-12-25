@echo off
chcp 65001 >nul 2>&1
echo ========================================
echo Restore PostgreSQL Database
echo ========================================
echo.

set BACKUP_DIR=%~dp0backups
set DB_NAME=hikvision_db

REM Автоматический поиск PostgreSQL
set PG_PATH=
if exist "C:\Program Files\PostgreSQL\18\bin\psql.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\18\bin
) else if exist "C:\Program Files\PostgreSQL\17\bin\psql.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\17\bin
) else if exist "C:\Program Files\PostgreSQL\16\bin\psql.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\16\bin
) else if exist "C:\Program Files\PostgreSQL\15\bin\psql.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\15\bin
) else if exist "C:\Program Files\PostgreSQL\14\bin\psql.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\14\bin
) else (
    REM Попробовать найти через PATH
    where psql >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        for /f "delims=" %%i in ('where psql') do (
            set PG_PATH=%%~dpi
            goto :found
        )
    )
    echo ERROR: PostgreSQL not found!
    echo Please install PostgreSQL or specify path manually.
    echo.
    set /p PG_PATH="Enter PostgreSQL bin path (e.g. C:\Program Files\PostgreSQL\18\bin): "
    if not exist "%PG_PATH%\psql.exe" (
        echo ERROR: Invalid PostgreSQL path!
        pause
        exit /b 1
    )
)

:found
if "%PG_PATH%"=="" (
    echo ERROR: Could not find PostgreSQL installation!
    pause
    exit /b 1
)

echo Found PostgreSQL at: %PG_PATH%
echo.

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
echo ========================================
echo IMPORTANT INFORMATION:
echo ========================================
echo This will restore ONLY the database: %DB_NAME%
echo Other databases on this server will NOT be affected.
echo.
echo Database: %DB_NAME%
echo Backup file: %BACKUP_FILE%
echo.
echo WARNING: This will REPLACE existing %DB_NAME% database!
echo All data in %DB_NAME% will be lost and replaced with backup.
echo.
echo ========================================
set /p CONFIRM="Are you sure? (yes/no): "

if /i not "%CONFIRM%"=="yes" (
    echo Cancelled.
    pause
    exit /b 0
)

echo.
echo Dropping existing database (if exists)...
"%PG_PATH%\psql.exe" -U postgres -c "DROP DATABASE IF EXISTS %DB_NAME%;"
if %ERRORLEVEL% NEQ 0 (
    echo WARNING: Could not drop database. It may not exist yet.
)

echo Creating new database...
"%PG_PATH%\psql.exe" -U postgres -c "CREATE DATABASE %DB_NAME%;"
if %ERRORLEVEL% NEQ 0 (
    echo ERROR: Could not create database!
    pause
    exit /b 1
)

echo Restoring from backup...
"%PG_PATH%\pg_restore.exe" -U postgres -h localhost -d %DB_NAME% -v "%BACKUP_FILE%"

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo Database restored successfully!
    echo ========================================
    echo.
    echo Note: Other databases on this server were NOT affected.
    echo Only %DB_NAME% database was restored.
) else (
    echo.
    echo ========================================
    echo ERROR: Restore failed!
    echo ========================================
    echo.
    echo Note: No other databases were affected by this error.
)

pause

