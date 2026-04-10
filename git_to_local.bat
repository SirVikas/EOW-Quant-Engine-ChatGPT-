@echo off
TITLE EOW QUANT ENGINE - SELECTIVE UPDATE PROTECTOR
D:
cd "D:\EOW Quant Engine V14.0\eow_quant_engine_FINAL_v2.2\eow_quant_engine"

echo ======================================================
echo    STEP 1: STASHING ONLY SESSION DATA (NOT SCRIPTS)
echo ======================================================
:: Hum sirf 'data' folder aur '.env' ko temporarily save kar rahe hain
:: Developer ke setup scripts (.bat) ko hum stash nahi karenge taaki wo update ho sakein
git stash push data/ .env reports_for_analyzation/ -m "TradeDataOnly"

echo.
echo ======================================================
echo    STEP 2: SYNCING ALL LOGIC & SETUP FILES...
echo ======================================================
git fetch origin main
git pull origin main

echo.
echo ======================================================
echo    STEP 3: RE-APPLYING YOUR TRADE DATA...
echo ======================================================
:: Aapka $9000 ka balance aur history wapas aa jayegi
:: Lekin 'install_and_run.bat' developer wala naya version hi rahega
git stash pop

echo.
echo ======================================================
echo    SUCCESS: Logic & Setup Updated. Trade Data Preserved.
echo ======================================================
pause