# EOW Quant Engine — v1.0
### Self-Evolving Autonomous Multi-Asset Trading System

---

## 🚀 Quick Start (3 Ways)

### Option A — Windows (Easiest)
```
Double-click: install_and_run.bat
```
That's it. Opens the dashboard automatically.

### Option B — Linux / macOS
```bash
bash install_and_run.sh paper      # paper mode (default)
bash install_and_run.sh live       # live mode
```

### Option C — Manual
```bash
python -m venv venv
source venv/bin/activate           # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.template .env              # fill in your API keys
python run.py                      # starts engine + opens browser
```

### Option D — Docker
```bash
docker-compose up --build          # starts Redis + DB + engine + dashboard
# Dashboard at http://localhost:3000  (nginx)
# API direct at http://localhost:8000
```

> **Direct run (Options A/B/C):** Dashboard auto-opens at **http://127.0.0.1:8000**
> — served by FastAPI itself, no nginx needed.

---

## 📁 Project Structure

```
eow_quant_engine/
│
├── run.py                  ← ONE-CLICK LAUNCHER (start here)
├── main.py                 ← FastAPI application + engine wiring
├── config.py               ← All tunable parameters (strategy DNA)
├── requirements.txt
├── dashboard.html          ← Standalone pastel dashboard (no build needed)
│
├── core/
│   ├── market_data.py      ← Step 1: WebSocket multi-currency streams
│   ├── pnl_calculator.py   ← Step 2: Pure PnL (gross - fees - slippage - borrow)
│   ├── genome_engine.py    ← Step 3: Strategy mutation + backtest + promotion
│   ├── regime_detector.py  ← Market regime: TRENDING / MEAN_REVERTING / VOL_EXP
│   ├── risk_controller.py  ← Step 5: SL/TP enforcement + MDD halt
│   ├── self_healing.py     ← Auto-reconnect + ghost order clear + balance sync
│   └── data_lake.py        ← SQLite tick/candle/trade persistence
│
├── strategies/
│   └── strategy_modules.py ← TrendFollowing + MeanReversion + VolatilityExpansion
│
├── utils/
│   ├── capital_scaler.py   ← Kelly Criterion + streak-based position sizing
│   └── export_manager.py   ← Full-state JSON export/import
│
├── data/
│   ├── eow_lake.db         ← SQLite data lake (auto-created)
│   └── exports/            ← JSON state exports
│
├── docker-compose.yml
├── Dockerfile
├── nginx.conf
├── install_and_run.bat     ← Windows one-click
└── install_and_run.sh      ← Linux/macOS one-click
```

---

## 🧠 Architecture Overview

```
Binance WebSocket
      │
      ▼
MarketDataProvider          ← streams 30 USDT pairs simultaneously
      │
      ├──► DataLake          ← persists every tick + candle to SQLite
      │
      ├──► RegimeDetector    ← ADX + ATR + BB Width → regime classification
      │         │
      │         ▼
      │    get_strategy()   ← routes to correct strategy module
      │         │
      │         ▼
      │    Signal (LONG/SHORT/NONE)
      │         │
      │         ▼
      ├──► CapitalScaler     ← Kelly + streak sizing
      │         │
      │         ▼
      ├──► RiskController    ← opens position, monitors SL/TP, MDD halt
      │         │
      │         ▼
      └──► PurePnLCalculator ← gross − fees − slippage − borrow = Net PnL

GenomeEngine (background, every 60 min)
      │
      ├── mutates strategy DNA
      ├── backtests on last 24h of DataLake candles
      └── promotes winners to active if PF > 1.3 and WR > 52%

SelfHealingProtocol (every 60s)
      ├── API ping
      ├── Redis flush
      ├── WebSocket health check
      └── balance sync

FastAPI (port 8000)
      ├── REST: /api/status, /api/pnl, /api/market, /api/positions...
      └── WebSocket: /ws → pushes real-time updates to dashboard
```

---

## ⚙️ Configuration (config.py / .env)

| Parameter              | Default    | Description                          |
|------------------------|------------|--------------------------------------|
| `TRADE_MODE`           | PAPER      | PAPER or LIVE                        |
| `AUTH_ENABLED`         | false      | Enable bearer-token control-plane auth |
| `ALLOWED_ORIGINS`      | localhost  | Comma-separated CORS allow-list      |
| `CONTROL_API_KEYS`     | empty      | `token:role` pairs (operator/admin)  |
| `INITIAL_CAPITAL`      | 1000 USDT  | Starting bankroll                    |
| `TOP_N_PAIRS`          | 30         | USDT pairs to monitor                |
| `MAX_RISK_PER_TRADE`   | 1%         | Risk per trade as % of equity        |
| `MAX_DRAWDOWN_HALT`    | 15%        | Engine halts at this MDD             |
| `KELLY_FRACTION`       | 0.25       | Quarter-Kelly (conservative)         |
| `GENOME_CYCLE_MINUTES` | 60         | Mutation cycle interval              |
| `GENOME_POPULATION`    | 20         | Shadow strategies per cycle          |
| `GENOME_PROMOTE_PF`    | 1.3        | Min profit factor to promote         |
| `GENOME_PROMOTE_WIN_RATE` | 52%    | Min win rate to promote              |
| `HEAL_INTERVAL_SECONDS`| 60         | Self-healing watchdog interval       |

---

## 📊 API Reference

| Method | Endpoint             | Description                        |
|--------|----------------------|------------------------------------|
| GET    | /api/status          | Engine health, mode, equity        |
| GET    | /api/pnl             | Pure PnL stats + equity curve      |
| GET    | /api/market          | Live market snapshot               |
| GET    | /api/positions       | Open positions + risk state        |
| GET    | /api/genome          | Genome log + active strategy DNA   |
| GET    | /api/regime          | Market regime per symbol           |
| GET    | /api/thoughts        | CT-Scan AI thought log             |
| GET    | /api/health          | Self-healing watchdog status       |
| POST   | /api/mode/PAPER      | Switch to paper mode               |
| POST   | /api/mode/LIVE       | Switch to live mode                |
| POST   | /api/export          | Download full JSON state           |
| POST   | /api/emergency-close | Close all open positions           |
| POST   | /api/resume          | Resume after halt                  |
| WS     | /ws                  | Real-time dashboard WebSocket feed |

> Privileged endpoints (`/api/mode/*`, `/api/import-dna`, `/api/emergency-close`, `/api/resume`) require `Authorization: Bearer <token>` when `AUTH_ENABLED=true`.

---

## 🧬 Pure PnL Formula

```
NetPnL = GrossProfit
       − BinanceFees   (maker 0.02% / taker 0.04% per side)
       − SlippageCost  (0.03% per side, configurable)
       − BorrowCost    (short positions: annual rate × hold hours / 8760)
```

---

## 📦 JSON Export Format

POST `/api/export` downloads a timestamped `.json`:

```json
{
  "meta": { "export_ts": 1700000000000, "engine_ver": "EOW_QUANT_ENGINE_v1.0" },
  "strategy_dna": {
    "active": {
      "TrendFollowing":      { "ema_fast": 9, "ema_slow": 21, ... },
      "MeanReversion":       { "bb_period": 20, "bb_std": 2.0, ... },
      "VolatilityExpansion": { "lookback": 20, "vol_filter": 1.2, ... }
    }
  },
  "trade_history": [ { "trade_id": "...", "net_pnl": 12.44, ... } ],
  "session_stats": { "win_rate": 58.3, "profit_factor": 1.84, ... },
  "portfolio_ratios": { "alpha": 0.08, "beta": 0.72, "sharpe_ratio": 1.42 }
}
```

Re-import tuned DNA: POST `/api/import-dna` with `{ "path": "data/exports/eow_state_xxx.json" }`

---

## ⚠️ Important Notes

1. **Start in PAPER mode** always. Test for at least 2 weeks before LIVE.
2. **Binance API keys** need Spot + Futures read + trade permissions.
3. **LIVE mode** executes real orders with real money. Use at your own risk.
4. The Genome Engine mutates strategy parameters automatically — review promotion logs.
5. Redis is optional — engine uses in-memory cache without it.
6. TimescaleDB is optional — engine falls back to SQLite data lake.

---

## 📜 License
Personal use. Not financial advice.
