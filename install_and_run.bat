@echo off
title EOW Quant Engine v1.6
color 0A
setlocal enabledelayedexpansion

echo.
echo  ================================================
echo   EOW QUANT ENGINE  v1.6  --  Self-Evolving AI
echo   Paper Trading Mode  ^|  Auto-Optimized DNA
echo  ================================================
echo.

:: ── Base path (spaces + parentheses safe) ──────────────────────
set "BASE=%~dp0"
if "%BASE:~-1%"=="\" set "BASE=%BASE:~0,-1%"

:: Venv is placed at a SAFE SHORT PATH (no spaces, no parens)
:: This avoids venv creation failures caused by special chars in
:: the project folder name like "(ChatGPT)" or "V17.0(..."
set "VENV=C:\eow_venv"
set "VENV_PY=C:\eow_venv\Scripts\python.exe"

set "REDIS_DIR=%BASE%\data\redis"
set "REDIS_EXE=%BASE%\data\redis\redis-server.exe"
set "REDIS_CLI=%BASE%\data\redis\redis-cli.exe"
set "REDIS_CONF=%BASE%\data\redis\redis.conf"
set "REDIS_MODE=none"
set "PY_MINOR=0"
set "WARN_PYTHON=0"

:: ═══════════════════════════════════════════════════════════════
:: STEP 1 — Python check
:: ═══════════════════════════════════════════════════════════════
python --version >nul 2>&1
if errorlevel 1 goto :no_python
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set "PYVER=%%v"
echo  [OK] Python %PYVER% ready
goto :python_version_check

:no_python
echo  [X] Python nahi mila!
echo.
echo  Kripya Python 3.11 install karein:
echo  https://python.org/downloads/release/python-3119/
echo  Install karte waqt "Add Python to PATH" zaroor check karein.
echo.
pause
exit /b 1

:python_version_check
for /f "tokens=1,2 delims=." %%a in ("%PYVER%") do set "PY_MINOR=%%b"
if %PY_MINOR% GEQ 13 set "WARN_PYTHON=1"
if %WARN_PYTHON% EQU 0 goto :python_ok

echo.
echo  [!] WARNING: Python %PYVER% bahut naya hai!
echo      scipy aur kuch packages Python 3.13+ support nahi karte abhi.
echo      RECOMMENDED: Python 3.11 install karein:
echo      https://python.org/downloads/release/python-3119/
echo.
echo      Phir bhi continue karna chahte hain?
choice /C YN /N /M "  Y=Haan continue, N=Band karo: "
if errorlevel 2 goto :abort_python

:python_ok

:: ═══════════════════════════════════════════════════════════════
:: STEP 2 — Virtual environment at C:\eow_venv
:: ═══════════════════════════════════════════════════════════════
echo  [..] Setting up environment...
echo  [..] Venv location: %VENV%

:: If venv exists and python works, skip creation
if exist "%VENV_PY%" goto :venv_test

echo  [..] Venv ban raha hai C:\eow_venv par...
python -m venv "%VENV%"
if errorlevel 1 goto :venv_fail

:venv_test
"%VENV_PY%" --version >nul 2>&1
if errorlevel 1 goto :venv_corrupt

call "%VENV%\Scripts\activate.bat"
if errorlevel 1 goto :venv_fail
echo  [OK] Environment ready
goto :install_packages

:venv_corrupt
echo  [!] Venv corrupt hai — rebuild ho raha hai...
rd /s /q "%VENV%" >nul 2>&1
python -m venv "%VENV%"
if errorlevel 1 goto :venv_fail
call "%VENV%\Scripts\activate.bat"
if errorlevel 1 goto :venv_fail
echo  [OK] Environment ready (rebuilt)
goto :install_packages

:venv_fail
echo.
echo  [X] Virtual environment fail ho gaya!
echo.
echo  Possible reason: Python PATH mein koi aur Python hai.
echo  Check karein: where python
echo.
echo  Aapke system par python.exe ka path:
where python 2>nul
echo.
pause
exit /b 1

:: ═══════════════════════════════════════════════════════════════
:: STEP 3 — Install packages
::   Always use "%VENV_PY%" -m pip — never bare pip command.
::   Bare pip uses the pip launcher which breaks when multiple
::   Python versions are installed (e.g. Python 3.14 + 3.11).
:: ═══════════════════════════════════════════════════════════════
:install_packages
echo  [..] Installing packages (pehli baar 1-2 min lagenge)...
"%VENV_PY%" -m pip install --upgrade pip --no-cache-dir --quiet >nul 2>&1

if not exist "%BASE%\requirements.txt" goto :no_req_file
if %WARN_PYTHON% EQU 1 goto :filtered_install

"%VENV_PY%" -m pip install -r "%BASE%\requirements.txt" --no-cache-dir --quiet
goto :verify_packages

:filtered_install
echo  [!] Python %PYVER% -- scipy skip hoga (incompatible)
findstr /V /I "scipy" "%BASE%\requirements.txt" > "%TEMP%\eow_req_filtered.txt"
"%VENV_PY%" -m pip install -r "%TEMP%\eow_req_filtered.txt" --no-cache-dir --quiet
del "%TEMP%\eow_req_filtered.txt" >nul 2>&1
goto :verify_packages

:no_req_file
echo  [!] requirements.txt nahi mila -- core packages install ho rahe hain...

:verify_packages
"%VENV_PY%" -c "import uvicorn, fastapi, websockets" >nul 2>&1
if errorlevel 1 goto :retry_install
echo  [OK] All packages installed
goto :make_folders

:retry_install
echo  [..] Core packages retry ho rahe hain...
"%VENV_PY%" -m pip install fastapi "uvicorn[standard]" websockets httpx pydantic pydantic-settings loguru python-binance redis pandas numpy aiofiles apscheduler orjson python-dotenv psutil --no-cache-dir
if errorlevel 1 goto :pkg_fail
echo  [OK] All packages installed
goto :make_folders

:pkg_fail
echo  [X] Package installation fail ho gayi!
pause
exit /b 1

:: ═══════════════════════════════════════════════════════════════
:: STEP 4 — Create folders
:: ═══════════════════════════════════════════════════════════════
:make_folders
if not exist "%BASE%\data"         mkdir "%BASE%\data"
if not exist "%BASE%\data\exports" mkdir "%BASE%\data\exports"
if not exist "%BASE%\data\redis"   mkdir "%BASE%\data\redis"
echo  [OK] Data folders ready

:: ═══════════════════════════════════════════════════════════════
:: STEP 5 — Config file
:: ═══════════════════════════════════════════════════════════════
if exist "%BASE%\.env" goto :env_ok
if not exist "%BASE%\.env.template" goto :env_blank
copy "%BASE%\.env.template" "%BASE%\.env" >nul
echo  [OK] Config template se create hua
goto :env_ok

:env_blank
echo  [!] .env.template nahi mila -- blank .env ban raha hai
type nul > "%BASE%\.env"

:env_ok
echo  [OK] Config ready

:: ═══════════════════════════════════════════════════════════════
:: STEP 6 — Optimized DNA
:: ═══════════════════════════════════════════════════════════════
if exist "%BASE%\data\exports\optimized_dna.json" goto :dna_ok
if not exist "%BASE%\data\exports\optimized_dna.json.bak" goto :dna_missing
copy "%BASE%\data\exports\optimized_dna.json.bak" "%BASE%\data\exports\optimized_dna.json" >nul
echo  [OK] Optimized strategy DNA backup se restore hua
goto :dna_ok

:dna_missing
echo  [!] Koi optimized DNA nahi mila -- engine fresh start karega

:dna_ok
echo  [OK] Optimized strategy DNA ready

:: ═══════════════════════════════════════════════════════════════
:: STEP 7 — Redis Setup (Existing → Docker → Portable)
:: ═══════════════════════════════════════════════════════════════
echo.
echo  ================================================
echo   Redis Setup
echo  ================================================

:: 7a: Already running on 6379?
netstat -an 2>nul | findstr ":6379 " | findstr "LISTENING" >nul
if errorlevel 1 goto :check_docker
echo  [OK] Redis already port 6379 par chal raha hai
set "REDIS_MODE=existing"
goto :redis_verify

:: 7b: Docker?
:check_docker
echo  [..] Docker check ho raha hai...
docker info >nul 2>&1
if errorlevel 1 goto :use_portable
echo  [OK] Docker mila -- Docker Redis use hoga
set "REDIS_MODE=docker"
goto :redis_docker

:: 7c: Portable Redis
:use_portable
echo  [!] Docker nahi mila -- Portable Redis use hoga

:redis_portable
if exist "%REDIS_EXE%" goto :redis_portable_start

echo  [..] Portable Redis download ho raha hai (sirf ek baar)...
for %%d in ("%REDIS_DIR%") do set "REDIS_SHORT=%%~sd"

curl --version >nul 2>&1
if errorlevel 1 goto :download_ps
curl -L --silent --show-error -o "%REDIS_SHORT%\redis.zip" "https://github.com/microsoftarchive/redis/releases/download/win-3.2.100/Redis-x64-3.2.100.zip"
if errorlevel 1 goto :download_fail
goto :extract_redis

:download_ps
powershell -NoProfile -Command "[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://github.com/microsoftarchive/redis/releases/download/win-3.2.100/Redis-x64-3.2.100.zip' -OutFile '%REDIS_SHORT%\redis.zip' -UseBasicParsing"
if errorlevel 1 goto :download_fail

:extract_redis
echo  [..] Redis extract ho raha hai...
powershell -NoProfile -Command "Expand-Archive -Path '%REDIS_SHORT%\redis.zip' -DestinationPath '%REDIS_SHORT%\extracted' -Force"
if errorlevel 1 goto :extract_fail

for /r "%REDIS_DIR%\extracted" %%f in (redis-server.exe) do (
    if not exist "%REDIS_EXE%" copy "%%f" "%REDIS_EXE%" >nul
)
for /r "%REDIS_DIR%\extracted" %%f in (redis-cli.exe) do (
    if not exist "%REDIS_CLI%" copy "%%f" "%REDIS_CLI%" >nul
)
rd /s /q "%REDIS_DIR%\extracted" >nul 2>&1
del "%REDIS_SHORT%\redis.zip" >nul 2>&1

if not exist "%REDIS_EXE%" goto :redis_exe_missing
echo  [OK] Portable Redis download aur ready

:redis_portable_start
set "REDIS_MODE=portable"

if not exist "%REDIS_CONF%" (
    echo port 6379>                    "%REDIS_CONF%"
    echo bind 127.0.0.1>>              "%REDIS_CONF%"
    echo maxmemory 256mb>>             "%REDIS_CONF%"
    echo maxmemory-policy allkeys-lru>>"%REDIS_CONF%"
    echo save "">>                     "%REDIS_CONF%"
    echo loglevel warning>>            "%REDIS_CONF%"
    echo logfile "">>                  "%REDIS_CONF%"
    echo  [OK] Redis config bana
)

tasklist /FI "IMAGENAME eq redis-server.exe" 2>nul | findstr /I "redis-server.exe" >nul
if errorlevel 1 goto :start_portable_redis
echo  [OK] Portable Redis already chal raha hai
goto :redis_verify

:start_portable_redis
echo  [..] Portable Redis start ho raha hai...
start /B "" "%REDIS_EXE%" "%REDIS_CONF%"
timeout /t 3 /nobreak >nul
tasklist /FI "IMAGENAME eq redis-server.exe" 2>nul | findstr /I "redis-server.exe" >nul
if errorlevel 1 goto :portable_start_fail
echo  [OK] Portable Redis chal raha hai (background)
goto :redis_verify

:redis_docker
docker ps -a --format "{{.Names}}" 2>nul | findstr /X "eow-redis" >nul
if errorlevel 1 goto :create_container
echo  [OK] Redis container exists
goto :ensure_running

:create_container
echo  [..] Redis container nahi hai. Create ho raha hai...
docker run -d --name eow-redis -p 6379:6379 --restart always redis:alpine >nul
if errorlevel 1 goto :docker_fallback
echo  [OK] Redis Docker container ready
timeout /t 5 /nobreak >nul

:ensure_running
docker ps --format "{{.Names}}" 2>nul | findstr /X "eow-redis" >nul
if errorlevel 1 goto :start_container
echo  [OK] Redis container already running
goto :redis_verify

:start_container
echo  [..] Container start ho raha hai...
docker start eow-redis >nul
timeout /t 5 /nobreak >nul
goto :redis_verify

:redis_verify
echo  [..] Redis health check...

if "%REDIS_MODE%"=="docker" (
    docker exec eow-redis redis-cli ping > "%TEMP%\eow_rping.tmp" 2>&1
) else if "%REDIS_MODE%"=="portable" (
    "%REDIS_CLI%" -p 6379 ping > "%TEMP%\eow_rping.tmp" 2>&1
) else (
    if exist "%REDIS_CLI%" (
        "%REDIS_CLI%" -p 6379 ping > "%TEMP%\eow_rping.tmp" 2>&1
    ) else (
        redis-cli ping > "%TEMP%\eow_rping.tmp" 2>&1
    )
)

set /p REDIS_REPLY=<"%TEMP%\eow_rping.tmp"
del "%TEMP%\eow_rping.tmp" >nul 2>&1

echo %REDIS_REPLY% | findstr /I "PONG" >nul
if errorlevel 1 goto :redis_fail

if "%REDIS_MODE%"=="docker"   echo  [OK] Redis healthy  [Mode: Docker]
if "%REDIS_MODE%"=="portable" echo  [OK] Redis healthy  [Mode: Portable -- no Docker needed]
if "%REDIS_MODE%"=="existing" echo  [OK] Redis healthy  [Mode: Already running]

findstr /B "REDIS_URL=" "%BASE%\.env" >nul 2>&1
if errorlevel 1 (
    echo REDIS_URL=redis://127.0.0.1:6379/0>>"%BASE%\.env"
    echo  [OK] REDIS_URL .env mein add hua
) else (
    echo  [OK] REDIS_URL already configured
)

:: ═══════════════════════════════════════════════════════════════
:: STEP 8 — Launch Engine
:: ═══════════════════════════════════════════════════════════════
echo.
echo  ================================================
echo   Engine PAPER mode mein start ho raha hai...
echo   Dashboard: http://127.0.0.1:8000
echo.
echo   Browser mein khud khul jaayega.
echo   Band karne ke liye: Ctrl+C dabayein
echo  ================================================
echo.

"%VENV_PY%" "%BASE%\run.py" paper
if errorlevel 1 (
    echo.
    echo  [X] Engine error ke saath band hua.
    echo  Logs check karein.
)

if "%REDIS_MODE%"=="portable" (
    echo.
    echo  [..] Portable Redis band ho raha hai...
    taskkill /F /IM redis-server.exe >nul 2>&1
    echo  [OK] Redis band ho gaya
)

echo.
echo  Engine band ho gaya.
endlocal
pause
exit /b 0

:: ═══════════════════════════════════════════════════════════════
:: Error labels
:: ═══════════════════════════════════════════════════════════════
:abort_python
echo  Script band ho rahi hai. Python 3.11 install karein.
pause
exit /b 1

:download_fail
echo.
echo  [X] Redis download fail ho gaya!
echo  Option A: Docker Desktop install karein: https://www.docker.com/products/docker-desktop
echo  Option B: Manually download karein: https://github.com/microsoftarchive/redis/releases
echo            redis-server.exe + redis-cli.exe yahan rakhen: %REDIS_DIR%\
echo.
pause
exit /b 1

:extract_fail
echo  [X] Zip extract fail ho gaya!
pause
exit /b 1

:redis_exe_missing
echo  [X] redis-server.exe zip mein nahi mila!
pause
exit /b 1

:portable_start_fail
echo  [X] Portable Redis start nahi hua!
echo  Manually try karein: %REDIS_EXE%
pause
exit /b 1

:docker_fallback
echo  [!] Docker container create fail -- Portable Redis try kar raha hai...
set "REDIS_MODE=none"
goto :redis_portable

:redis_fail
echo  [X] Redis PONG nahi aaya! Got: [%REDIS_REPLY%]
if "%REDIS_MODE%"=="docker"   echo      Docker logs: docker logs eow-redis
if "%REDIS_MODE%"=="portable" echo      Manually chalayein: %REDIS_EXE%
pause
exit /b 1
