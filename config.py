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

    # ── Phase 4: Profit Engine ───────────────────────────────────────────────
    # RR Engine
    MIN_RR_RATIO: float = 1.5            # Minimum TP/SL ratio to accept a trade

    # Trade Scorer
    MIN_TRADE_SCORE: float = 0.60        # Minimum composite alpha score (0–1)
    MAX_COST_FRACTION: float = 0.20      # Max cost as fraction of gross TP (matches 5× fee rule)

    # Capital Allocator
    MAX_CAPITAL_PER_TRADE: float = 0.05  # Max 5% of equity per trade
    DAILY_RISK_CAP: float = 0.03         # Max 3% of equity risked per day

    # Trade Manager
    PARTIAL_TP_R: float = 1.5            # Book 50% position at 1.5R profit

    # ── Phase 5: EV Engine + Adaptive Intelligence ───────────────────────────
    # EV Engine
    EV_MIN_TRADES: int = 10             # Minimum history before EV gate activates
    EV_WINDOW: int = 30                 # Rolling trade window for EV calculation
    EV_BOOTSTRAP_PASS: bool = True      # Allow trades when < EV_MIN_TRADES (bootstrap)

    # Adaptive Scorer
    ADAPTIVE_LR: float = 0.05          # Weight learning rate per trade outcome
    ADAPTIVE_MIN_WEIGHT: float = 0.05  # Floor for any single factor weight
    ADAPTIVE_MAX_WEIGHT: float = 0.40  # Ceiling for any single factor weight

    # Confidence Decay Engine
    DECAY_FREQ_WINDOW_MIN: int = 30    # Signal frequency tracking window (minutes)
    DECAY_FREQ_MAX: int = 3            # Signals above this count trigger decay
    DECAY_PER_EXTRA: float = 0.10      # Confidence reduction per extra signal (10%)
    DECAY_MIN_FACTOR: float = 0.70     # Minimum decay factor (max 30% reduction)

    # Drawdown Controller
    DD_SOFT_CUT_AT: float = 0.05       # 5% DD → 0.75× size
    DD_HARD_CUT_AT: float = 0.10       # 10% DD → 0.50× size
    DD_STOP_AT: float = 0.15           # 15% DD → STOP all new trades

    # Regime Memory
    REGIME_MEMORY_WINDOW: int = 50     # Rolling trades per (regime, strategy) pair

    # ── Phase 5.1: Activation + Exploration Control ──────────────────────────
    # Trade Activator — prevents system freeze by relaxing filters
    ACTIVATOR_T1_MIN: int = 30           # Minutes of no trade → Tier 1 relaxation
    ACTIVATOR_T2_MIN: int = 60           # Minutes of no trade → Tier 2 relaxation
    ACTIVATOR_T3_MIN: int = 90           # Minutes of no trade → Tier 3 relaxation
    ACTIVATOR_T1_VOL_MULT: float = 0.60  # Volume threshold multiplier at Tier 1
    ACTIVATOR_T2_VOL_MULT: float = 0.40  # Volume threshold multiplier at Tier 2
    ACTIVATOR_T3_VOL_MULT: float = 0.30  # Volume threshold multiplier at Tier 3
    ACTIVATOR_T1_SCORE: float = 0.55     # Relaxed score threshold at Tier 1
    ACTIVATOR_T2_SCORE: float = 0.50     # Relaxed score threshold at Tier 2 / T3

    # Exploration Engine — 10% learning trades
    EXPLORE_RATE: float = 0.10           # Fraction of signal slots for exploration
    EXPLORE_SIZE_MULT: float = 0.25      # Size multiplier for exploration trades
    EXPLORE_SCORE_MIN: float = 0.45      # Absolute score floor for exploration
    EXPLORE_EV_FLOOR: float = 0.50       # Max allowed EV negative fraction of est_risk
    EXPLORE_DAILY_LOSS_CAP: float = 0.02 # Max daily equity loss from exploration

    # Adaptive Filter Engine — dynamic threshold tuning
    AF_RELAX_AFTER_MIN: int = 60         # Relax filters after N minutes without trade
    AF_TIGHTEN_AFTER_LOSSES: int = 3     # Tighten after N consecutive losses
    AF_RELAX_STEP: float = 0.05          # Score relaxation per step
    AF_TIGHTEN_STEP: float = 0.05        # Score tightening per step
    AF_MAX_RELAX: float = 0.15           # Maximum cumulative relaxation
    AF_MAX_TIGHTEN: float = 0.15         # Maximum cumulative tightening

    # Smart Fee Guard — RR-aware fee tolerance
    SFG_HIGH_RR_THRESHOLD: float = 3.0  # RR above this → high-RR tolerance
    SFG_HIGH_RR_FEE_MAX: float = 0.35   # Max fee/TP fraction for high-RR trades
    SFG_NORMAL_FEE_MAX: float = 0.20    # Max fee/TP fraction for normal trades

    # Trade Flow Monitor — frequency and health tracking
    TFM_WINDOW_MIN: int = 60             # Rolling window for trade flow metrics

    # ── Phase 6: Stability + Profit Consistency ───────────────────────────────
    # EV Confidence Engine — EV-tier-based sizing
    EVC_HIGH_THRESHOLD: float = 0.15    # EV ≥ 0.15 → HIGH_CONF (full size)
    EVC_MID_THRESHOLD: float = 0.05     # EV ≥ 0.05 → MEDIUM_CONF (normal size)
    EVC_HIGH_SIZE_MULT: float = 1.00    # HIGH_CONF size multiplier
    EVC_MID_SIZE_MULT: float = 1.00     # MEDIUM_CONF size multiplier
    EVC_LOW_SIZE_MULT: float = 0.70     # LOW_CONF size multiplier (EV barely positive)

    # Loss Cluster Controller — consecutive-loss circuit breaker
    LCC_REDUCE_AFTER: int = 3           # Consecutive losses → reduce to 50%
    LCC_PAUSE_AFTER: int = 5            # Consecutive losses → pause trading
    LCC_PAUSE_MINUTES: int = 30         # Pause duration in minutes
    LCC_REDUCE_SIZE_MULT: float = 0.50  # Size multiplier when clustering detected

    # Streak Intelligence Engine — hot/cold streak detection
    SE_WIN_STREAK_MIN: int = 3          # Consecutive wins to declare HOT streak
    SE_LOSS_STREAK_MIN: int = 3         # Consecutive losses to declare COLD streak
    SE_HOT_SCORE_ADJ: float = -0.03     # Score_min delta on HOT (negative = relax)
    SE_COLD_SCORE_ADJ: float = 0.05     # Score_min delta on COLD (positive = tighten)

    # Capital Recovery Engine — intelligent size restoration after drawdown
    CRE_DEFENSIVE_DD: float = 0.05      # Begin defensive sizing above this DD
    CRE_RECOVERY_SIZE_MIN: float = 0.70 # Minimum size during defensive/early recovery
    CRE_RECOVERY_STEP_PCT: float = 0.10 # Fraction of full recovery per step (unused directly)

    # Exploration Guard — prevents exploration from causing uncontrolled damage
    EG_DAILY_LOSS_CAP_PCT: float = 0.02 # Disable exploration when daily loss ≥ 2%

    # ── Phase 7: Profit Maximization + Edge Amplification ─────────────────────
    # Trade Ranker — edge prioritization engine
    TR_MIN_RANK_SCORE: float = 0.60       # Trades below this rank are rejected
    TR_EV_WEIGHT: float = 0.30            # Weight for EV score in composite rank
    TR_TRADE_SCORE_WEIGHT: float = 0.25   # Weight for adaptive trade score
    TR_REGIME_WEIGHT: float = 0.25        # Weight for regime alignment score
    TR_HISTORY_WEIGHT: float = 0.20       # Weight for historical performance score

    # Capital Concentrator — allocate more to top-ranked trades
    CC_BAND_LOW_MIN: float = 0.60         # Band lower bound (maps to 0.5× mult)
    CC_BAND_LOW_MAX: float = 0.70         # Band upper bound
    CC_BAND_MID_MIN: float = 0.70         # Band lower bound (maps to 1.0× mult)
    CC_BAND_MID_MAX: float = 0.80
    CC_BAND_HIGH_MIN: float = 0.80        # Band lower bound (maps to 1.5× mult)
    CC_BAND_HIGH_MAX: float = 0.90
    CC_BAND_ELITE_MIN: float = 0.90       # Band lower bound (maps to 2.0× mult)
    CC_MULT_LOW: float = 0.50
    CC_MULT_MID: float = 1.00
    CC_MULT_HIGH: float = 1.50
    CC_MULT_ELITE: float = 2.00
    CC_MAX_POSITION_PCT: float = 0.05     # Hard cap: max % equity per trade

    # Edge Amplifier — boost TP and trailing aggressiveness on elite setups
    EA_EV_THRESHOLD: float = 0.15         # Minimum EV for amplification
    EA_RANK_THRESHOLD: float = 0.80       # Minimum rank score for amplification
    EA_VOL_RATIO_THRESHOLD: float = 1.5   # Minimum volume ratio for amplification
    EA_TP_BOOST_MULT: float = 1.25        # TP target multiplier when amplified
    EA_TRAIL_BOOST_MULT: float = 1.20     # Trailing SL aggressiveness multiplier

    # Trade Competition Engine — select best N trades per cycle
    TCE_MAX_CONCURRENT: int = 3           # Maximum trades accepted per cycle
    TCE_MIN_RANK_GAP: float = 0.05        # Minimum rank difference to prefer one over another

    # Edge Memory Engine — remember what works
    EM_WINDOW: int = 50                   # Rolling trades per (strategy, symbol, regime) key
    EM_MIN_TRADES: int = 5                # Minimum trades before memory boost activates
    EM_BOOST_MAX: float = 0.15            # Maximum positive boost to rank score
    EM_PENALTY_MAX: float = 0.15          # Maximum negative penalty to rank score
    EM_WIN_RATE_BOOST_THRESHOLD: float = 0.60   # Win rate above this → boost
    EM_WIN_RATE_PENALTY_THRESHOLD: float = 0.40 # Win rate below this → penalize

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
