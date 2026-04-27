# EOW Quant Engine — Performance Report

**Generated:** 2026-04-27 03:07 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **243 trades** with a net **LOSS** of **-151.08 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $848.92 USDT |
| Net PnL | -151.0820 USDT |
| Win Rate | 45.7% |
| Profit Factor | 0.379 |
| Sharpe Ratio | -2.915 |
| Sortino Ratio | -2.329 |
| Calmar Ratio | -0.929 |
| Max Drawdown | 16.87% |
| Risk of Ruin | 100.00% |
| Total Fees | 50.5689 USDT |
| Total Slippage | 0.0000 USDT |
| Deployability | 36/100 (NOT READY) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -100.5131 USDT (before all costs)
- **Fees deducted:** -50.5689 USDT
- **Slippage deducted:** -0.0000 USDT
- **Net PnL (bankable):** -151.0820 USDT

### 2.2 Trade Statistics

- Avg win: +0.8310 USDT
- Avg loss: -1.8434 USDT
- Profit factor: 0.379

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-15.1%** | **-2.92** | **-2.33** | **16.9%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 03:06:20 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 03:06:20 | SYSTEM | Mode: PAPER \| Capital: 1000.0 USDT |
| 03:06:20 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 03:06:21 | SYSTEM | 📂 DataLake replay: 243 trades → equity=848.92 USDT |
| 03:06:21 | SYSTEM | 📂 State restored: snapshot(848.92) validated vs replay(848.92) |
| 03:06:21 | SYSTEM | ⚡ Phase 4 Profit Engine online \| rr_min=1.5 score_min=0.58 max_per_trade=5% daily_cap=3% |
| 03:06:21 | SYSTEM | 🧠 Phase 5 EV Engine online \| ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 03:06:21 | SYSTEM | 🔓 Phase 5.1 Activation Layer online \| activator_tiers=T1@3min T2@7min T3@15min \| explore_rate=10% smart_fee_rr≥3.0:15% |
| 03:06:21 | SYSTEM | Phase 6.6 Gate online \| can_trade=True reason=BOOT_GRACE safe_mode=False |
| 03:06:21 | SYSTEM | All subsystems online. Scanning markets… |
| 03:06:21 | SYSTEM | ⚡ [FTD-031] Performance layer online \| target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 03:06:25 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\data\exports\optimized_dna.json |
| 03:07:24 | SYSTEM | ⚡ Mode switched to PAPER |

---
*EOW Quant Engine V4.0 — 2026-04-27 03:07 UTC*