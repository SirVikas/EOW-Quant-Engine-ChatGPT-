@echo off
title PHOENIX - NORMAL GATED MODE
color 0A

echo.
echo  ================================================================
echo   PHOENIX  --  NORMAL OPERATING MODE (full quality-gate stack)
echo  ================================================================
echo.
echo   BYPASS_ALL_GATES=False  (all gates active)
echo.
echo   Verify after start:  python diagnose.py  (section 1)
echo       Gate Mode        GATED
echo  ================================================================
echo.

cd /d "%~dp0"
set "BYPASS_ALL_GATES=False"
python run.py

pause
