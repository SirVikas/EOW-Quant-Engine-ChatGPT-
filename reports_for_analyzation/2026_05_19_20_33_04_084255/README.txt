EOW Quant Engine — Master Report Bundle
═══════════════════════════════════════
Generated : 2026-05-19 14:59:05 UTC
Engine    : EOW_QUANT_ENGINE_v1.9.0
Trades    : 203
Net PnL   : -64.09 USDT
Win Rate  : 18.2%
PF        : 0.329

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
09_odyssey/         FTD-056-ODYSSEY: Proof-of-Learning → Proof-of-Edge → Proof-of-Alpha
  rl_learning_progression.json   Context Q evolution, Wilson CI, maturity stages
  edge_validation_report.json    Bootstrap PF CI + binomial significance vs random
  alpha_persistence_report.json  Bayesian WR, Q-stability, alpha durability
  strategy_evolution_report.json Per-strategy early/mid/late trajectory
  regime_performance_matrix.json Regime stats + RL Q integration (enhanced)
  confidence_calibration_report.json Q-value prediction accuracy (Brier score)
  signal_quality_evolution.json  Rolling RR/WR/fee-drag trend windows
  adaptive_decision_audit.json   RL policy change explanations per context
  reward_propagation_report.json Shaped reward quality + fee impact on learning
  intelligence_maturity_report.json 10-milestone Proof-of-Learning scorecard
10_auto_intelligence/ FTD-030: Autonomous intelligence loop state
  state.json          Current engine state: cycles, verdicts, last correction
  history.json        Last 100 correction cycle records
11_learning_memory/ FTD-030B: Pattern memory, negative memory, heatmap
  summary.json        Full memory store state + activation stats
  patterns.json       Top 100 formed patterns by confidence (leaderboard)
  failed_patterns.json Bottom 100 failed patterns by confidence
  negative_memory.json Current negative-memory blacklist (avoid zones)
  heatmap.json        Regime × parameter confidence heatmap
  log.json            Last 200 memory store records (explainability log)
12_observability/   FTD-053-GAIA: Full pipeline observability snapshot
  status.json         All six observability phase stats + health score
  anomalies.json      Active anomalies + recent history (up to 100)
  escalations.json    Active escalations + history (up to 100)
  feeds.json          Five strategic intelligence feed channels
  ai_summary.json     Latest AI strategic intelligence summary
  events.json         Recent event bus events (up to 200)
  sync.json           GitHub sync engine status
13_system_diagnostics/ System health, audit trail, AI brain state
  ct_scan.json        FTD-REF-026: Full CT-Scan (HEALTHY/WARNING/CRITICAL)
  consistency.json    FTD-040: Consistency + drawdown + streak + recovery
  audit_log.json      FTD-022: Last 1000 structured audit events
  ai_brain.json       FTD-023: Aggregated AI brain intelligence state
