@echo off
TITLE GitHub to Local Sync - VENV Protector

:: Step 1: Switch to the correct drive
D:

:: Step 2: Navigate to your specific local directory
cd "D:\EOW Quant Engine V14.0\eow_quant_engine_FINAL_v2.2\eow_quant_engine"

echo ======================================================
echo    SAFE UPDATE FROM GITHUB (Protecting Local VENV)
echo ======================================================

:: [VENV PROTECTION CHECK]
:: This step confirms the VENV folder exists before doing any Git operation
if exist "venv" (
    echo [SAFEGUARD] Local 'venv' folder detected. 
    echo [SAFEGUARD] Git will not touch this folder as it is ignored.
) else (
    echo [WARNING] No 'venv' found. You may need to recreate it later.
)

:: Step 3: Fetch updates
echo.
echo Fetching latest code...
git fetch origin main

:: Step 4: Pull changes
:: 'git pull' only updates files that are tracked in the repository.
:: Since 'venv' is in .gitignore, it remains untouched on your hard drive. [cite: 8]
git pull origin main

echo.
echo ======================================================
echo    SUCCESS: Your code is updated!
echo    Your local 'venv' folder was NOT deleted or modified.
echo ======================================================
pause