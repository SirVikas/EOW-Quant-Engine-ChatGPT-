EOW Quant Engine — Master Report Bundle
═══════════════════════════════════════
Generated : 2026-05-02 09:33:17 UTC
Engine    : EOW_QUANT_ENGINE_v1.0
Trades    : 366
Net PnL   : -169.41 USDT
Win Rate  : 36.6%
PF        : 0.362

Folder Guide
────────────
01_system_state/  Full engine state JSON (DNA, trade history, portfolio ratios)
02_reports/       FTD-025A 15-section report (MD+PDF) + FTD-025B narrative (MD)
03_trade_archive/ Trade history XLSX + PDF executive summary + MD developer log
04_performance/   Performance Explorer reports for ALL / 1D / 7D / 20D presets
                  Each preset: report_<P>.json (summary) + trades_<P>.csv (raw)
05_forensics/     Deep-dive forensic analysis (7 JSON files)
  strategy_forensics.json   Per-strategy WR, PF, fees, verdict
  exit_analysis.json        How trades exit: SL / TP / TSL+ / BE
  fee_drag_analysis.json    Fee burden per symbol (FEE_TOXIC verdicts)
  regime_performance.json   WR and PF split by market regime
  hourly_performance.json   Golden hours vs avoid hours (UTC)
  signal_funnel.json        Pipeline funnel: generated → gated → placed
  capital_efficiency.json   Gap analysis vs $1/min target + roadmap
