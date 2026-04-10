@echo off
setlocal EnableDelayedExpansion

:: ======================================================
::  EOW Quant Engine - Local to GitHub (with Backup)
::  Replaces remote repo contents; backs up local first.
::  venv/ and .git/ are always excluded.
:: ======================================================

:: --- CONFIGURATION ---
SET "BACKUP_DIR=D:\EOW_Backups"
SET "REPO_URL=https://github.com/SirVikas/EOW-Quant-Engine.git"

:: ======================================================
echo.
echo  ====================================================
echo   EOW QUANT ENGINE ^| GitHub Replace + Backup Tool
echo  ====================================================
echo.

:: --- PRE-FLIGHT: Check git is installed ---
where git >nul 2>&1
if errorlevel 1 (
    echo  [ERROR] Git is not installed or not in PATH.
    echo          Please install Git from https://git-scm.com and retry.
    echo.
    pause
    exit /b 1
)

:: ======================================================
echo  [STEP 1/4] SELECT YOUR PROJECT FOLDER
echo  ====================================================
echo.

:: --- STEP 1/4: SELECT YOUR PROJECT FOLDER ---
set "PS_CMD=powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$objShell = New-Object -ComObject Shell.Application; ^
    $objFolder = $objShell.BrowseForFolder(0, 'Select the EOW Quant Engine folder to upload', 0); ^
    if ($objFolder) { $objFolder.Self.Path }""

for /f "usebackq delims=" %%I in (`%PS_CMD%`) do set "SOURCE_PATH=%%I"

if not defined SOURCE_PATH (
    echo  [CANCELLED] No folder selected. Exiting.
    echo.
    pause
    exit /b 0
)
if "%SOURCE_PATH%"=="" (
    echo  [CANCELLED] No folder selected. Exiting.
    echo.
    pause
    exit /b 0
)

echo  Selected: "%SOURCE_PATH%"
cd /d "%SOURCE_PATH%"
if errorlevel 1 (
    echo  [ERROR] Could not change to selected directory.
    pause
    exit /b 1
)

:: ======================================================
echo.
echo  [STEP 2/4] CREATING LOCAL BACKUP (venv excluded^)
echo  ====================================================
echo.

if not exist "%BACKUP_DIR%" (
    mkdir "%BACKUP_DIR%"
    if errorlevel 1 (
        echo  [ERROR] Could not create backup directory: %BACKUP_DIR%
        pause
        exit /b 1
    )
)

:: Build a clean timestamp: YYYY-MM-DD_HH-MM-SS
:: Uses PowerShell for a reliable, filesystem-safe timestamp
for /f "usebackq delims=" %%T in (
    `Powershell -NoProfile -Command "Get-Date -Format 'yyyy-MM-dd_HH-mm-ss'"`
) do set "TIMESTAMP=%%T"

set "BACKUP_FILE=%BACKUP_DIR%\EOW_Backup_%TIMESTAMP%.zip"
echo  Destination : %BACKUP_FILE%
echo  Zipping     : please wait...
echo.

tar -a -c -f "%BACKUP_FILE%" --exclude=venv --exclude=.git .
if errorlevel 1 (
    echo.
    echo  [ERROR] Backup failed. Aborting to protect your data.
    pause
    exit /b 1
)

echo.
echo  [OK] Backup saved to: %BACKUP_FILE%

:: ======================================================
echo.
echo  [STEP 3/4] PREPARING GIT REPOSITORY
echo  ====================================================
echo.

:: Write a clean .gitignore (venv only; .git is managed by Git itself)
(
    echo venv/
    echo __pycache__/
    echo *.pyc
    echo *.pyo
    echo *.egg-info/
    echo dist/
    echo build/
    echo .env
) > .gitignore
echo  [OK] .gitignore written (venv and common Python artifacts excluded^).

:: Initialise repo if needed, or update remote URL
if not exist ".git" (
    echo  Initialising new Git repository...
    git init
    if errorlevel 1 ( echo  [ERROR] git init failed. & pause & exit /b 1 )
    git remote add origin %REPO_URL%
) else (
    git remote set-url origin %REPO_URL%
)

git branch -M main
if errorlevel 1 ( echo  [ERROR] Could not set branch to main. & pause & exit /b 1 )

:: Clear the index so deleted/moved files are handled cleanly
echo  Clearing Git index...
git rm -r --cached . >nul 2>&1

echo  Staging all files (venv will be ignored via .gitignore^)...
git add .
if errorlevel 1 ( echo  [ERROR] git add failed. & pause & exit /b 1 )

echo  Creating commit...
git commit -m "Complete replacement (venv filtered): %TIMESTAMP%"
if errorlevel 1 (
    echo.
    echo  [WARNING] git commit returned a non-zero exit code.
    echo           This may simply mean there were no changes to commit.
)

:: ======================================================
echo.
echo  [STEP 4/4] FORCE-PUSH TO GITHUB
echo  ====================================================
echo.
echo  WARNING: This will OVERWRITE the remote repository at:
echo           %REPO_URL%
echo.
set /p "CONFIRM=  Type YES to continue, or press Enter to abort: "
if /i not "%CONFIRM%"=="YES" (
    echo.
    echo  [ABORTED] Push cancelled by user. Your backup and local commit are intact.
    echo.
    pause
    exit /b 0
)

echo.
echo  Pushing to GitHub...
git push origin main --force
if errorlevel 1 (
    echo.
    echo  [ERROR] Push failed.
    echo         Common causes:
    echo           - Not authenticated (run: git credential-manager or gh auth login^)
    echo           - No network access
    echo           - Repository does not exist yet on GitHub
    echo.
    pause
    exit /b 1
)

:: ======================================================
echo.
echo  ====================================================
echo   SUCCESS! GitHub repository updated.
echo   - venv was excluded from the upload
echo   - Backup saved to: %BACKUP_FILE%
echo  ====================================================
echo.
pause
