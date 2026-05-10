EOW Quant Engine — Master Report Bundle
═══════════════════════════════════════
Generated : 2026-05-10 16:47:38 UTC
Engine    : EOW_QUANT_ENGINE_v1.2.2
Trades    : 1055
Net PnL   : -294.35 USDT
Win Rate  : 24.4%
PF        : 0.461

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
06_evolution/     FTD-EV-001 Self-learning forensic audit trail (4 files)
  evolution_lineage.json    Generation-by-generation correction history
                            Format: [Cycle ID] → [Change] → [Pre vs Post Delta]
  system_health.json        Drift status (Stable/Warning/Critical) + trajectory
  alert_log.json            All critical alerts; LEARNING_PAUSE events flagged RED
  executive_summary.md      Natural-language 24-hour evolution narrative
07_live_process/ FTD-LPA: Live Process Access runtime snapshot (5 files)
  *_MANIFEST.json           Package manifest + architecture / safety notes
  *_runtime_logs.json       All loguru log records captured since startup
  *_runtime_logs.txt        Human-readable plain-text log stream
  *_thought_log.json        Engine CT-Scan decision trace (last 500 entries)
  *_rl_qtable.json          Complete RL Q-table with all context states
  *_trade_logs.json         In-memory session trades + SQLite history
08_rl_intelligence/ FTD-055-ATHENA: Institutional RL learning analysis (2 files)
  rl_intelligence.json      Evidence-based verdict: Is the RL actually learning?
                            Verdict / intelligence_score / context coverage /
                            alpha discovery / differentiation / policy evolution
  trade_quality_evolution.json  Are later trades smarter than earlier trades?
                            Early vs late session win-rate, rolling windows,
                            regime evolution trends
