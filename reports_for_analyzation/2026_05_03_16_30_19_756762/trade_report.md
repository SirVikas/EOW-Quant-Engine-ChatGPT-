# EOW Quant Engine — Performance Report

**Generated:** 2026-05-03 10:57 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **392 trades** with a net **LOSS** of **-174.49 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $825.51 USDT |
| Net PnL | -174.4909 USDT |
| Win Rate | 36.2% |
| Profit Factor | 0.394 |
| Sharpe Ratio | -2.594 |
| Sortino Ratio | -2.267 |
| Calmar Ratio | -0.585 |
| Max Drawdown | 19.16% |
| Risk of Ruin | 100.00% |
| Total Fees | 64.9516 USDT |
| Total Slippage | 10.2632 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -99.2761 USDT (before all costs)
- **Fees deducted:** -64.9516 USDT
- **Slippage deducted:** -10.2632 USDT
- **Net PnL (bankable):** -174.4909 USDT

### 2.2 Trade Statistics

- Avg win: +0.7976 USDT
- Avg loss: -1.1510 USDT
- Profit factor: 0.394

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-17.4%** | **-2.59** | **-2.27** | **19.2%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 10:48:45 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 10:48:45 | SYSTEM | Mode: PAPER \| Capital: 1000.0 USDT |
| 10:48:45 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 10:48:46 | SYSTEM | 📂 DataLake replay: 391 trades → equity=826.14 USDT |
| 10:48:46 | SYSTEM | 📂 State restored: snapshot(826.14) validated vs replay(826.14) |
| 10:48:46 | SYSTEM | ⚡ Phase 4 Profit Engine online \| rr_min=2.0 score_min=0.48 max_per_trade=5% daily_cap=6% |
| 10:48:46 | SYSTEM | 🧠 Phase 5 EV Engine online \| ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 10:48:46 | SYSTEM | 🔓 Phase 5.1 Activation Layer online \| activator_tiers=T1@5min T2@12min T3@25min \| explore_rate=3% smart_fee_rr≥3.0:15% |
| 10:48:46 | SYSTEM | Phase 6.6 Gate online \| can_trade=True reason=BYPASS_ALL_GATES safe_mode=False |
| 10:48:46 | SYSTEM | All subsystems online. Scanning markets… |
| 10:48:46 | SYSTEM | ⚡ [FTD-031] Performance layer online \| target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 10:48:50 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=38.2 |
| 10:48:50 | SIGNAL | 🔔 Signal SHORT LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 10:48:50 | SIGNAL | 💰 Orchestrator LUNCUSDT: score=0.478 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=1987820.741097 |
| 10:48:50 | TRADE | ⚡ PAPER_SPEED market-fill override LUNCUSDT: USE_LIMIT_ORDERS bypassed |
| 10:48:50 | TRADE | ✅ Opened SHORT LUNCUSDT qty=1987820.741097 risk=12.39U [TrendFollowing \| TRENDING] |
| 10:48:50 | SIGNAL | ⚡ PAPER_SPEED fallback BABYUSDT: SHORT entry=0.0249 rsi=58.4 |
| 10:48:50 | SIGNAL | 🔔 Signal SHORT BABYUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 10:48:50 | SIGNAL | 💰 Orchestrator BABYUSDT: score=0.468 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=6625.006415 |
| 10:48:50 | TRADE | ⚡ PAPER_SPEED market-fill override BABYUSDT: USE_LIMIT_ORDERS bypassed |
| 10:48:50 | TRADE | ✅ Opened SHORT BABYUSDT qty=6625.006415 risk=12.39U [TrendFollowing \| TRENDING] |
| 10:48:50 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\data\exports\optimized_dna.json |
| 10:48:50 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=22.7 above_sma=False regime=TRENDING) |
| 10:48:51 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=47.4 above_sma=True regime=MEAN_REVERTING) |
| 10:48:55 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=30.7 above_sma=False regime=TRENDING) |
| 10:48:56 | SYSTEM | ⚡ Mode switched to PAPER |
| 10:48:58 | SIGNAL | ⚡ PAPER_SPEED fallback ORDIUSDT: SHORT entry=4.9800 rsi=39.2 |
| 10:48:58 | SIGNAL | 🔔 Signal SHORT ORDIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 10:48:58 | SIGNAL | 💰 Orchestrator ORDIUSDT: score=0.420 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=33.178245 |
| 10:48:58 | TRADE | ⚡ PAPER_SPEED market-fill override ORDIUSDT: USE_LIMIT_ORDERS bypassed |
| 10:48:58 | TRADE | ✅ Opened SHORT ORDIUSDT qty=33.178245 risk=12.39U [TrendFollowing \| TRENDING] |
| 10:49:09 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=33.3 above_sma=False regime=TRENDING) |
| 10:50:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=24.0 above_sma=False regime=TRENDING) |
| 10:50:01 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=36.8 above_sma=False regime=TRENDING) |
| 10:50:02 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=35.1 above_sma=False regime=TRENDING) |
| 10:50:03 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=55.6 above_sma=True regime=MEAN_REVERTING) |
| 10:51:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=24.0 above_sma=False regime=TRENDING) |
| 10:51:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=32.7 above_sma=False regime=TRENDING) |
| 10:51:05 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=47.4 above_sma=True regime=MEAN_REVERTING) |
| 10:51:07 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=24.2 above_sma=False regime=TRENDING) |
| 10:52:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=30.0 above_sma=False regime=TRENDING) |
| 10:52:01 | FILTER | ⚡ PAPER_SPEED ETHUSDT: RSI filter blocked (rsi=35.7 above_sma=False regime=TRENDING) |
| 10:52:07 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=52.6 above_sma=True regime=MEAN_REVERTING) |
| 10:52:25 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=30.3 above_sma=False regime=TRENDING) |
| 10:53:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=29.4 above_sma=False regime=TRENDING) |
| 10:53:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=45.5 above_sma=False regime=MEAN_REVERTING) |
| 10:53:02 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=34.3 above_sma=False regime=TRENDING) |
| 10:53:05 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: SHORT entry=2312.5700 rsi=38.9 |
| 10:53:05 | SIGNAL | 🔔 Signal SHORT ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 10:53:05 | SIGNAL | 💰 Orchestrator ETHUSDT: score=0.370 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.071448 |
| 10:53:05 | TRADE | ⚡ PAPER_SPEED market-fill override ETHUSDT: USE_LIMIT_ORDERS bypassed |
| 10:53:05 | TRADE | ✅ Opened SHORT ETHUSDT qty=0.071448 risk=12.39U [TrendFollowing \| TRENDING] |
| 10:54:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 10:54:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=29.4 above_sma=False regime=TRENDING) |
| 10:54:03 | TRADE | Position closed [SL] LUNCUSDT @ 8.332e-05 |
| 10:54:11 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=42.9 above_sma=False regime=MEAN_REVERTING) |
| 10:54:22 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0780 rsi=48.5 |
| 10:54:22 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 10:54:22 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.400 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=79.452275 |
| 10:54:22 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 10:54:22 | TRADE | ✅ Opened SHORT ORCAUSDT qty=79.452275 risk=12.38U [TrendFollowing \| TRENDING] |
| 10:55:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=33.3 above_sma=False regime=TRENDING) |
| 10:55:24 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=61.9 above_sma=True regime=MEAN_REVERTING) |
| 10:56:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=21.7 above_sma=False regime=TRENDING) |
| 10:56:02 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=61.9 above_sma=True regime=MEAN_REVERTING) |
| 10:57:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=23.0 above_sma=False regime=TRENDING) |
| 10:57:12 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: LONG entry=0.0543 rsi=61.9 |
| 10:57:12 | SIGNAL | 🔔 Signal LONG BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 10:57:12 | SIGNAL | 💰 Orchestrator BIOUSDT: score=0.428 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=3040.549314 |
| 10:57:12 | TRADE | ⚡ PAPER_SPEED market-fill override BIOUSDT: USE_LIMIT_ORDERS bypassed |
| 10:57:12 | TRADE | ✅ Opened LONG BIOUSDT qty=3040.549314 risk=12.38U [TrendFollowing \| TRENDING] |

---
*EOW Quant Engine V4.0 — 2026-05-03 10:57 UTC*