@echo off
title PHOENIX - XTE OBSERVATION CAMPAIGN (REAL EVIDENCE)
color 0A

echo.
echo  ================================================================
echo   PHOENIX  --  XTE OBSERVATION CAMPAIGN
echo   FTD-094A  --  REAL EVIDENCE COLLECTION (Phase 1)
echo  ================================================================
echo.
echo   XTE_OBSERVE_ENABLED=True         (score open positions, observe-only)
echo   XTE_OBSERVE_PATH_ENABLED=True    (per-tick path for path-accurate proof)
echo   EXIT_COORDINATOR_SHADOW_ENABLED=True   (exit-authority parity audit)
echo   BYPASS_ALL_GATES=True            (accelerate to 500 closed trades)
echo.
echo   Observe-only: this changes NO trade/SL/TP decision. It records
echo   one XTE record per closed trade toward the 500-sample target.
echo.
echo   WARNING: temporary calibration mode (like start_calibration.bat).
echo   When the campaign completes, stop and relaunch start_normal.bat.
echo.
echo   Monitor :  GET /api/governance/lifecycle   (campaign progress)
echo   Verdict :  GET /api/truth/xte/validation   (after 500 samples)
echo   Runbook :  XTE_CAMPAIGN_OPERATIONS_RUNBOOK.md
echo  ================================================================
echo.

cd /d "%~dp0"
set "XTE_OBSERVE_ENABLED=True"
set "XTE_OBSERVE_PATH_ENABLED=True"
set "EXIT_COORDINATOR_SHADOW_ENABLED=True"
set "BYPASS_ALL_GATES=True"
python run.py

pause
