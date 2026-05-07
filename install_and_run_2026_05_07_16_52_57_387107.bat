@echo off
title EOW Quant Engine — v1.6
color 0A
setlocal enabledelayedexpansion

echo.
echo  ================================================
echo   EOW QUANT ENGINE  v1.6  —  Self-Evolving AI
echo   Paper Trading Mode  ^|  Auto-Optimized DNA
echo  ================================================
echo.

:: ── Step 1: Python check ─────────────────────────────────────────────────────
python --version >nul 2>&1
if errorlevel 1 (
    echo  [X] Python nahi mila!
    echo.
    echo  Kripya Python 3.11+ install karein:
    echo  https://python.org/downloads
    echo.
    echo  Install karte waqt "Add Python to PATH" zaroor check karein.
    echo.
    pause
    exit /b 1
)
for /f "tokens=2" %%v in ('python --version 2^>^&1') do set PYVER=%%v
echo  [OK] Python %PYVER% ready

:: ── Step 2: Virtual environment ──────────────────────────────────────────────
echo  [..] Setting up environment...
if not exist venv (
    python -m venv venv >nul 2>&1
)
call venv\Scripts\activate.bat
echo  [OK] Environment ready

:: ── Step 3: Install packages ─────────────────────────────────────────────────
echo  [..] Installing packages (1-2 minutes on first run)...
python -m pip install --upgrade pip --no-cache-dir --quiet >nul 2>&1
pip install -r requirements.txt --no-cache-dir --quiet >nul 2>&1

:: Verify the most important package
python -c "import uvicorn, fastapi, websockets" >nul 2>&1
if errorlevel 1 (
    echo  [..] Retrying package install...
    pip install fastapi "uvicorn[standard]" websockets httpx pydantic pydantic-settings ^
        loguru python-binance redis pandas numpy aiofiles apscheduler orjson ^
        python-dotenv psutil --no-cache-dir --quiet
)
echo  [OK] All packages installed

:: ── Step 4: Create folders ────────────────────────────────────────────────────
if not exist data mkdir data
if not exist data\exports mkdir data\exports
echo  [OK] Data folders ready

:: ── Step 5: Config file ───────────────────────────────────────────────────────
if not exist .env (
    copy .env.template .env >nul
)
echo  [OK] Config ready

:: ── Step 6: Copy optimized DNA (so engine starts with good parameters) ────────
if not exist data\exports\optimized_dna.json (
    if exist data\exports\optimized_dna.json.bak (
        copy data\exports\optimized_dna.json.bak data\exports\optimized_dna.json >nul
    )
)
echo  [OK] Optimized strategy DNA ready

:: ── Launch ───────────────────────────────────────────────────────────────────
echo.
echo  ================================================
echo   Starting engine in PAPER mode...
echo   Dashboard: http://127.0.0.1:8000
echo.
echo   Browser mein khud khul jaayega.
echo   Band karne ke liye: Ctrl+C dabayein
echo  ================================================
echo.

python run.py paper

echo.
echo  Engine band ho gaya.
pause
