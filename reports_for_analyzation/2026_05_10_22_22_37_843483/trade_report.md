# EOW Quant Engine — Performance Report

**Generated:** 2026-05-10 16:47 UTC  
**Mode:** `TIER 2: LIVE PAPER — VIRTUAL CAPITAL`  
**Persistence:** ✅ PERSISTENCE ACTIVE  

---

## 1. Executive Summary

The engine closed **1055 trades** with a net **LOSS** of **-294.35 USDT**.  

| Metric | Value |
|--------|-------|
| Final Capital | $705.65 USDT |
| Net PnL | -294.3460 USDT |
| Win Rate | 24.4% |
| Profit Factor | 0.461 |
| Sharpe Ratio | -2.382 |
| Sortino Ratio | -2.424 |
| Calmar Ratio | -0.227 |
| Max Drawdown | 30.91% |
| Risk of Ruin | 100.00% |
| Total Fees | 141.8088 USDT |
| Total Slippage | 67.9061 USDT |
| Deployability | 55/100 (CONDITIONAL) |

---

## 2. Performance Audit

### 2.1 PnL Breakdown

- **Gross PnL:** -84.6311 USDT (before all costs)
- **Fees deducted:** -141.8088 USDT
- **Slippage deducted:** -67.9061 USDT
- **Net PnL (bankable):** -294.3460 USDT

### 2.2 Trade Statistics

- Avg win: +0.9746 USDT
- Avg loss: -0.6848 USDT
- Profit factor: 0.461

---

## 3. Benchmark Comparison

| Fund | Annual Return | Sharpe | Sortino | Max DD |
|------|--------------|--------|---------|--------|
| **EOW Engine** | **-29.4%** | **-2.38** | **-2.42** | **30.9%** |
| S&P 500 (Buy & Hold) | +10.5% | 0.60 | 0.85 | 33.9% |
| Avg Hedge Fund (HFRX) | +4.8% | 0.42 | 0.55 | 12.5% |
| Renaissance Medallion | +66.0% | 3.20 | 5.10 | 5.0% |
| Top-Tier CTAs (SG CTA) | +8.2% | 0.72 | 1.05 | 18.0% |

---

## 4. Signal Audit (CT-Scan Log)

| Time | Level | Message |
|------|-------|---------|
| 16:33:03 | SIGNAL | ⚡ ALPHA TrendBreakout SAHARAUSDT score=0.531 rr=4.00 |
| 16:33:03 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=62.7 above_sma=True regime=TRENDING) |
| 16:33:03 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 16:33:03 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=34.4 above_sma=False regime=TRENDING) |
| 16:33:04 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 16:33:04 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=25.0 above_sma=False regime=TRENDING) |
| 16:33:04 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 16:33:04 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=29.4 above_sma=False regime=TRENDING) |
| 16:33:07 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 16:33:07 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=44.0 above_sma=False regime=TRENDING) |
| 16:33:08 | TRADE | [TM] ONDOUSDT BE: SL→0.4224 (R=1.01≥1.0 mode=TREND_FOLLOW → SL→BE) |
| 16:34:01 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 16:34:01 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=60.6 above_sma=True regime=MEAN_REVERTING) |
| 16:34:01 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 16:34:01 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=27.3 above_sma=False regime=TRENDING) |
| 16:34:02 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 16:34:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=37.7 above_sma=False regime=TRENDING) |
| 16:34:02 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 16:34:02 | SIGNAL | ⚡ ALPHA PullbackEntry LAYERUSDT score=0.583 rr=4.00 |
| 16:34:02 | SIGNAL | ⚡ PAPER_SPEED fallback LAYERUSDT: SHORT entry=0.1265 rsi=58.3 |
| 16:34:03 | SIGNAL | 📈 STREAK TONUSDT: COLD len=7 score_adj=+0.05 → eff_min=0.480 |
| 16:34:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=35.1 above_sma=False regime=TRENDING) |
| 16:34:07 | TRADE | Position closed [BE] ONDOUSDT @ 0.4225 |
| 16:35:05 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:35:05 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=53.8 above_sma=True regime=MEAN_REVERTING) |
| 16:35:06 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:35:06 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=32.9 above_sma=False regime=TRENDING) |
| 16:35:06 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:35:06 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 16:35:08 | SIGNAL | 📈 STREAK TONUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:35:08 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=43.8 above_sma=False regime=TRENDING) |
| 16:35:27 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:35:27 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=38.5 above_sma=False regime=TRENDING) |
| 16:35:59 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #47: meta_score=48.2 verdict=— |
| 16:36:04 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:36:04 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=66.0 above_sma=True regime=TRENDING) |
| 16:36:04 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:36:04 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=28.6 above_sma=False regime=TRENDING) |
| 16:36:05 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:36:05 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=50.9 above_sma=True regime=MEAN_REVERTING) |
| 16:36:05 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:36:05 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=35.7 above_sma=False regime=TRENDING) |
| 16:36:06 | SIGNAL | 📈 STREAK TONUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:36:06 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=46.7 above_sma=False regime=TRENDING) |
| 16:36:06 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:36:06 | SIGNAL | ⚡ PAPER_SPEED fallback LAYERUSDT: SHORT entry=0.1264 rsi=52.3 |
| 16:37:00 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:37:00 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=51.2 above_sma=False regime=TRENDING) |
| 16:37:01 | SIGNAL | 📈 STREAK TONUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:37:01 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=45.2 above_sma=False regime=TRENDING) |
| 16:37:01 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:37:01 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=52.2 above_sma=True regime=MEAN_REVERTING) |
| 16:37:02 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:37:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=36.8 above_sma=False regime=TRENDING) |
| 16:37:03 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:37:03 | SIGNAL | ⚡ ALPHA PullbackEntry UNIUSDT score=0.690 rr=5.00 |
| 16:37:03 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=58.8 above_sma=True regime=TRENDING) |
| 16:37:14 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:37:14 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=43.8 above_sma=False regime=TRENDING) |
| 16:38:08 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:38:08 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=54.6 above_sma=True regime=MEAN_REVERTING) |
| 16:38:09 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:38:09 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=41.1 above_sma=False regime=TRENDING) |
| 16:38:09 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:38:09 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=38.1 above_sma=False regime=TRENDING) |
| 16:38:10 | SIGNAL | 📈 STREAK TONUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:38:10 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=45.2 above_sma=False regime=TRENDING) |
| 16:38:10 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:38:10 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=40.0 above_sma=False regime=TRENDING) |
| 16:38:10 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:38:10 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=58.8 above_sma=True regime=TRENDING) |
| 16:38:10 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:38:10 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=29.1 above_sma=False regime=TRENDING) |
| 16:39:00 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:39:00 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=66.2 above_sma=True regime=MEAN_REVERTING) |
| 16:39:01 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:39:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=46.0 above_sma=False regime=TRENDING) |
| 16:39:01 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:39:01 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=63.8 above_sma=True regime=TRENDING) |
| 16:39:01 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:39:01 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=48.9 above_sma=False regime=TRENDING) |
| 16:39:02 | SIGNAL | 📈 STREAK TONUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:39:02 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=41.4 above_sma=False regime=TRENDING) |
| 16:39:03 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.480 |
| 16:39:03 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=50.0 above_sma=False regime=TRENDING) |
| 16:39:07 | SIGNAL | ⚡ DTP LAYERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:39:07 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:39:07 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=47.7 above_sma=False regime=TRENDING) |
| 16:39:17 | TRADE | [TM] ETHUSDT BE: SL→2345.6193 (R=1.00≥1.0 mode=TREND_FOLLOW → SL→BE) |
| 16:40:00 | SIGNAL | ⚡ DTP LAYERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:40:00 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:40:00 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=48.9 above_sma=False regime=TRENDING) |
| 16:40:00 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:40:00 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:40:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81304.6000 rsi=56.9 |
| 16:40:00 | SIGNAL | ⚡ DTP SAHARAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:40:00 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:40:00 | SIGNAL | ⚡ ALPHA PullbackEntry SAHARAUSDT score=0.508 rr=4.00 |
| 16:40:00 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=56.3 above_sma=True regime=MEAN_REVERTING) |
| 16:40:01 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:40:01 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:40:01 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 16:40:04 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:40:04 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:40:04 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=50.4 above_sma=False regime=TRENDING) |
| 16:40:04 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:40:04 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:40:04 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0541 rsi=56.2 |
| 16:40:07 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:40:07 | SIGNAL | 📈 STREAK TONUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:40:07 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=41.4 above_sma=False regime=TRENDING) |
| 16:40:59 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #48: meta_score=48.2 verdict=— |
| 16:41:12 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:41:12 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:41:12 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=52.7 |
| 16:41:12 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:41:12 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:41:12 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81315.1600 rsi=53.2 |
| 16:41:12 | SIGNAL | ⚡ DTP SAHARAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:41:12 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:41:12 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=MEAN_REVERTING) |
| 16:41:13 | SIGNAL | ⚡ DTP LAYERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:41:13 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:41:13 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=51.1 above_sma=False regime=TRENDING) |
| 16:41:14 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:41:14 | SIGNAL | 📈 STREAK TONUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:41:14 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=37.0 above_sma=False regime=TRENDING) |
| 16:41:15 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:41:15 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:41:15 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: LONG entry=4.0460 rsi=43.1 |
| 16:41:24 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:41:24 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:41:24 | FILTER | ⚡ PAPER_SPEED bypass BIOUSDT: SLEEP_MODE(vol=24958=9%_of_avg=276213,min=10%[base=45%×0.20]) |
| 16:41:24 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0541 rsi=60.0 |
| 16:42:02 | SIGNAL | ⚡ DTP SAHARAUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:42:02 | SIGNAL | 📈 STREAK SAHARAUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:42:02 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=50.0 above_sma=True regime=MEAN_REVERTING) |
| 16:42:02 | SIGNAL | ⚡ DTP LUNCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:42:02 | SIGNAL | 📈 STREAK LUNCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:42:02 | SIGNAL | ⚡ PAPER_SPEED fallback LUNCUSDT: SHORT entry=0.0001 rsi=61.8 |
| 16:42:02 | SIGNAL | ⚡ DTP TONUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:42:02 | SIGNAL | 📈 STREAK TONUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:42:02 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=25.0 above_sma=False regime=TRENDING) |
| 16:42:03 | SIGNAL | ⚡ DTP BTCUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:42:03 | SIGNAL | 📈 STREAK BTCUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:42:03 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=46.3 above_sma=False regime=TRENDING) |
| 16:42:05 | SIGNAL | ⚡ DTP LAYERUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:42:05 | SIGNAL | 📈 STREAK LAYERUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:42:05 | SIGNAL | ⚡ ALPHA PullbackEntry LAYERUSDT score=0.548 rr=4.00 |
| 16:42:05 | SIGNAL | ⚡ PAPER_SPEED fallback LAYERUSDT: SHORT entry=0.1272 rsi=56.5 |
| 16:42:06 | SIGNAL | ⚡ DTP UNIUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:42:06 | SIGNAL | 📈 STREAK UNIUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:42:06 | SIGNAL | ⚡ ALPHA PullbackEntry UNIUSDT score=0.484 rr=5.00 |
| 16:42:06 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: LONG entry=4.0520 rsi=42.6 |
| 16:42:09 | SIGNAL | ⚡ DTP BIOUSDT: tier=TIER_1 af=RELAX score_min=0.430 vol_mult=0.50× fee_tol=0.10 |
| 16:42:09 | SIGNAL | 📈 STREAK BIOUSDT: COLD len=8 score_adj=+0.05 → eff_min=0.430 |
| 16:42:09 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=62.5 above_sma=True regime=TRENDING) |
| 16:42:30 | TRADE | Position closed [TSL+] ETHUSDT @ 2348.06 |
| 16:43:01 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=47.9 above_sma=True regime=MEAN_REVERTING) |
| 16:43:02 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: LONG entry=4.0480 rsi=42.6 |
| 16:43:02 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81294.2800 rsi=52.7 |
| 16:43:02 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=70.9 above_sma=True regime=TRENDING) |
| 16:43:04 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=27.3 above_sma=False regime=TRENDING) |
| 16:43:05 | SIGNAL | ⚡ ALPHA PullbackEntry LAYERUSDT score=0.543 rr=4.00 |
| 16:43:05 | SIGNAL | ⚡ PAPER_SPEED fallback LAYERUSDT: SHORT entry=0.1270 rsi=61.9 |
| 16:43:06 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0541 rsi=62.5 |
| 16:44:00 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=42.6 above_sma=True regime=MEAN_REVERTING) |
| 16:44:00 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81294.2900 rsi=57.0 |
| 16:44:00 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=27.3 above_sma=False regime=TRENDING) |
| 16:44:00 | SIGNAL | ⚡ ALPHA TrendBreakout LUNCUSDT score=0.817 rr=5.00 |
| 16:44:00 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=81.4 above_sma=True regime=TRENDING) |
| 16:44:00 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0541 rsi=62.5 |
| 16:44:02 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=51.2 above_sma=True regime=MEAN_REVERTING) |
| 16:44:02 | SIGNAL | ⚡ ALPHA PullbackEntry LAYERUSDT score=0.573 rr=4.00 |
| 16:44:02 | SIGNAL | ⚡ PAPER_SPEED fallback LAYERUSDT: SHORT entry=0.1267 rsi=60.5 |
| 16:45:00 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=45.8 above_sma=False regime=TRENDING) |
| 16:45:01 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=78.6 above_sma=True regime=TRENDING) |
| 16:45:01 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=54.5 above_sma=True regime=MEAN_REVERTING) |
| 16:45:03 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=42.1 above_sma=False regime=TRENDING) |
| 16:45:03 | SIGNAL | ⚡ PAPER_SPEED fallback LAYERUSDT: SHORT entry=0.1266 rsi=52.6 |
| 16:45:03 | SIGNAL | ⚡ ALPHA PullbackEntry UNIUSDT score=0.540 rr=5.00 |
| 16:45:03 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: LONG entry=4.0480 rsi=39.8 |
| 16:45:08 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0541 rsi=57.1 |
| 16:45:59 | SYSTEM | 🧠 [FTD-030] Auto-intelligence cycle #49: meta_score=48.3 verdict=— |
| 16:46:01 | SIGNAL | ⚡ PAPER_SPEED fallback UNIUSDT: LONG entry=4.0680 rsi=47.8 |
| 16:46:02 | SIGNAL | ⚡ ALPHA TrendBreakout TONUSDT score=0.879 rr=5.00 |
| 16:46:02 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=32.0 above_sma=False regime=TRENDING) |
| 16:46:02 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=46.5 above_sma=False regime=MEAN_REVERTING) |
| 16:46:02 | FILTER | ⚡ PAPER_SPEED BTCUSDT: RSI filter blocked (rsi=48.3 above_sma=False regime=TRENDING) |
| 16:46:02 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=46.0 above_sma=True regime=MEAN_REVERTING) |
| 16:46:05 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=75.6 above_sma=True regime=TRENDING) |
| 16:46:06 | SIGNAL | ⚡ PAPER_SPEED fallback BIOUSDT: SHORT entry=0.0540 rsi=57.1 |
| 16:47:09 | SIGNAL | ⚡ PAPER_SPEED fallback BTCUSDT: SHORT entry=81281.8400 rsi=66.2 |
| 16:47:09 | FILTER | ⚡ PAPER_SPEED UNIUSDT: RSI filter blocked (rsi=48.7 above_sma=True regime=MEAN_REVERTING) |
| 16:47:10 | FILTER | ⚡ PAPER_SPEED SAHARAUSDT: RSI filter blocked (rsi=54.1 above_sma=True regime=MEAN_REVERTING) |
| 16:47:11 | FILTER | ⚡ PAPER_SPEED TONUSDT: RSI filter blocked (rsi=48.3 above_sma=False regime=TRENDING) |
| 16:47:14 | FILTER | ⚡ PAPER_SPEED LAYERUSDT: RSI filter blocked (rsi=55.0 above_sma=False regime=MEAN_REVERTING) |
| 16:47:14 | FILTER | ⚡ PAPER_SPEED LUNCUSDT: RSI filter blocked (rsi=83.1 above_sma=True regime=TRENDING) |
| 16:47:22 | FILTER | ⚡ PAPER_SPEED BIOUSDT: RSI filter blocked (rsi=69.2 above_sma=False regime=MEAN_REVERTING) |
| 16:47:33 | SYSTEM | 📊 Unified Report v2 exported (FTD-025B-URX-V2) |

---
*EOW Quant Engine V4.0 — 2026-05-10 16:47 UTC*