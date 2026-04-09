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
echo STEP 2: CREATING LOCAL BACKUP (EXCLUDING VENV)
echo ======================================================
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"
set "t=%date%_%time%"
set "t=%t:/=-%"
set "t=%t::=-%"
set "t=%t: =_%

:: [UPDATED] Create zip, strictly excluding venv and .git
echo Zipping files to %BACKUP_DIR%...
tar -a -c -f "%BACKUP_DIR%\EOW_Backup_%t%.zip" --exclude=venv --exclude=.git .
echo Backup Complete.

echo.
echo ======================================================
echo STEP 3: PREPARING GITHUB (FILTERING VENV)
echo ======================================================

:: [NEW] Create or Update .gitignore to ensure venv is NEVER uploaded
echo venv/ > .gitignore
echo .git/ >> .gitignore
echo [INFO] .gitignore updated to filter VENV folder.

:: Force Initialize if .git is missing or wrong
if not exist ".git" (
    echo Initializing new Git repository...
    git init
    git remote add origin %REPO_URL%
) else (
    git remote set-url origin %REPO_URL%
)

git branch -M main

echo Cleaning local Git index...
git rm -r --cached . >nul 2>&1

echo Staging files (VENV will be ignored)...
:: [INFO] 'git add .' will now respect the .gitignore file we created
git add .

echo Creating replacement commit...
git commit -m "Complete Replacement (VENV Filtered): %date% %time%"

echo.
echo Pushing to GitHub (Overwriting Online Files)...
git push origin main --force

echo.
echo ======================================================
echo SUCCESS: GitHub updated. VENV folder was filtered out.
echo ======================================================
pause