@echo off
title PHOENIX - XTE PIPELINE EVAL (SIMULATED DATA)
color 0C

echo.
echo  ================================================================
echo   PHOENIX  --  XTE PIPELINE EVALUATION  (AD-HOC, FAST)
echo   FTD-094A  --  SIMULATED 500-SAMPLE RUN
echo  ================================================================
echo.
echo   WARNING: This generates SIMULATED XTE observations to exercise
echo   the validation / counterfactual / verdict pipeline END-TO-END
echo   in seconds. It is NOT real evidence. Every record is tagged
echo   simulated:true and written to a SEPARATE eval archive so your
echo   real campaign data is never touched.
echo.
echo   Use this ONLY to see the pipeline work. Do NOT treat the
echo   printed verdict as proof that XTE improves profitability.
echo   For real proof, run start_xte_campaign.bat instead.
echo  ================================================================
echo.

cd /d "%~dp0"
python tools\xte_simulate_campaign.py --n 500 --reset ^
    --archive reports\xte_observations\eval_obs.jsonl ^
    --paths   reports\xte_observations\eval_paths.jsonl

pause
