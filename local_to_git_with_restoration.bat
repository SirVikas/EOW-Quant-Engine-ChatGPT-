@echo off
setlocal EnableDelayedExpansion

SET "REPO_URL=https://github.com/SirVikas/EOW-Quant-Engine.git"

:: [Previous Folder Selection and Zip Backup logic remains the same...]

echo ======================================================
echo STEP 3: SYNCING TO GITHUB WITH RESTORE POINT
echo ======================================================

cd /d "%SOURCE_PATH%"

if not exist ".git" (
    git init
    git remote add origin %REPO_URL%
)

:: Create a unique tag name using date and time
set "tag_name=backup_%date:~-4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%"
set "tag_name=%tag_name: =0%"

echo Creating a Restore Point (Tag) on GitHub: %tag_name%

git add .
git commit -m "Snapshot before replacement: %date% %time%"

:: Create a local tag and push it to GitHub
git tag -a %tag_name% -m "Restore point created on %date%"
git push origin %tag_name%

echo.
echo [SUCCESS] GitHub Restore Point Created: %tag_name%
echo Now proceeding with force update...
echo.

:: Perform the main force push
git push origin main --force 

echo ======================================================
echo OPERATION COMPLETE
echo ======================================================
pause