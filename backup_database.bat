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

REM Автоматический поиск PostgreSQL
set PG_PATH=
if exist "C:\Program Files\PostgreSQL\18\bin\pg_dump.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\18\bin
) else if exist "C:\Program Files\PostgreSQL\17\bin\pg_dump.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\17\bin
) else if exist "C:\Program Files\PostgreSQL\16\bin\pg_dump.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\16\bin
) else if exist "C:\Program Files\PostgreSQL\15\bin\pg_dump.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\15\bin
) else if exist "C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" (
    set PG_PATH=C:\Program Files\PostgreSQL\14\bin
) else (
    REM Попробовать найти через PATH
    where pg_dump >nul 2>&1
    if %ERRORLEVEL% EQU 0 (
        for /f "delims=" %%i in ('where pg_dump') do (
            set PG_PATH=%%~dpi
            goto :found_backup
        )
    )
    echo ERROR: PostgreSQL not found!
    echo Please install PostgreSQL or specify path manually.
    echo.
    set /p PG_PATH="Enter PostgreSQL bin path (e.g. C:\Program Files\PostgreSQL\18\bin): "
    if not exist "%PG_PATH%\pg_dump.exe" (
        echo ERROR: Invalid PostgreSQL path!
        pause
        exit /b 1
    )
)

:found_backup
if "%PG_PATH%"=="" (
    echo ERROR: Could not find PostgreSQL installation!
    pause
    exit /b 1
)

echo Found PostgreSQL at: %PG_PATH%
echo.
echo Creating backup...
"%PG_PATH%\pg_dump.exe" -U postgres -h localhost -d %DB_NAME% -F c -f "%BACKUP_DIR%\hikvision_db_%DATE%.dump"

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

