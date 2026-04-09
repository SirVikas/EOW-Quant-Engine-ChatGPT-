@echo off
TITLE Emergency Restore System - EOW Quant Engine
setlocal EnableDelayedExpansion

:: --- CONFIGURATION ---
SET "BACKUP_DIR=D:\EOW_Backups"

echo ======================================================
echo          EMERGENCY RESTORE SYSTEM (LOCAL BACKUP)
echo ======================================================

:: Step 1: Select the folder where you want to restore the data
set "PS_CMD=Powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$objShell = New-Object -ComObject Shell.Application; ^
    $objFolder = $objShell.BrowseForFolder(0, 'Select the folder to RESTORE into', 0); ^
    if ($objFolder) { $objFolder.Self.Path }""

for /f "usebackq delims=" %%I in (`%PS_CMD%`) do set "RESTORE_PATH=%%I"

if "%RESTORE_PATH%"=="" (
    echo ERROR: No folder selected. Restore cancelled.
    pause
    exit /b
)

:: Step 2: Find the latest backup file in the backup directory
cd /d "%BACKUP_DIR%"
for /f "delims=" %%F in ('dir /b /a-d /o-d "EOW_Backup_*.zip"') do (
    set "LATEST_BACKUP=%%F"
    goto :found
)

:found
if "%LATEST_BACKUP%"=="" (
    echo ERROR: No backup files found in %BACKUP_DIR%
    pause
    exit /b
)

echo.
echo [FOUND] Latest Backup: %LATEST_BACKUP%
echo [TARGET] Restore To  : %RESTORE_PATH%
echo.
set /p "CONFIRM=Are you sure you want to overwrite files in the target folder? (Y/N): "
if /i not "%CONFIRM%"=="Y" exit /b

:: Step 3: Perform Restore (Extract Zip)
echo.
echo Restoring files... please wait...
tar -x -f "%BACKUP_DIR%\%LATEST_BACKUP%" -C "%RESTORE_PATH%"

echo.
echo ======================================================
echo SUCCESS: System restored from local backup.
echo Note: Your local 'venv' was not in the backup, 
echo so it remains as it was in the target folder.
echo ======================================================
pause