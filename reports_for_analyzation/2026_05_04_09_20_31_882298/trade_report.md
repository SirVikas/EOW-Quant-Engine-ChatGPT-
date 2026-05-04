# EOW Quant Engine — Performance Report

**Generated:** 2026-05-04 03:48 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **443 trades** with a net **LOSS** of **-169.47 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $830.53 USDT |
| Net PnL | -169.4709 USDT |
| Win Rate | 35.4% |
| Profit Factor | 0.481 |
| Sharpe Ratio | -2.245 |
| Sortino Ratio | -2.050 |
| Calmar Ratio | -0.503 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Total Fees | 71.2660 USDT |
| Total Slippage | 14.9989 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -83.2060 USDT (before all costs)
- **Fees deducted:** -71.2660 USDT
- **Slippage deducted:** -14.9989 USDT
- **Net PnL (bankable):** -169.4709 USDT

### 2.2 Trade Statistics

- Avg win: +0.9988 USDT
- Avg loss: -1.1408 USDT
- Profit factor: 0.481

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-16.9%** | **-2.25** | **-2.05** | **19.2%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 03:22:10 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 03:22:11 | SYSTEM | Mode: PAPER \| Capital: 1000.0 USDT |
| 03:22:11 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 03:22:13 | SYSTEM | 📂 DataLake replay: 443 trades → equity=830.53 USDT |
| 03:22:13 | SYSTEM | 📂 State restored: snapshot(830.53) validated vs replay(830.53) |
| 03:22:13 | SYSTEM | ⚡ Phase 4 Profit Engine online \| rr_min=2.0 score_min=0.48 max_per_trade=5% daily_cap=6% |
| 03:22:13 | SYSTEM | 🧠 Phase 5 EV Engine online \| ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 03:22:13 | SYSTEM | 🔓 Phase 5.1 Activation Layer online \| activator_tiers=T1@5min T2@12min T3@25min \| explore_rate=3% smart_fee_rr≥3.0:15% |
| 03:22:13 | SYSTEM | Phase 6.6 Gate online \| can_trade=True reason=BYPASS_ALL_GATES safe_mode=False |
| 03:22:13 | SYSTEM | All subsystems online. Scanning markets… |
| 03:22:13 | SYSTEM | ⚡ [FTD-031] Performance layer online \| target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 03:22:23 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\data\exports\optimized_dna.json |
| 03:22:31 | SYSTEM | ⚡ Mode switched to PAPER |
| 03:27:13 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #1: meta_score=58.4 verdict=BLOCKED |
| 03:32:13 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #2: meta_score=58.4 verdict=BLOCKED |
| 03:37:13 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #3: meta_score=58.4 verdict=BLOCKED |
| 03:47:13 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #4: meta_score=58.4 verdict=BLOCKED |

---
*EOW Quant Engine V4.0 — 2026-05-04 03:48 UTC*