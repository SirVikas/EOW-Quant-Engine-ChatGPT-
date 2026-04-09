@echo off
TITLE GitHub to Local Sync - EOW Quant Engine

:: Step 1: Switch to the correct drive
D:

:: Step 2: Navigate to your specific local directory
cd "D:\EOW Quant Engine V14.0\eow_quant_engine_FINAL_v2.2\eow_quant_engine"

echo ======================================================
echo    SYNCING FROM: https://github.com/SirVikas/EOW-Quant-Engine
echo ======================================================

:: Step 3: Check if the directory is a Git repository
if not exist ".git" (
    echo [ERROR] This folder is not initialized with Git.
    echo Please run 'git init' and 'git remote add origin' first.
    pause
    exit
)

:: Step 4: Pull the latest changes from GitHub
:: Note: Defaulting to 'main'. Change to 'master' if your repo uses it.
git pull origin main

echo.
echo ======================================================
echo    UPDATE COMPLETE: Local files are now in sync.
echo    Note: 'venv' folder remains untouched.
echo ======================================================
pause