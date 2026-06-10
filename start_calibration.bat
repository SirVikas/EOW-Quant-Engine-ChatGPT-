@echo off
title PHOENIX - CALIBRATION MODE (BYPASS_ALL_GATES)
color 0E

echo.
echo  ================================================================
echo   PHOENIX  --  PHASE-2 CALIBRATION MODE
echo   PHX-CALIBRATION-PHASE-001
echo  ================================================================
echo.
echo   BYPASS_ALL_GATES=True  (quality gates OFF, lean gates 1-3 ON)
echo   Purpose: collect ETE samples to 500 for Phase-2 calibration.
echo.
echo   WARNING: This mode must NOT become the permanent operating
echo   mode. When "ETE Samples (cumulative)" reaches 500, stop the
echo   engine and launch with start_normal.bat instead.
echo.
echo   Verify after start:  python diagnose.py  (section 1)
echo       Gate Mode        BYPASS
echo  ================================================================
echo.

cd /d "%~dp0"
set "BYPASS_ALL_GATES=True"
python run.py

pause
