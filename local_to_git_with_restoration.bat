@echo off
setlocal EnableDelayedExpansion

SET "REPO_URL=https://github.com/SirVikas/EOW-Quant-Engine.git"

:: Step 1: Drive and Path (Aapke directory ke hisab se)
D:
cd "D:\EOW Quant Engine V14.0\eow_quant_engine_FINAL_v2.2\eow_quant_engine"

echo ======================================================
echo STEP 3: SYNCING TO GITHUB (Logic Only - Data Protected)
echo ======================================================

if not exist ".git" (
    git init
    git remote add origin %REPO_URL%
)

:: [IMPORTANT] Private assets ko stage hone se rokna
:: Taaki aapka balance aur keys upload na hon
git rm -r --cached .env data/ venv/ reports_for_analyzation/ 2>nul

:: Unique tag name for restore point
set "tag_name=logic_backup_%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%"
set "tag_name=%tag_name: =0%"

echo Creating a Logic Restore Point: %tag_name%

:: Sirf logic files ko add karna
git add .
:: Data folders ko specifically un-stage karna (Double Safety)
git reset data/ .env venv/ reports_for_analyzation/ 2>nul

git commit -m "System Logic Backup: %date% %time%" 

:: Push Tag and Logic
git tag -a %tag_name% -m "Logic restore point created on %date%"
git push origin %tag_name%
git push origin main --force [cite: 9]

echo ======================================================
echo SUCCESS: Logic Uploaded. Private Data Kept Local. 
echo ======================================================
pause