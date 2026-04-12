@echo off
TITLE Git Backup Tool
SET "GIT_SHELL=C:\Program Files\Git\bin\sh.exe"

IF NOT EXIST "%GIT_SHELL%" (
    echo Error: Git for Windows nahi mila! 
    pause
    exit
)

:: PowerShell se rasta puchne ka naya aur saaf tareeka
for /f "usebackq delims=" %%I in (`powershell -Command "Add-Type -AssemblyName System.Windows.Forms; $f = New-Object System.Windows.Forms.FolderBrowserDialog; if($f.ShowDialog() -eq 'OK'){$f.SelectedPath}"`) do set "LOCAL_PATH=%%I"
if "%LOCAL_PATH%"=="" exit

for /f "usebackq delims=" %%I in (`powershell -Command "Add-Type -AssemblyName Microsoft.VisualBasic; [Microsoft.VisualBasic.Interaction]::InputBox('Enter Target GitHub Repo URL:', 'GitHub Backup', 'https://github.com/')"`) do set "REPO_URL=%%I"
if "%REPO_URL%"=="" exit

:: Bash commands ko execute karna
"%GIT_SHELL%" -c "cd '%LOCAL_PATH%'; if [ ! -f '.gitignore' ]; then echo 'venv/' > .gitignore; echo '.venv/' >> .gitignore; echo '__pycache__/' >> .gitignore; fi; if [ ! -d '.git' ]; then git init; fi; git add .; git commit -m 'Backup: $(date)'; git branch -M main; git remote add origin '%REPO_URL%' 2>/dev/null || git remote set-url origin '%REPO_URL%'; git push -u origin main --force"

powershell -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('Backup Successful!')"
pause