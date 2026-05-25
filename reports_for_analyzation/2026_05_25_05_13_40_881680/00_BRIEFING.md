# PHOENIX Intelligence Briefing
**Snapshot:** 2026-05-24 23:40:57 UTC | **Engine:** v1.37.0 | **Mode:** PAPER (BYPASS_ALL_GATES=True)

---

## CRITICAL ALERTS

> **ESCALATION [CRITICAL]**: CRITICAL: ALLOW_COLLAPSE, IQ_REGRESSION (IQ_REGRESSION, ALLOW_COLLAPSE)
> **ESCALATION [HIGH]**: HIGH: IQ_REGRESSION, LOSS_STREAK, WIN_RATE_EROSION (LOSS_STREAK, IQ_REGRESSION, WIN_RATE_EROSION)
> **ESCALATION [HIGH]**: HIGH: IQ_REGRESSION, LOSS_STREAK, WIN_RATE_EROSION (LOSS_STREAK, IQ_REGRESSION, WIN_RATE_EROSION)
> **NEGATIVE EDGE**: Profit Factor = 0.404 — system is consuming capital

---

## 1. OPERATIONAL STATUS

| Field | Value |
|-------|-------|
| Engine Halted | False |
| Graceful Stop | False |
| Uptime | 2h 10m |
| Observability Pipeline | HEALTHY |
| Capital (Equity) | +821.60 USDT |
| Max Drawdown | 17.8% |
| Deployability | 0/100 (BLOCKED) |
| Open Positions | 2 |
| Symbols Watched | 13 |

---

## 2. TRADING ACTIVITY

| Metric | Value |
|--------|-------|
| Total Trades | 740 |
| Net PnL | -178.40 USDT |
| Win Rate | 18.6% |
| Profit Factor | 0.404 |
| Sharpe Ratio | -4.87 |
| Max Drawdown | 17.8% |
| Total Fees Paid | +94.20 USDT |
| Avg Win | +0.88 USDT |
| Avg Loss | -0.50 USDT |
| Minutes Since Last Trade | 0m |

---

## 3. SIGNAL PIPELINE

| Metric | Value |
|--------|-------|
| Signals / Hour | 169.0 |
| Trades / Hour | 17.0 |
| Rejection Rate | 0.0% |
| Skips This Session | 145 |
| CT-Scan SIGNAL entries (last 100) | 69 |
| CT-Scan FILTER entries (last 100) | 24 |
| CT-Scan TRADE entries (last 100) | 6 |
| Last Skip Reason | `⚡ PAPER_SPEED ONDOUSDT: RSI_LEVEL: rsi=66.2 above_sma=True bands=[58.0,42.0] (rsi=66.2 above_sma=True regime=TRENDING)` |

**Top Rejection Reasons:**
```
  (no rejection data in current window)
```

**Market Regime Distribution:** MEAN_REVERTING=2, TRENDING=11

---

## 4. ANOMALIES & ESCALATIONS

| Severity | Trigger | Age | Status |
|---------|---------|-----|--------|
| CRITICAL | CRITICAL: ALLOW_COLLAPSE, IQ_REGRESSION | 2h 8m | ACTIVE |
| HIGH | HIGH: IQ_REGRESSION, LOSS_STREAK, WIN_RATE_EROSION | 2h 4m | ACTIVE |
| HIGH | HIGH: IQ_REGRESSION, LOSS_STREAK, WIN_RATE_EROSION | 1h 58m | ACTIVE |
| HIGH | HIGH: IQ_REGRESSION, LOSS_STREAK, WIN_RATE_EROSION | 1h 52m | ACTIVE |
| HIGH | HIGH: IQ_REGRESSION, WIN_RATE_EROSION | 1h 38m | ACTIVE |
| HIGH | HIGH: IQ_REGRESSION, WIN_RATE_EROSION | 1h 32m | ACTIVE |
| HIGH | HIGH: IQ_REGRESSION, WIN_RATE_EROSION | 1h 26m | ACTIVE |
| HIGH | HIGH: IQ_REGRESSION, WIN_RATE_EROSION | 1h 20m | ACTIVE |

**Active Anomaly Counts:**
_No active anomalies._

---

## 5. ECONOMIC TRUTH VERDICT

| Dimension | Verdict |
|-----------|---------|
| Survivability (Phase-D) | NOT_VIABLE |
| Net Expectancy / Trade | -0.24 USDT |
| Regime Health | SINGLE_REGIME_VIABLE |
| Survivability (Phase-E) | UNKNOWN |
| Equilibrium (Phase-F) | UNKNOWN |

---

## 6. ALPHA CONFIRMATION (Phase-I)

| Field | Value |
|-------|-------|
| Alpha Tier | UNPROVEN |
| Alpha Score | 7 / 100 |
| Gate Status | BLOCKED |
| Trades in Window | 300 |
| Live Deployment Authorized | False (constitutional invariant) |

| Engine | State | Score |
|--------|-------|-------|
| I.1 Statistical | INSUFFICIENT_EVIDENCE | 7 |
| I.2 OOS | OOS_FAILURE | 0 |
| I.3 Fee Survival | FEE_DESTROYED | 0 |
| I.4 Regime | FRAGILE | 0 |
| I.5 Drawdown | DISQUALIFYING | 0 |


---

## 7. RL LEARNING STATE

| Metric | Value |
|--------|-------|
| Total Contexts | 22 |
| Total Pulls | 40 |
| Total Allowed | 40 |
| Allow Rate | 100.0% |
| Toxic Contexts | 2 |

**Top Performing Contexts:**
| Context | Q-Value | Visits | Win Rate |
|---------|---------|--------|----------|
| TRENDING|NY|MeanReversion | +0.000 | 0 | 0.0% |
| VOLATILITY_EXPANSION|NY|TrendFollowing | +0.000 | 0 | 0.0% |
| VOLATILITY_EXPANSION|NY|MeanReversion | +0.000 | 0 | 0.0% |
| TRENDING|LATE|MeanReversion | +0.000 | 0 | 0.0% |
| VOLATILITY_EXPANSION|LATE|TrendFollowing | +0.000 | 0 | 0.0% |

**Worst Performing Contexts:**
| Context | Q-Value | Visits | Win Rate |
|---------|---------|--------|----------|
| MEAN_REVERTING|LONDON|MeanReversion | -0.422 | 216 | 20.8% |
| TRENDING|LONDON|TrendFollowing | -0.402 | 7 | 0.0% |
| MEAN_REVERTING|ASIA|MeanReversion | -0.344 | 285 | 17.9% |



---

## 8. GENOME & STRATEGY STATE

| Strategy | Gen | Train PF | OOS PF | OOS WR | Promoted |
|----------|-----|---------|--------|--------|----------|
| TrendFollowing | G? | N/A | N/A | N/A | NO |
| MeanReversion | G? | N/A | N/A | N/A | NO |
| VolatilityExpansion | G? | N/A | N/A | N/A | NO |


---

## 9. TOP DIAGNOSTIC FINDINGS

1. Negative profit factor (0.404) — more capital consumed than earned
2. High fee drag: 35% of gross PnL consumed by fees
3. RL: 2 toxic context(s) blocking entries in those regime/session/strategy combinations
4. Alpha gate UNPROVEN (score=7/100): need 0 more trades for Phase-I certification

---

## ARCHITECTURE REFERENCE

| Diagnostic Question | File |
|--------------------|------|
| Why no trades? | `02_signal_intelligence/trade_flow.json` + `02_signal_intelligence/thought_log.json` |
| Which signals are blocked? | `02_signal_intelligence/last_skip.json` |
| RL Q-table (all contexts) | `03_live_process_snapshot/rl_qtable.json` |
| Economic truth (all 6 engines) | `04_economic_truth/orchestration.json` |
| Full learning intelligence (29 sections) | `05_alpha_and_learning/lio_full_snapshot.json` |
| Alpha certification status | `06_risk_and_governance/alpha_confirmation.json` |
| Execution governance | `06_risk_and_governance/execution_governance.json` |
| Capital & AEE state | `07_capital_and_performance/aee_state.json` + `07_capital_and_performance/capital_flow.json` |
| Genome DNA & evolution | `09_genome/genome_state.json` |
| Active anomalies | `01_operational_health/anomalies.json` |
| Active escalations | `01_operational_health/escalations.json` |
| Halt & skip history | `01_operational_health/halt_audit.json` |
