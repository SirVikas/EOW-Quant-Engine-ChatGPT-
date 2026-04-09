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
    REDIS_URL: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # ── TimescaleDB ──────────────────────────────────────────────────────────
    DB_URL: str = Field(
        default="postgresql+asyncpg://quant:quant@localhost:5432/eow_quant",
        env="DB_URL",
    )

    # ── Trading Mode ─────────────────────────────────────────────────────────
    TRADE_MODE: Literal["PAPER", "LIVE"] = Field(default="PAPER", env="TRADE_MODE")

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
    SLIPPAGE_EST: float = 0.0012          # Realistic slippage (was 0.03%, observed ~0.15%)

    # ── Genome Engine ────────────────────────────────────────────────────────
    GENOME_CYCLE_MINUTES: int = 60         # Mutation cycle interval
    GENOME_POPULATION: int = 20            # Shadow strategies per cycle
    GENOME_LOOKBACK_HOURS: int = 24        # Backtest window (fresh data)
    GENOME_PROMOTE_WIN_RATE: float = 0.55  # Min win-rate to promote (raised: 52%→55%)
    GENOME_PROMOTE_PF: float = 1.5         # Min profit-factor to promote (raised: 1.3→1.5)

    # ── Self-Healing ─────────────────────────────────────────────────────────
    HEAL_INTERVAL_SECONDS: int = 60
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
    ATR_MULT_SL: float = 2.0              # Tightened 2.5→2.0: smaller loss per loser
    ATR_MULT_TP: float = 3.0              # Lowered 4.5→3.0: more achievable targets
    BB_PERIOD: int = 20
    BB_STD: float = 2.5                   # Widened 2.2→2.5: only trade extreme BB deviations

    model_config = {"env_file": ".env", "extra": "ignore"}


# ── Singleton ────────────────────────────────────────────────────────────────
cfg = EngineConfig()


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
