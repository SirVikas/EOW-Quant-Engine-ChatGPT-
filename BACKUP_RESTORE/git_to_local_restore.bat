@echo off
TITLE Git Restore Tool
SET "GIT_SHELL=C:\Program Files\Git\bin\sh.exe"

IF NOT EXIST "%GIT_SHELL%" (
    echo Error: Git for Windows nahi mila!
    pause
    exit
)

for /f "usebackq delims=" %%I in (`powershell -Command "Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.Interaction]::InputBox('Enter GitHub Repo URL to Restore:', 'GitHub Restore')"`) do set "REPO_URL=%%I"
if "%REPO_URL%"=="" exit

for /f "usebackq delims=" %%I in (`powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.FolderBrowserDialog; if($f.ShowDialog() -eq 'OK'){$f.SelectedPath}"`) do set "TARGET_DIR=%%I"
if "%TARGET_DIR%"=="" exit

"%GIT_SHELL%" -c "cd '%TARGET_DIR%'; if [ -d '.git' ]; then git pull origin main; else git clone '%REPO_URL%' .; fi"

powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Restore Complete!')"
pause