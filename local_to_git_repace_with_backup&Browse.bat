@echo off
setlocal EnableDelayedExpansion

:: --- CONFIGURATION ---
SET "BACKUP_DIR=D:\EOW_Backups"
SET "REPO_URL=https://github.com/SirVikas/EOW-Quant-Engine.git"

echo ======================================================
echo STEP 1: SELECT YOUR PROJECT FOLDER
echo ======================================================

:: Use PowerShell to open the folder browser
set "PS_CMD=Powershell -NoProfile -ExecutionPolicy Bypass -Command ^
    "$objShell = New-Object -ComObject Shell.Application; ^
    $objFolder = $objShell.BrowseForFolder(0, 'Select the EOW Quant Engine folder to upload', 0); ^
    if ($objFolder) { $objFolder.Self.Path }""

for /f "usebackq delims=" %%I in (`%PS_CMD%`) do set "SOURCE_PATH=%%I"

:: Check if user cancelled
if "%SOURCE_PATH%"=="" (
    echo.
    echo ERROR: No folder selected. Operation cancelled.
    pause
    exit /b
)

echo Selected Folder: "%SOURCE_PATH%"
cd /d "%SOURCE_PATH%"

echo.
echo ======================================================
echo STEP 2: CREATING LOCAL BACKUP (ZIP)
echo ======================================================
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
set "t=%date%_%time%"
set "t=%t:/=-%"
set "t=%t::=-%"
set "t=%t: =_%

:: Create zip, excluding venv to save time/space
echo Zipping files to %BACKUP_DIR%...
tar -a -c -f "%BACKUP_DIR%\EOW_Backup_%t%.zip" --exclude=venv --exclude=.git .
echo Backup Complete.

echo.
echo ======================================================
echo STEP 3: REPLACING GITHUB REPOSITORY
echo ======================================================

:: Force Initialize if .git is missing or wrong
if not exist ".git" (
    echo Initializing new Git repository...
    git init
    git remote add origin %REPO_URL%
) else (
    :: Ensure the remote URL is correct even if folder changed
    git remote set-url origin %REPO_URL%
)

git branch -M main

echo Cleaning local Git index...
git rm -r --cached . >nul 2>&1

echo Staging all files from selected folder...
git add .

echo Creating replacement commit...
git commit -m "Complete Replacement from Browse: %date% %time%"

echo.
echo Pushing to GitHub (Overwriting Online Files)...
git push origin main --force

echo.
echo ======================================================
echo SUCCESS: GitHub matches your local folder exactly.
echo ======================================================
pause