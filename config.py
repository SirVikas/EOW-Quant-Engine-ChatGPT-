"""
EOW Quant Engine — Master Configuration
All tunable parameters live here. Export → re-import to re-tune the engine.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
import os


class EngineConfig(BaseSettings):
    # ── Binance API ─────────────────────────────────────────────────────────
    BINANCE_API_KEY: str = Field(default="", env="BINANCE_API_KEY")
    BINANCE_API_SECRET: str = Field(default="", env="BINANCE_API_SECRET")
    BINANCE_TESTNET: bool = Field(default=True, env="BINANCE_TESTNET")

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = Field(default="redis://127.0.0.1:6379/0", env="REDIS_URL")

    # ── TimescaleDB ──────────────────────────────────────────────────────────
    DB_URL: str = Field(
        default="postgresql+asyncpg://quant:quant@localhost:5432/eow_quant",
        env="DB_URL",
    )

    # ── Trading Mode ─────────────────────────────────────────────────────────
    TRADE_MODE: Literal["PAPER", "LIVE"] = Field(default="PAPER", env="TRADE_MODE")
    AUTH_ENABLED: bool = Field(default=False, env="AUTH_ENABLED")
    # Comma-separated origins, e.g. "http://localhost:8000,https://ops.example.com"
    ALLOWED_ORIGINS: str = Field(default="http://localhost:8000", env="ALLOWED_ORIGINS")
    # Comma-separated token:role pairs, e.g. "op_token:operator,admin_token:admin"
    CONTROL_API_KEYS: str = Field(default="", env="CONTROL_API_KEYS")

    # ── Universe ─────────────────────────────────────────────────────────────
    TOP_N_PAIRS: int = 30                  # How many USDT pairs to watch
    MIN_VOLUME_USDT: float = 20_000_000   # 24h min volume filter

    # ── Risk / Capital ───────────────────────────────────────────────────────
    INITIAL_CAPITAL: float = 1000.0        # USDT starting bankroll (paper)
    MAX_RISK_PER_TRADE: float = 0.015      # 1.5% of equity per trade (larger size → lower fee drag)
    MAX_DRAWDOWN_HALT: float = 0.15        # Halt engine at 15% MDD
    KELLY_FRACTION: float = 0.25           # Conservative quarter-Kelly
    WIN_STREAK_SCALE_UP: int = 3           # Consecutive wins → scale up
    LOSS_STREAK_SCALE_DOWN: int = 2        # Consecutive losses → scale down

    # ── Binance Fee Schedule ─────────────────────────────────────────────────
    MAKER_FEE: float = 0.0002             # 0.02%
    TAKER_FEE: float = 0.0004             # 0.04%
    SLIPPAGE_EST: float = 0.0003          # 0.03% — realistic Binance futures slippage for major pairs
    VOL_BASELINE_ATR_PCT: float = 0.20    # Baseline ATR% for dynamic edge premium
    VOL_PREMIUM_MULT: float = 0.05        # Small linear premium on required_r per unit ATR above baseline
    BASE_MIN_R: float = 1.10               # Fallback post-cost R threshold (was 1.20 — relaxed for more entries)
    ATR_SLIPPAGE_MULT: float = 0.10       # Reduced from 0.20 — keeps per-trade ATR overhead proportionate
    # Per-regime minimum R thresholds — relaxed for higher signal frequency
    REGIME_MIN_R_TRENDING: float = 1.10        # was 1.20 — still captures strong trends
    REGIME_MIN_R_MEAN_REVERTING: float = 1.05  # unchanged — high WR compensates
    REGIME_MIN_R_VOLATILE: float = 1.05        # was 1.15 — breakouts move fast

    # ── Limit Order / Price Chase (Alpha Preservation) ───────────────────────
    USE_LIMIT_ORDERS: bool = True         # Use limit orders to save fees & eliminate slippage
    LIMIT_ENTRY_OFFSET_BPS: float = 3.0  # Place limit 3 bps (0.03%) better than signal price
    PRICE_CHASE_TICKS: int = 5           # After N ticks without fill, move limit to market
    BREAKEVEN_TRIGGER_R: float = 0.5      # Move SL to BE+cost after this profit milestone
    SPEED_EXIT_TRIGGER_R: float = 1.0     # Enable speed-exit checks after this R
    SPEED_EXIT_STALL_TICKS: int = 8       # Exit if no new peak/trough in N ticks after >1R
    BREAKEVEN_EPSILON_USDT: float = 0.05  # Net PnL band considered breakeven

    # ── Genome Engine ────────────────────────────────────────────────────────
    GENOME_CYCLE_MINUTES: int = 3          # Reduced 5→3: faster evolution cycles
    GENOME_POPULATION: int = 20            # Shadow strategies per cycle
    GENOME_LOOKBACK_HOURS: int = 24        # Backtest window (fresh data)
    GENOME_PROMOTE_WIN_RATE: float = 0.50  # Reduced 0.55→0.50: achievable promotion gate
    GENOME_PROMOTE_PF: float = 1.2         # Reduced 1.5→1.2: achievable promotion gate
    # Phase 3 — OOS Validation & Execution-Cost Gating
    GENOME_OOS_SPLIT_RATIO: float = 0.70       # 70% candles for training, 30% held-out OOS test
    GENOME_OOS_MIN_PF: float = 1.0             # OOS profit-factor floor
    GENOME_OVERFITTING_MAX_RATIO: float = 2.5  # Relaxed 2.0→2.5: avoid over-penalising good fits
    GENOME_MIN_AVG_R: float = 0.20             # Relaxed 0.35→0.20: allow early-stage promotions

    # ── Self-Healing ─────────────────────────────────────────────────────────
    HEAL_INTERVAL_SECONDS: int = 45       # Reduced 60→45: faster ping accumulation for Network score
    MAX_RECONNECT_ATTEMPTS: int = 10

    # ── Regime Detection ─────────────────────────────────────────────────────
    REGIME_ADX_THRESHOLD: float = 20.0    # ADX > 20 → Trending (lowered for earlier detection)
    REGIME_ATR_MULT: float = 1.5          # ATR spike → Volatility Expansion

    # ── Strategy Defaults (DNA) ──────────────────────────────────────────────
    RSI_PERIOD: int = 14
    RSI_OVERSOLD: float = 35.0            # Raised 28→35: require more bearish momentum for SHORT
    RSI_OVERBOUGHT: float = 65.0          # Lowered 72→65: require less overbought for LONG entry
    EMA_FAST: int = 12                    # Raised 8→12: reduce whipsaw noise
    EMA_SLOW: int = 50                    # Raised 21→50: stronger trend confirmation
    EMA_TREND: int = 100                  # NEW: macro trend direction filter (price vs EMA100)
    ATR_PERIOD: int = 14
    ATR_MULT_SL: float = 2.5              # Widened 1.5→2.5: survives 1-min noise, fewer premature SL hits
    ATR_MULT_TP: float = 6.0              # Raised 4.0→6.0: gross RR = 6.0/2.5 = 2.4 — covers fees & slippage
    BB_PERIOD: int = 20
    BB_STD: float = 2.0                   # Tightened 2.5→2.0: more frequent BB touches, better RR

    model_config = {"env_file": ".env", "extra": "ignore"}


# ── Singleton ────────────────────────────────────────────────────────────────
cfg = EngineConfig()


def parse_allowed_origins(raw: str) -> list[str]:
    origins = [o.strip() for o in (raw or "").split(",") if o.strip()]
    return origins or ["http://localhost:8000"]


def parse_control_api_keys(raw: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for part in (raw or "").split(","):
        item = part.strip()
        if not item or ":" not in item:
            continue
        token, role = item.split(":", 1)
        token = token.strip()
        role = role.strip().lower()
        if token and role:
            out[token] = role
    return out


# ── Pastel UI Color Palette ──────────────────────────────────────────────────
PASTEL = {
    "mint":     "#E6FFFA",
    "lavender": "#FAF5FF",
    "sky":      "#EBF8FF",
    "peach":    "#FFF5F5",
    "lemon":    "#FEFCBF",
    "accent_green":  "#38A169",
    "accent_purple": "#805AD5",
    "accent_blue":   "#3182CE",
    "accent_red":    "#E53E3E",
    "text_dark":     "#1A202C",
    "text_muted":    "#718096",
}
