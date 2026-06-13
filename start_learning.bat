@echo off
title PHOENIX - LEARNING MODE (BYPASS_ALL_GATES)
color 0B

echo.
echo  ================================================================
echo   PHOENIX  --  RL LEARNING MODE (post-calibration)
echo  ================================================================
echo.
echo   BYPASS_ALL_GATES=True  (quality gates OFF, lean gates 1-3 ON)
echo.
echo   Purpose: maximise trade throughput so the RL brain keeps
echo   learning. Use this AFTER Phase-2 calibration is complete
echo   (ETE samples >= 500). The lean gate (SL distance / RR / fee
echo   economy) stays active as the quality filter; toxic contexts
echo   are still blocked.
echo.
echo   v1.90.0: the PAPER_SPEED RSI governor now honours BYPASS, so
echo   this mode actually trades instead of starving on RSI blocks.
echo.
echo   NOTE: expectancy is still negative — this trades for learning
echo   data, not profit. Switch to start_normal.bat for capital-
echo   quality (GATED) operation.
echo.
echo   Verify after start:  python diagnose.py  (section 1)
echo       Gate Mode        BYPASS
echo  ================================================================
echo.

cd /d "%~dp0"
set "BYPASS_ALL_GATES=True"
python run.py

pause
