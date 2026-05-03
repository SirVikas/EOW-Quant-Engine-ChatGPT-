# EOW Quant Engine — Performance Report

**Generated:** 2026-05-03 08:16 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **374 trades** with a net **LOSS** of **-165.10 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $834.90 USDT |
| Net PnL | -165.0988 USDT |
| Win Rate | 36.9% |
| Profit Factor | 0.386 |
| Sharpe Ratio | -2.544 |
| Sortino Ratio | -2.203 |
| Calmar Ratio | -0.596 |
| Max Drawdown | 18.65% |
| Risk of Ruin | 100.00% |
| Total Fees | 62.7503 USDT |
| Total Slippage | 8.6122 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -93.7363 USDT (before all costs)
- **Fees deducted:** -62.7503 USDT
- **Slippage deducted:** -8.6122 USDT
- **Net PnL (bankable):** -165.0988 USDT

### 2.2 Trade Statistics

- Avg win: +0.7523 USDT
- Avg loss: -1.1395 USDT
- Profit factor: 0.386

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-16.5%** | **-2.54** | **-2.20** | **18.6%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 07:46:22 | SYSTEM | 🚀 EOW Quant Engine booting… |
| 07:46:22 | SYSTEM | Mode: PAPER \| Capital: 1000.0 USDT |
| 07:46:22 | SYSTEM | 📋 Function Registry loaded — 81 functions registered |
| 07:46:23 | SYSTEM | 📂 DataLake replay: 369 trades → equity=830.74 USDT |
| 07:46:23 | SYSTEM | 📂 State restored: snapshot(830.74) validated vs replay(830.74) |
| 07:46:23 | SYSTEM | ⚡ Phase 4 Profit Engine online \| rr_min=2.0 score_min=0.48 max_per_trade=5% daily_cap=6% |
| 07:46:23 | SYSTEM | 🧠 Phase 5 EV Engine online \| ev_window=30 ev_min_trades=10 adaptive_lr=0.05 dd_stop=15% |
| 07:46:23 | SYSTEM | 🔓 Phase 5.1 Activation Layer online \| activator_tiers=T1@5min T2@12min T3@25min \| explore_rate=3% smart_fee_rr≥3.0:15% |
| 07:46:23 | SYSTEM | Phase 6.6 Gate online \| can_trade=True reason=BYPASS_ALL_GATES safe_mode=False |
| 07:46:23 | SYSTEM | All subsystems online. Scanning markets… |
| 07:46:23 | SYSTEM | ⚡ [FTD-031] Performance layer online \| target=100.0ms cache_ttl_pattern=60.0s queue_workers=2 |
| 07:46:26 | SYSTEM | 📥 DNA imported from D:\EOW Quant Engine V17.0(ChatGPT)_INVERSE_LOGIC\eow_quant_engine_FINAL_v2.2\eow_quant_engine\data\exports\optimized_dna.json |
| 07:46:27 | FILTER | ⚡ PAPER_SPEED bypass ORCAUSDT: SLEEP_MODE(vol=469=9%_of_avg=5080,min=10%[base=45%×0.20]) |
| 07:46:27 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=23.4 above_sma=False regime=TRENDING) |
| 07:46:27 | FILTER | ⚡ PAPER_SPEED bypass BTCUSDT: SLEEP_MODE(vol=0=2%_of_avg=8,min=10%[base=45%×0.20]) |
| 07:46:27 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: LONG entry=78400.5700 rsi=44.9 |
| 07:46:27 | SIGNAL | 🔔 Signal LONG BTCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:46:27 | SIGNAL | 💰 Orchestrator BTCUSDT: score=0.441 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.002119 |
| 07:46:27 | TRADE | ⚡ PAPER_SPEED market-fill override BTCUSDT: USE_LIMIT_ORDERS bypassed |
| 07:46:27 | TRADE | ✅ Opened LONG BTCUSDT qty=0.002119 risk=12.46U [TrendFollowing \| TRENDING] |
| 07:46:27 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=36.9 above_sma=False regime=MEAN_REVERTING) |
| 07:46:30 | SIGNAL | ⚡ PAPER_SPEED fallback ETHUSDT: LONG entry=2311.3500 rsi=40.6 |
| 07:46:30 | SIGNAL | 🔔 Signal LONG ETHUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:46:30 | SIGNAL | 💰 Orchestrator ETHUSDT: score=0.437 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=0.071884 |
| 07:46:30 | TRADE | ⚡ PAPER_SPEED market-fill override ETHUSDT: USE_LIMIT_ORDERS bypassed |
| 07:46:30 | TRADE | ✅ Opened LONG ETHUSDT qty=0.071884 risk=12.46U [TrendFollowing \| TRENDING] |
| 07:46:32 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=MEAN_REVERTING) |
| 07:46:34 | FILTER | ⚡ PAPER_SPEED bypass ORDIUSDT: SLEEP_MODE(vol=130=6%_of_avg=2240,min=10%[base=45%×0.20]) |
| 07:46:34 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=62.8 above_sma=True regime=TRENDING) |
| 07:46:34 | SYSTEM | ⚡ Mode switched to PAPER |
| 07:48:01 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: LONG entry=0.0001 rsi=31.0 |
| 07:48:01 | SIGNAL | 🔔 Signal LONG LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:48:01 | SIGNAL | 💰 Orchestrator LUNCUSDT: score=0.397 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=1950100.938967 |
| 07:48:01 | TRADE | ⚡ PAPER_SPEED market-fill override LUNCUSDT: USE_LIMIT_ORDERS bypassed |
| 07:48:01 | TRADE | ✅ Opened LONG LUNCUSDT qty=1950100.938967 risk=12.46U [MeanReversion \| MEAN_REVERTING] |
| 07:48:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=MEAN_REVERTING) |
| 07:48:02 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=28.4 above_sma=False regime=TRENDING) |
| 07:48:06 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=63.4 above_sma=True regime=TRENDING) |
| 07:49:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=53.8 above_sma=True regime=MEAN_REVERTING) |
| 07:49:01 | FILTER | ⚡ PAPER_SPEED ORDIUSDT: RSI filter blocked (rsi=67.5 above_sma=True regime=TRENDING) |
| 07:49:09 | FILTER | ⚡ PAPER_SPEED ORCAUSDT: RSI filter blocked (rsi=31.5 above_sma=False regime=TRENDING) |
| 07:50:01 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0640 rsi=54.0 |
| 07:50:01 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:50:01 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.530 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=80.498353 |
| 07:50:01 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 07:50:01 | TRADE | ✅ Opened SHORT ORCAUSDT qty=80.498353 risk=12.46U [TrendFollowing \| TRENDING] |
| 07:50:01 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0535 rsi=70.0 |
| 07:50:01 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 07:50:01 | SIGNAL | 💰 Orchestrator BIOUSDT: score=0.398 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=3105.581308 |
| 07:50:01 | TRADE | ⚡ PAPER_SPEED market-fill override BIOUSDT: USE_LIMIT_ORDERS bypassed |
| 07:50:01 | TRADE | ✅ Opened SHORT BIOUSDT qty=3105.581308 risk=12.46U [MeanReversion \| MEAN_REVERTING] |
| 07:50:01 | SIGNAL | ⚡ ALPHA TrendBreakout ORDIUSDT score=0.812 rr=5.00 |
| 07:50:01 | SIGNAL | 🔔 Signal LONG ORDIUSDT \| TCB: ADX=32.4 VOL=6.1x RR=5.00 SCORE=0.812 |
| 07:50:01 | SIGNAL | 💰 Orchestrator ORDIUSDT: score=0.794 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=31.569181 |
| 07:50:01 | TRADE | ⚡ PAPER_SPEED market-fill override ORDIUSDT: USE_LIMIT_ORDERS bypassed |
| 07:50:01 | TRADE | ✅ Opened LONG ORDIUSDT qty=31.569181 risk=12.46U [TrendFollowing \| TRENDING] |
| 07:51:23 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #1: meta_score=85.0 verdict=BLOCKED |
| 07:55:13 | TRADE | [TM] BIOUSDT BE: SL→0.0035 (R=2.10≥1.8 → SL→BE±0.05) |
| 07:55:18 | TRADE | Position closed [TSL+] BIOUSDT @ 0.0529 |
| 07:56:23 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #2: meta_score=85.0 verdict=BLOCKED |
| 07:56:55 | TRADE | [TM] ORCAUSDT BE: SL→2.0140 (R=1.85≥1.8 → SL→BE±0.05) |
| 07:57:01 | TRADE | Position closed [TSL+] ORCAUSDT @ 2.038 |
| 07:59:54 | TRADE | Position closed [SL] ORDIUSDT @ 5.235 |
| 08:01:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=20.0 above_sma=False regime=TRENDING) |
| 08:01:23 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #3: meta_score=85.0 verdict=BLOCKED |
| 08:02:02 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=13.3 above_sma=False regime=TRENDING) |
| 08:03:00 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=13.3 above_sma=False regime=TRENDING) |
| 08:03:33 | SIGNAL | ⚡ PAPER_SPEED fallback ORCAUSDT: SHORT entry=2.0590 rsi=49.1 |
| 08:03:33 | SIGNAL | 🔔 Signal SHORT ORCAUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 08:03:33 | SIGNAL | 💰 Orchestrator ORCAUSDT: score=0.618 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=80.924811 |
| 08:03:33 | TRADE | ⚡ PAPER_SPEED market-fill override ORCAUSDT: USE_LIMIT_ORDERS bypassed |
| 08:03:33 | TRADE | ✅ Opened SHORT ORCAUSDT qty=80.924811 risk=12.50U [TrendFollowing \| TRENDING] |
| 08:03:50 | TRADE | [TM] LUNCUSDT BE: SL→0.0501 (R=1.80≥1.8 → SL→BE±0.05) |
| 08:03:50 | TRADE | Position closed [TSL+] LUNCUSDT @ 8.681e-05 |
| 08:04:06 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=23.5 above_sma=False regime=TRENDING) |
| 08:05:01 | SIGNAL | ⚡ PAPER_SPEED fallback ORDIUSDT: LONG entry=5.2540 rsi=50.9 |
| 08:05:01 | SIGNAL | 🔔 Signal LONG ORDIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 08:05:01 | SIGNAL | 💰 Orchestrator ORDIUSDT: score=0.589 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=31.824354 |
| 08:05:01 | TRADE | ⚡ PAPER_SPEED market-fill override ORDIUSDT: USE_LIMIT_ORDERS bypassed |
| 08:05:01 | TRADE | ✅ Opened LONG ORDIUSDT qty=31.824354 risk=12.54U [TrendFollowing \| TRENDING] |
| 08:05:03 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=22.2 above_sma=False regime=TRENDING) |
| 08:06:02 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=23.5 above_sma=False regime=TRENDING) |
| 08:06:23 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #4: meta_score=85.0 verdict=BLOCKED |
| 08:07:08 | SIGNAL | ⚡ ALPHA TrendBreakout BIOUSDT score=0.730 rr=5.00 |
| 08:07:08 | SIGNAL | 🔔 Signal SHORT BIOUSDT \| TCB: ADX=51.7 VOL=1.3x RR=5.00 SCORE=0.730 |
| 08:07:08 | SIGNAL | 💰 Orchestrator BIOUSDT: score=0.745 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=3203.163945 |
| 08:07:08 | TRADE | ⚡ PAPER_SPEED market-fill override BIOUSDT: USE_LIMIT_ORDERS bypassed |
| 08:07:08 | TRADE | ✅ Opened SHORT BIOUSDT qty=3203.163945 risk=12.54U [TrendFollowing \| TRENDING] |
| 08:07:40 | TRADE | Position closed [SL] ORDIUSDT @ 5.226 |
| 08:09:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 08:10:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=63.4 above_sma=True regime=MEAN_REVERTING) |
| 08:11:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=63.8 above_sma=True regime=MEAN_REVERTING) |
| 08:11:23 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #5: meta_score=85.0 verdict=BLOCKED |
| 08:12:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=63.4 above_sma=True regime=TRENDING) |
| 08:13:01 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 08:13:01 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=49.3 |
| 08:13:01 | SIGNAL | 🔔 Signal SHORT LUNCUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 08:13:01 | SIGNAL | 💰 Orchestrator LUNCUSDT: score=0.748 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=1947973.038450 |
| 08:13:01 | TRADE | ⚡ PAPER_SPEED market-fill override LUNCUSDT: USE_LIMIT_ORDERS bypassed |
| 08:13:01 | TRADE | ✅ Opened SHORT LUNCUSDT qty=1947973.038450 risk=25.05U [TrendFollowing \| TRENDING] |
| 08:13:02 | SIGNAL | ⚡ DTP ORDIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 08:13:02 | SIGNAL | ⚡ PAPER_SPEED fallback ORDIUSDT: LONG entry=5.1750 rsi=23.1 |
| 08:13:02 | SIGNAL | 🔔 Signal LONG ORDIUSDT \| PAPER_SPEED_FALLBACK(momentum micro-signal) |
| 08:13:02 | SIGNAL | 💰 Orchestrator ORDIUSDT: score=0.585 upstream_mult=0.00× conc_mult=1.00× band=BYPASS rank=1.000 amplified=False explore=False qty=32.266715 |
| 08:13:02 | TRADE | ⚡ PAPER_SPEED market-fill override ORDIUSDT: USE_LIMIT_ORDERS bypassed |
| 08:13:02 | TRADE | ✅ Opened LONG ORDIUSDT qty=32.266715 risk=25.05U [MeanReversion \| MEAN_REVERTING] |
| 08:16:23 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #6: meta_score=85.0 verdict=BLOCKED |

---
*EOW Quant Engine V4.0 — 2026-05-03 08:16 UTC*