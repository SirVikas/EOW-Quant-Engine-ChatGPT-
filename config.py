"""
EOW Quant Engine — Master Configuration
All tunable parameters live here. Export → re-import to re-tune the engine.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal
import os

# Single source of truth for the application version.
# Update this when making significant changes — dashboard and all reports read from here.
APP_VERSION = "1.95.0"

# PHOENIX NEXUS — Institutional Intelligence Layer
PCCP_VERSION = "1.0.0"   # v1.0: PHOENIX Central Control Plane
CTAO_VERSION = "1.0.0"   # v1.0: CT Scan Autonomous Orchestrator
KG_VERSION = "1.0.0"            # v1.0: Knowledge Graph Engine
STRATEGIC_MEMORY_VERSION = "1.0.0"   # v1.0: Strategic Memory Engine
ECON_INTELLIGENCE_VERSION = "1.0.0"  # v1.0: Economic Intelligence Engine

DIGITAL_TWIN_V2_VERSION = "1.0.0"     # v1.0: Digital Twin Engine v2
EVOLUTION_GOV_VERSION = "1.0.0"       # v1.0: Evolution Governance System
PCAO_EXECUTIVE_VERSION = "1.0.0"      # v1.0: PCAO Executive Layer
META_GOV_VERSION = "1.0.0"            # v1.0: Meta Governance Layer
CONSTITUTION_VERSION = "1.0.0"        # v1.0: Constitution Engine
EPISTEMIC_VERSION = "1.0.0"           # v1.0: Epistemic Intelligence Layer
TRUST_FABRIC_VERSION = "1.0.0"        # v1.0: Unified Trust Fabric
AUTO_IMPROVEMENT_VERSION = "1.0.0"    # v1.0: Autonomous Improvement Loop

REAL_MARKET_VALIDATION_VERSION = "1.0.0"   # v1.0: Real Market Validation Layer
EVIDENCE_WAREHOUSE_VERSION = "1.0.0"       # v1.0: Institutional Evidence Warehouse
PERF_ATTRIBUTION_VERSION = "1.0.0"         # v1.0: Multi-Horizon Performance Attribution
REGIME_INTELLIGENCE_VERSION = "1.0.0"      # v1.0: Regime Intelligence Layer
BOARD_GOVERNANCE_VERSION = "1.0.0"         # v1.0: Executive Board Governance
REPORTING_HUB_VERSION = "1.0.0"            # v1.0: Unified Reporting Hub
LINEAGE_VERSION = "1.0.0"                  # v1.0: Snapshot & Lineage System
HUMAN_GOVERNANCE_VERSION = "1.0.0"         # v1.0: Human Governance Framework
DISASTER_RECOVERY_VERSION = "1.0.0"       # v1.0: Disaster Recovery & Continuity
MATURITY_SCORECARD_VERSION = "1.0.0"      # v1.0: Institutional Maturity Scorecard
VERIFICATION_SUITE_VERSION = "1.0.0"      # v1.0: Institutional Verification Suite

INSTITUTIONAL_MEMORY_VERSION = "1.0.0"       # v1.0: Institutional Memory Layer
META_KNOWLEDGE_VERSION = "1.0.0"             # v1.0: Meta Knowledge Layer
EVOLUTION_PLANNING_VERSION = "1.0.0"         # v1.0: Evolution Planning Layer
COLLECTIVE_INTELLIGENCE_VERSION = "1.0.0"    # v1.0: Collective Intelligence Layer
CAPABILITY_GOVERNANCE_VERSION = "1.0.0"      # v1.0: Capability Governance Layer
DIGITAL_DNA_VERSION = "1.0.0"                # v1.0: Digital DNA Layer
KNOWLEDGE_SYNTHESIS_VERSION = "1.0.0"        # v1.0: Knowledge Synthesis Layer
WAR_GAMING_VERSION = "1.0.0"                 # v1.0: War Gaming Layer
ECOSYSTEM_INTELLIGENCE_VERSION = "1.0.0"     # v1.0: Ecosystem Intelligence Layer
CIVILIZATION_ORCHESTRATOR_VERSION = "1.0.0"  # v1.0: Civilization Orchestrator Layer

DATA_GOVERNANCE_VERSION = "1.0.0"           # v1.0: Data Governance Layer
MODEL_GOVERNANCE_VERSION = "1.0.0"          # v1.0: Model Governance Layer
DECISION_INTELLIGENCE_VERSION = "1.0.0"     # v1.0: Decision Intelligence Layer
WORKFLOW_ORCHESTRATION_VERSION = "1.0.0"    # v1.0: Workflow Orchestration Layer
RESOURCE_ECONOMICS_VERSION = "1.0.0"        # v1.0: Resource Economics Layer
CHANGE_MANAGEMENT_VERSION = "1.0.0"         # v1.0: Change Management Layer
SERVICE_GOVERNANCE_VERSION = "1.0.0"        # v1.0: Service Governance Layer
DEPENDENCY_GOVERNANCE_VERSION = "1.0.0"     # v1.0: Dependency Governance Layer
EXECUTIVE_MANAGEMENT_VERSION = "1.0.0"      # v1.0: Executive Management Layer
FEDERATION_VERSION = "1.0.0"                # v1.0: Federation Layer

KNOWLEDGE_OPERATIONS_VERSION = "1.0.0"
WORKFORCE_MANAGEMENT_VERSION = "1.0.0"
CAPITAL_COMMAND_VERSION = "1.0.0"
RISK_COMMAND_VERSION = "1.0.0"
ORGANIZATION_DESIGN_VERSION = "1.0.0"
STRATEGY_OFFICE_VERSION = "1.0.0"
RESOURCE_PLANNING_VERSION = "1.0.0"
ECOSYSTEM_GOVERNANCE_VERSION = "1.0.0"
INSTITUTIONAL_ECONOMICS_VERSION = "1.0.0"
META_CIVILIZATION_VERSION = "1.0.0"

STRATEGY_TRUTH_VERSION = "1.0.0"
LIVE_MARKET_LAB_VERSION = "1.0.0"
ALPHA_ATTRIBUTION_VERSION = "1.0.0"
LONG_HORIZON_VALIDATION_VERSION = "1.0.0"
REGIME_SURVIVABILITY_VERSION = "1.0.0"
OPERATIONS_CENTER_VERSION = "1.0.0"
BENCHMARKING_VERSION = "1.0.0"
ECONOMIC_PROOF_VERSION = "1.0.0"

NEXUS_NAME    = "PHOENIX NEXUS"
NEXUS_VERSION = "3.2.0"
NEXUS_LAYERS  = ["IMRAF", "DIAL", "AEOS", "EMA", "EGI"]
NEXUS_PENDING = ["KGE", "HKE", "AEG"]

# OBSERVATORY-X — Institutional Observability Layer  (FTD-OBSX-CORTEX-DASHBOARD-001)
OBSX_NAME    = "OBSERVATORY-X"
OBSX_VERSION = "1.5.0"   # v1.5: Economic Survivability Engine
OBSX_COMPONENTS = ["registry", "scheduler", "health_monitor", "lineage_tracker",
                   "inspector", "defect_engine", "recommendation_engine",
                   "truth_layer", "trust_engine", "ownership", "nexus_bridge",
                   "outcome_registry", "cemetery", "cross_correlator", "precedent_library",
                   "disease_registry", "economic_outcome_ledger", "board_reports",
                   "long_term_archive", "recommendation_reality_engine"]

# CORTEX — Institutional Governance Layer  (FTD-OBSX-CORTEX-DASHBOARD-001)
CORTEX_NAME    = "CORTEX"
CORTEX_VERSION = "1.5.0"   # v1.5: Governance Consistency Audit + Amendment Impact Tracker
CORTEX_COMPONENTS = ["module_registry", "dependency_mapper", "conflict_engine",
                     "influence_matrix", "blame_engine", "constitution",
                     "counterfactual_engine", "constitutional_amendment",
                     "constitutional_precedents", "governance_replay",
                     "constitutional_court", "governance_case_law", "governance_simulator",
                     "constitutional_history", "constitutional_commentary", "governance_stress_test"]

# PHOENIX TRUST PROGRAM (PTP) — Trust Validation Layer
PTP_NAME    = "PHOENIX TRUST PROGRAM"
PTP_VERSION = "1.6.0"   # v1.6: Evidence Accumulation Report (multi-regime + survival)
PTP_PILLARS = ["RECOMMENDATION_ACCURACY", "INVESTIGATION_ACCURACY",
               "BLAME_ACCURACY", "COUNTERFACTUAL_ACCURACY", "CONFLICT_ACCURACY"]

# AEG Pipeline
AEG_PIPELINE_VERSION = "1.3.0"  # v1.3: Shadow Mode, Longitudinal Tracker

# PCAO — Planning, Control, Autonomy, and Oversight
PCAO_VERSION = "0.5.0"   # v0.5: Board Accuracy Ledger, Executive Scorecard, Strategic Forecast Engine
AEG_VALIDATION_VERSION = "1.0.0"  # v1.0: AEG Validation Program (shadow evidence, promotion accuracy, readiness index)
NEXUS_IHI_VERSION      = "1.1.0"  # v1.1: Validation Suite + Institutional Learning Engine
CORTEX_GMETRICS_VERSION = "1.0.0" # v1.0: Governance Metrics (Constitutional KPIs, Amendment Outcomes)
NEXUS_MATURITY_VERSION  = "1.0.0"  # v1.0: 20 Institutional Maturity Reports (GAP-EM/VM/EI/IL-01..05)

# NEXUS — Evidence Supremacy Engine
NEXUS_ESE_VERSION = "1.0.0"   # v1.0: Evidence Supremacy Automation

# v1.78.0 — POST-v1.77.0 Independent Architectural Gap Review
OBSERVABILITY_PLATFORM_VERSION = "1.0.0"   # v1.0: Institutional Observability Platform
PORTFOLIO_INTELLIGENCE_VERSION = "1.0.0"   # v1.0: Portfolio Intelligence Layer
CAUSAL_INTELLIGENCE_VERSION = "1.0.0"      # v1.0: Causal Inference Engine
RESEARCH_LAB_VERSION = "1.0.0"             # v1.0: Institutional Research Lab
AGENT_FABRIC_VERSION = "1.0.0"             # v1.0: Multi-Agent Coordination Fabric
FORECASTING_ENGINE_VERSION = "1.0.0"       # v1.0: Strategic Forecasting Engine
SELF_DIAGNOSTICS_VERSION = "1.0.0"         # v1.0: Self-Diagnostic Reconstruction Engine
POLICY_GOVERNANCE_VERSION = "1.0.0"        # v1.0: Global Policy Governance System
INSTITUTIONAL_SCORECARD_VERSION = "1.0.0"  # v1.0: Continuous Institutional Scorecard
COMMAND_CENTER_VERSION = "1.0.0"           # v1.0: PHOENIX Command Center

DATA_ASSURANCE_VERSION = "1.0.0"           # v1.0: Data Assurance Layer
SIGNAL_CERTIFICATION_VERSION = "1.0.0"    # v1.0: Signal Certification Layer
DRIFT_DETECTION_VERSION = "1.0.0"         # v1.0: Drift Detection Layer
POSTMORTEM_VERSION = "1.0.0"              # v1.0: Postmortem System
READINESS_V2_VERSION = "1.0.0"            # v1.0: Continuous Readiness Engine v2

# v1.84.0 — POST-v1.83.0 Remaining Developer Gaps (evidence automation)
EVIDENCE_ORCHESTRATION_VERSION = "1.0.0"   # v1.0: Evidence Orchestration Engine
CERTIFICATION_PIPELINE_VERSION = "1.0.0"   # v1.0: Automated Certification Pipeline
ANOMALY_RESPONSE_VERSION = "1.0.0"         # v1.0: Automated Anomaly Response System
PROOF_MATURITY_VERSION = "1.0.0"           # v1.0: Proof Maturity Index
SELF_HEALING_PLAYBOOKS_VERSION = "1.0.0"   # v1.0: Self-Healing Playbook Framework

# PHOENIX Institutional Stack — ordered maturity progression
INSTITUTIONAL_STACK = [
    {"name": "Trading Engine",       "status": "ACTIVE",       "version": None},
    {"name": "NEXUS",                "status": "ACTIVE",       "version": NEXUS_VERSION},
    {"name": "OBSERVATORY-X",        "status": "OPERATIONAL",  "version": OBSX_VERSION},
    {"name": "CORTEX",               "status": "OPERATIONAL",  "version": CORTEX_VERSION},
    {"name": "PHOENIX TRUST PROGRAM","status": "ACCUMULATING", "version": PTP_VERSION},
    {"name": "AEG",                  "status": "OPERATIONAL",  "version": AEG_PIPELINE_VERSION},
    {"name": "PCAO",                 "status": "ACTIVE",       "version": PCAO_VERSION},
    {"name": "EVIDENCE SUPREMACY",   "status": "OPERATIONAL",  "version": NEXUS_ESE_VERSION},
]

# Institutional Evolution Timeline — for dashboard display
INSTITUTIONAL_TIMELINE = [
    {"version": "1.57.0", "event": "NEXUS v3.0 — IMRAF+DIAL+AEOS+EMA+EGI complete",    "layer": "NEXUS"},
    {"version": "1.60.0", "event": "OBSERVATORY-X v1.0 — Foundation complete",           "layer": "OBSX"},
    {"version": "1.62.0", "event": "CORTEX v1.0 — Governance foundation complete",       "layer": "CORTEX"},
    {"version": "1.63.0", "event": "NEXUS v3.2 — Trust Validation Platform",             "layer": "NEXUS"},
    {"version": "1.64.0", "event": "OBSX v1.0 + CORTEX v1.0 — Institutional layers declared", "layer": "STACK"},
    {"version": "1.65.0", "event": "OBSX v1.1 + CORTEX v1.1 — Gap coverage: Outcome Registry, Cemetery, Correlator, Precedent Library, Amendment Framework, Precedents, Replay, Risk Scoring + PTP v1.0", "layer": "STACK"},
    {"version": "1.66.0", "event": "OBSX v1.2 + CORTEX v1.2 — Maturity: Disease Registry, Economic Ledger, Board Reports, Constitutional Court, Case Law, Governance Simulator + PTP v1.1 Promotion Ladder + AEG Pipeline v1.0", "layer": "STACK"},
    {"version": "1.67.0", "event": "OBSX v1.3 + CORTEX v1.3 + PTP v1.2 + AEG v1.1 + PCAO v0.1 — Accuracy Ledger, Trust Decay/Revocation, Sandbox Stats, Leaderboard, Evidence Packages, Auto-Demotion, Constitutional History, Long-Term Archive, Trust Evidence Bridge, PCAO Foundation", "layer": "STACK"},
    {"version": "1.68.0", "event": "17 institutional gaps filled — Live Accuracy Validator, Reality Engine, Evidence Warehouse, AEG Sandbox Replay/Court/Damage/Rollback, Constitutional Commentary/Stress Test, Evidence Supremacy Engine, PCAO Program Manager/Resource Governor/Executive Board/Memory Commander", "layer": "STACK"},
]


class EngineConfig(BaseSettings):
    # ── Binance API ─────────────────────────────────────────────────────────
    BINANCE_API_KEY: str = Field(default="", env="BINANCE_API_KEY")
    BINANCE_API_SECRET: str = Field(default="", env="BINANCE_API_SECRET")
    # qFTD-007: False — PAPER mode uses real Binance public endpoints; testnet
    # is only needed when explicitly set via env var BINANCE_TESTNET=true.
    BINANCE_TESTNET: bool = Field(default=False, env="BINANCE_TESTNET")

    # ── Redis ────────────────────────────────────────────────────────────────
    REDIS_URL: str = Field(default="redis://127.0.0.1:6379/0", env="REDIS_URL")

    # ── TimescaleDB ──────────────────────────────────────────────────────────
    DB_URL: str = Field(
        default="postgresql+asyncpg://quant:quant@localhost:5432/eow_quant",
        env="DB_URL",
    )

    # ── Trading Mode ─────────────────────────────────────────────────────────
    TRADE_MODE: Literal["PAPER", "LIVE"] = Field(default="PAPER", env="TRADE_MODE")
    # Emergency paper stress mode: prioritise trade throughput over quality gates.
    PAPER_SPEED_MODE: bool = Field(default=True, env="PAPER_SPEED_MODE")
    PAPER_TARGET_TRADES_PER_MIN: int = Field(default=20, env="PAPER_TARGET_TRADES_PER_MIN")
    # qFTD-007: FRESH = ignore prior trade history at boot (clean slate).
    # RESUME = replay DataLake trades to restore equity curve from last session.
    # Set env var BOOT_MODE=RESUME to re-enable session restore.
    BOOT_MODE: Literal["FRESH", "RESUME"] = Field(default="FRESH", env="BOOT_MODE")
    # qFTD-007-v2: seconds after boot during which gate failures do NOT trigger safe mode.
    # Engine transitions BOOTING→LIVE when indicator_validator.is_ready() OR elapsed≥grace.
    # With BYPASS_ALL_GATES=True the gate always passes regardless of BOOTING/LIVE state.
    # CandleBootstrapper seeds 120 candles at startup so indicators are warm < 60s;
    # 120s grace is sufficient and avoids a 15-min trade blackout.
    STARTUP_GRACE_SECONDS: float = Field(default=120.0, env="STARTUP_GRACE_SECONDS")
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
    MAX_RISK_PER_TRADE: float = 0.015      # 1.5% of equity per trade — reduced from 2.2% to cut fee drag and per-trade loss on fast-fails
    MIN_NOTIONAL_USDT: float = 20.0        # FTD-056-ACT: minimum trade notional floor — prevents micro-trades where $0.008 fee eats disproportionate share of small wins
    MAX_DRAWDOWN_HALT: float = 0.15        # Halt engine at 15% MDD
    KELLY_FRACTION: float = 0.25           # Conservative quarter-Kelly
    WIN_STREAK_SCALE_UP: int = 3           # Consecutive wins → scale up
    LOSS_STREAK_SCALE_DOWN: int = 2        # Consecutive losses → scale down

    # ── Hard Limits (FTD-031C: SSOT — never hardcoded elsewhere) ────────────
    MAX_LEVERAGE_CAP: float = 3.0          # Max exposure/equity ratio — immutable
    KILL_SWITCH_THRESHOLD: float = 0.20    # Emergency stop threshold — immutable
    MIN_EQUITY_FLOOR: float = 0.50         # Equity must never drop below 50% initial — immutable

    # ── Binance Fee Schedule ─────────────────────────────────────────────────
    MAKER_FEE: float = 0.0002             # 0.02%
    TAKER_FEE: float = 0.0004             # 0.04%
    SLIPPAGE_EST: float = 0.0003          # 0.03% — realistic Binance futures slippage for major pairs
    # Economic-viability dial (lean gate 3b). Round-trip cost = 2×taker + 2×slippage
    # ≈ 0.14%. When the stop sits at ~0.2% the cost eats ~70% of every 1R risked, so
    # even +0.4R gross winners book net losses (Fee Destruction 150%). Require the
    # stop to clear MIN_SL_TO_COST_RATIO × round-trip cost so a trade can pay for
    # itself. THIS IS THE PROFIT-vs-VOLUME DIAL: 3.0 (SL ≥ ~0.42%, cost ≤ 33% of R)
    # prioritises profitability and cuts the cost-dominated micro-trades; lower it
    # toward 1.0 to restore maximum trade volume at the cost of expectancy.
    MIN_SL_TO_COST_RATIO: float = 3.0
    VOL_BASELINE_ATR_PCT: float = 0.20    # Baseline ATR% for dynamic edge premium
    VOL_PREMIUM_MULT: float = 0.05        # Small linear premium on required_r per unit ATR above baseline
    BASE_MIN_R: float = 1.50               # Minimum post-cost R — raised to enforce positive expectancy
    ATR_SLIPPAGE_MULT: float = 0.10       # Reduced from 0.20 — keeps per-trade ATR overhead proportionate
    # Per-regime minimum R thresholds — tuned for MAX PROFIT (PF-first)
    REGIME_MIN_R_TRENDING: float = 1.20        # qFTD-040: restore balanced gate so valid post-cost trades are not over-blocked
    REGIME_MIN_R_MEAN_REVERTING: float = 1.05  # qFTD-040: MR relies on win-rate; lower R floor prevents dry-spell lock
    REGIME_MIN_R_VOLATILE: float = 1.15        # qFTD-040: volatile moves justify moderate R floor

    # ── Limit Order / Price Chase (Alpha Preservation) ───────────────────────
    USE_LIMIT_ORDERS: bool = True         # Use limit orders to save fees & eliminate slippage
    LIMIT_ENTRY_OFFSET_BPS: float = 3.0  # Place limit 3 bps (0.03%) better than signal price
    PRICE_CHASE_TICKS: int = 5           # After N ticks without fill, move limit to market
    BREAKEVEN_TRIGGER_R: float = 0.40     # lowered 1.0→0.40: avg winning trade = 0.09R; BE at 1.0R never armed (99.8% of wins below 1.0R). 0.40R arms BE on trades that develop past the noise floor, protecting gains via trailing stop.
    SPEED_EXIT_TRIGGER_R: float = 2.00    # lowered 2.50→2.00 — with TP at 2.4R (ATR_MULT_TP=6.0), a 2.5R speed-exit trigger was unreachable dead code; 2.0R makes the stall exit meaningful near TP
    SPEED_EXIT_STALL_TICKS: int = 25      # raised 20→25 — more patience; TP=4.0R needs time to be reached
    BREAKEVEN_EPSILON_USDT: float = 0.05  # Net PnL band considered breakeven
    # BE stop locks cost + 0.1R so armed-BE exits book a small real win instead of a
    # fee-noise scratch. Scratches were 57% of exits and read as losses by the
    # win-rate, LCC streak, and RL reward layers, stalling all three at once.
    BREAKEVEN_PROFIT_LOCK_R: float = 0.10
    # Peak-proportional profit ratchet — caps exit giveback on sub-1R winners.
    # The price-space trail (1.5× initial risk) only lifts the stop above the
    # +0.10R BE floor once peak_r > ~1.6R, which this strategy never reaches, so
    # winners peaking ~0.5R gave the entire peak back to the BE floor (91/171
    # 'BE' exits, avg peak 0.51R → final ~+0.10R). Once peak_r clears
    # GIVEBACK_RATCHET_MIN_R, lock GIVEBACK_LOCK_FRACTION of the proven peak.
    # Strictly one-directional (only tightens the stop) so it can never widen
    # risk or convert a winner into a loss — it only trades rare upside recovery
    # for reliable capture of the common 0.5R peak.
    GIVEBACK_RATCHET_ENABLED: bool  = True
    GIVEBACK_RATCHET_MIN_R:  float = 0.50  # leave the 0.40-0.50R zone room (BE floor only)
    GIVEBACK_LOCK_FRACTION:  float = 0.50  # lock half of proven peak_r above the trigger
    # FTD-PHOENIX-ESR-001 Phase 3/6: Trade Duration Protection
    TRADE_MIN_HOLD_FAST_FAIL_SEC: float = 90.0  # FAST_FAIL cannot fire before 90s — eradicates sub-90s loss exits

    # ── Adaptive Mode Engine (tri-modal execution) ───────────────────────────
    # Range Scalper — fires in MEAN_REVERTING regime; eliminates NO_TRADE_SESSION
    RS_CVD_IMBAL_MIN: float = 0.60        # CVD imbalance floor (60% buy/sell concentration)
    RS_MIN_BB_WIDTH: float  = 0.10        # Skip BB scalp when band width < 0.10% (flat market)
    # VTP — Volatile Take-Profit (TREND_FOLLOW / SHORT_HUNT modes only)
    VTP_EXIT_MIN_R: float   = 1.00        # lowered 1.50→1.00 — exit-analysis (1831 trades): zero exits ever reached 1.5R; 1.0R stall exit banks medium winners after the partial books at 0.8R

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
    GENOME_MIN_AVG_R: float = 0.20             # lowered 0.50→0.20: 0.50 gate was mathematically unreachable — with 50% WR and 1.0R avg loss, passing avg_R≥0.50 requires avg_win≥2.0R; no candidate could ever promote. 0.20 is the original value and a realistic bar.
    # FTD-PHOENIX-GENOME-READINESS-001: minimum candles per symbol before evaluation is allowed
    GENOME_MIN_CANDLES_TO_EVALUATE: int = 50   # must have ≥ warmup_bars candles to run any meaningful backtest
    # FTD-PHOENIX-ESR-001 Phase 1: OOS Validation Hardening
    GENOME_OOS_PASSTHROUGH_ENABLED: bool = False  # False → insufficient OOS data = REJECTED (not auto-pass)
    GENOME_OOS_MIN_TRADES: int = 10               # minimum OOS trades required for oos_valid = True
    # FTD-PHOENIX-ESR-001 Phase 5: Fee Destruction Governance
    GENOME_PROMOTE_MAX_COST_DRAG_PCT: float = 30.0     # Gate 5: reject if fees consume >30% of gross PnL in backtest
    GENOME_ET_FDR_FREEZE_THRESHOLD: float = 50.0       # live fee_destruction_ratio above this → freeze DNA evolution
    GENOME_ET_NET_EXP_FREEZE_THRESHOLD: float = -0.15  # live net_expectancy below this → freeze DNA evolution
    GENOME_ET_FREEZE_MIN_TRADES: int = 100             # min live trades before ET feedback freeze activates

    # ── Self-Healing ─────────────────────────────────────────────────────────
    HEAL_INTERVAL_SECONDS: int = 45       # Reduced 60→45: faster ping accumulation for Network score
    MAX_RECONNECT_ATTEMPTS: int = 10

    # ── Regime Detection ─────────────────────────────────────────────────────
    REGIME_ADX_THRESHOLD: float = 20.0    # ADX > 20 → Trending (lowered for earlier detection)
    REGIME_ATR_MULT: float = 1.5          # ATR spike → Volatility Expansion

    # ── Strategy Defaults (DNA) ──────────────────────────────────────────────
    RSI_PERIOD: int = 14
    RSI_OVERSOLD: float = 30.0            # FTD-056-ACT: tightened 35→30 — demand more extreme oversold to filter false MR LONG signals (WR was 17% vs 30% breakeven)
    RSI_OVERBOUGHT: float = 70.0          # FTD-056-ACT: tightened 65→70 — demand more extreme overbought to filter false MR SHORT signals
    EMA_FAST: int = 12                    # Raised 8→12: reduce whipsaw noise
    EMA_SLOW: int = 21                    # qFTD-011: 50→21 — EMA50 needs 52 candles on 1-min; EMA21 fires after 23 min
    EMA_TREND: int = 34                   # qFTD-011: 100→34 — Fibonacci macro filter; min_len 102→36 candles
    ATR_PERIOD: int = 14
    ATR_MULT_SL: float = 2.5              # Widened 1.5→2.5: survives 1-min noise, fewer premature SL hits
    # Raw RR = ATR_MULT_TP / ATR_MULT_SL = 6.0/2.5 = 2.4×.
    # Exit-analysis evidence (1831 trades): TP at 10×ATR (4.0R) produced ZERO take-profit
    # exits — every winner was cut by BE/trail long before 4R. A TP that never fills is
    # not a target, it's decoration. 6×ATR (2.4R) is reachable within typical hold windows
    # while still clearing MIN_RR_RATIO=2.0 and the lean gate.
    ATR_MULT_TP: float = 6.0              # lowered 10.0→6.0: RR=2.4× — reachable TP beats a fantasy 4R target that filled 0 times
    BB_PERIOD: int = 20
    BB_STD: float = 2.0                   # Tightened 2.5→2.0: more frequent BB touches, better RR

    # ── Session-Adaptive Volatility + Sizing ──────────────────────────────────
    # Per-session ATR floor and position-size multipliers.
    # ASIA (00-05 UTC): ATR typically 40-50% lower than NY — the fixed 0.10% floor
    # blocks nearly every ASIA setup before the strategy or RL see it. A session-
    # proportionate threshold lets the bandit discover ASIA alpha independently.
    # LATE (19-23 UTC): moderate vol reduction post-NY close.
    # Size scale compensates for higher relative fee drag at lower ATR: smaller
    # position → same dollar risk → lower fee % of notional move.
    SESSION_MIN_ATR_PCT: dict = {
        # Expectancy audit (4647 trades): ASIA fee_destruction_ratio=143.5 (fees 143× gross PnL),
        # LONDON FDR=28.1. Both sessions have positive gross_expectancy but fees annihilate it.
        # Root cause: low-ATR moves are smaller than round-trip fee cost. Raising ATR floors
        # blocks setups where the potential move cannot overcome the fee burden.
        "ASIA":   0.20,   # raised 0.06→0.20: FDR=143.5 — ASIA setups are fee-annihilated at low ATR
        "LONDON": 0.15,   # REVERTED 0.20→0.15: Board held ATR increase pending ATR bucket analysis (no per-ATR-bucket WR data yet)
        "NY":     0.10,   # unchanged — NY is TRUE_NEGATIVE but not fee-collapsed; FDR=1.23
        "LATE":   0.07,   # unchanged — LATE is TRUE_NEGATIVE; lower vol but not fee-collapsed
    }
    SESSION_SIZE_SCALE: dict = {
        "ASIA":   0.30,   # reduced 0.50→0.30: further cut ASIA exposure; FDR=143.5 demands minimal size on surviving setups
        "LONDON": 0.50,   # reduced 0.75→0.50: diagnostic 2026-06-08 WR=12.1% — halve LONDON exposure until edge proven
        "NY":     1.00,   # unchanged
        "LATE":   0.70,   # unchanged — 70%: post-NY liquidity drop
    }

    # ── Phase 4: Profit Engine ───────────────────────────────────────────────
    # RR Engine
    # Raised 1.5→2.0. ATR_MULT_TP=10.0 gives 4.0× raw RR so min 2.0 is safe.
    # Higher RR floor ensures only setups with real edge pass — fee drag needs RR≥2 to overcome.
    MIN_RR_RATIO: float = 2.0            # raised 1.5→2.0 — quality gate; raw RR=4.0 safely clears this

    # Trade Scorer
    # Lowered 0.65→0.48: in quiet markets (ADX 17–19, low vol, flat RSI) realistic scores
    # are 0.43–0.54; threshold 0.55 blocked ALL signals. Quality enforced by RR gate (≥2.0)
    # and wider TP (10×ATR = 4.0× RR). A lower score-min + higher RR is superior to
    # high score-min + no trades. Math: TRENDING+ADX18+1.5xVol+RSI0 → score≈0.47.
    # Score formula: regime(25%) + volume(20%) + adx(20%) + rsi_slope(15%) + vol_exp(10%) + cost(10%)
    # Lowered 0.48→0.40: RSI governor requires RSI pullback for LONG (slope typically 0),
    # combined with low ADX, legitimate signals score 0.43–0.46 — all blocked at 0.48.
    MIN_TRADE_SCORE: float = 0.40        # lowered 0.48→0.40 — RSI pullback entries score ~0.43–0.46
    # qFTD-011: 0.10→0.15 — tighter cost ceiling was blocking small-notional valid trades.
    MAX_COST_FRACTION: float = 0.15      # qFTD-011: 0.10→0.15 — realistic fee ceiling

    # ── FTD-033: Cost + Execution + Alpha Engine ─────────────────────────────
    COST_MIN_NET_EDGE_PCT: float = 0.001    # Q4:B — min 0.1% net edge (notional-relative)
    COST_EXPLORE_LOSS_MAX_PCT: float = 0.0005  # Q7:A — exploration floor: max -0.05% edge
    COST_HIGH_EDGE_FACTOR: float = 0.75    # Q11:C — adaptive size when edge is marginal
    COST_SPREAD_EST_PCT: float = 0.0002    # Q3:A — bid-ask spread estimate 0.02%
    COST_SLIPPAGE_MAX_PCT: float = 0.0010  # Q2:C — slippage cap 0.10%
    # FTD-033 additions
    COST_AWARE_TRADING: bool = True        # Master switch — skip cost gate only in test envs
    EXPLORATION_MODE: bool = True          # Allow EXPLORE verdicts for marginal net edge signals
    MAX_COST_PCT: float = 0.005           # Flag symbols with round-trip cost > 0.5% notional
    # qFTD-033R Q5:C — adaptive fee handling (cost > threshold% of TP → reduce size)
    COST_HIGH_FEE_TP_PCT: float = 20.0    # cost_pct_of_tp > 20% → apply adaptive reduction
    COST_ADAPTIVE_FEE_MULT: float = 0.65  # size factor when fee is high vs TP
    # qFTD-033R Q7 — upgraded alpha formula factors
    ALPHA_RR_BASELINE: float = 1.5        # RR baseline for rr_factor normalisation
    ALPHA_RR_FACTOR_CAP: float = 2.0      # max rr_factor boost (prevents outlier over-sizing)
    ALPHA_DD_PENALTY_MULT: float = 2.0    # drawdown penalty strength (0.08 DD → 16% alpha reduction)

    # Capital Allocator
    MAX_CAPITAL_PER_TRADE: float = 0.05  # Max 5% of equity per trade
    DAILY_RISK_CAP: float = 0.06         # raised 3%→6% — allow more high-quality trades per day

    # Trade Manager
    # Raised 2.0→3.0 — with TP at 4.0R, booking 50% at 3.0R preserves upside while locking gains.
    # Previous 2.0R partial TP was dragging down avg win before the full TP move completed.
    PARTIAL_TP_R: float = 0.8            # lowered 1.5→0.8 — exit-analysis (1831 trades): max R ever reached was ~0.43 under the old tight trail; 1.5R partial never fired once. 0.8R is reachable with the wider trail and banks 50% as a real win.
    # Trailing Stop — 0.60×ATR (0.24R at SL=2.5×ATR) was the binding winner-cap: it choked
    # every trade at ~0.2-0.4R while losers ran to -1.0R (avg_win/avg_loss=0.65 → PF<1
    # at any achievable win rate). At 1.20×ATR the giveback is 0.48R: trades peaking
    # 0.40-0.61R fall back to the BE lock (+0.1R), above ~0.61R the trail takes over and
    # winners can develop toward partial (0.8R), VTP stall exit (1.0R+) and TP (2.4R).
    TRAIL_ATR_MULT: float = 1.20

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
    DECAY_FREQ_MAX: int = 200          # paper-speed mode baseline: allow very high signal frequency
    DECAY_PER_EXTRA: float = 0.10      # Confidence reduction per extra signal (10%)
    DECAY_MIN_FACTOR: float = 0.85     # raised 0.70→0.85 — less decay penalty; max 15% reduction so quiet-market signals still pass

    # Drawdown Controller
    DD_SOFT_CUT_AT: float = 0.05       # 5% DD → 0.75× size
    DD_HARD_CUT_AT: float = 0.10       # 10% DD → 0.50× size
    DD_STOP_AT: float = 0.15           # 15% DD → STOP all new trades

    # Regime Memory
    REGIME_MEMORY_WINDOW: int = 50     # Rolling trades per (regime, strategy) pair

    # ── Phase 5.1: Activation + Exploration Control ──────────────────────────
    # Trade Activator — prevents system freeze by relaxing filters
    # Patience raised — let quality signals come naturally, don't rush relaxation
    ACTIVATOR_T1_MIN: int = 5            # raised 3→5 min — more patience before Tier 1 relax
    ACTIVATOR_T2_MIN: int = 12           # raised 7→12 min — deeper relax takes longer
    ACTIVATOR_T3_MIN: int = 25           # raised 15→25 min — max relax only after real dry spell
    ACTIVATOR_T1_VOL_MULT: float = 0.50  # Volume threshold multiplier at Tier 1 (was 0.60)
    ACTIVATOR_T2_VOL_MULT: float = 0.30  # Volume threshold multiplier at Tier 2 (was 0.40)
    ACTIVATOR_T3_VOL_MULT: float = 0.20  # Volume threshold multiplier at Tier 3 (was 0.30, = floor)
    # Relaxed scores updated to align with new MIN_TRADE_SCORE=0.65.
    # Even in dry-spell relaxation, we stay above 0.53 to avoid junk trades.
    ACTIVATOR_T1_SCORE: float = 0.44     # lowered 0.57→0.44 — below MIN_TRADE_SCORE=0.48 for genuine dry-spell relaxation
    ACTIVATOR_T2_SCORE: float = 0.40     # lowered 0.53→0.40 — deeper relaxation; at the score floor

    # Exploration Engine — learning trades
    # Exploration cut to 3% — system is in loss. Exploration amplifies losses, not learning.
    EXPLORE_RATE: float = 0.03           # cut 0.10→0.03 — no exploration until PF > 1.0
    EXPLORE_SIZE_MULT: float = 0.25      # Size multiplier for exploration trades
    # qFTD-008-EDGE: 0.45→0.60 — exploration quality bar raised to match new baseline.
    EXPLORE_SCORE_MIN: float = 0.52      # lowered 0.60→0.52 — aligned with new MIN_TRADE_SCORE=0.48 baseline
    EXPLORE_EV_FLOOR: float = 0.50       # Max allowed EV negative fraction of est_risk
    EXPLORE_DAILY_LOSS_CAP: float = 0.02 # Max daily equity loss from exploration
    EXPLORE_MAX_TRADES_PER_DAY: int = 50 # EDP: 20→50 — learning mode needs more daily exploration
    # FTD-PHOENIX-ESR-001 Phase 4: Exploration Economics Review
    EXPLORE_MAX_COST_DRAG_PCT: float = 20.0  # block exploration when the strategy's backtest cost_drag exceeds 20%

    # Adaptive Filter Engine — dynamic threshold tuning
    # EDP: 20→5 min — adaptive filter must respond within minutes, not tens of minutes
    AF_RELAX_AFTER_MIN: int = 5          # EDP: 20→5 min — rapid score relaxation on dry spells
    AF_TIGHTEN_AFTER_LOSSES: int = 3     # Tighten after N consecutive losses
    AF_RELAX_STEP: float = 0.05          # Score relaxation per step
    AF_TIGHTEN_STEP: float = 0.03        # qFTD-010: 0.05→0.03 — recalibrated for raised MIN_TRADE_SCORE=0.70
    AF_MAX_RELAX: float = 0.15           # Maximum cumulative relaxation
    AF_MAX_TIGHTEN: float = 0.08         # qFTD-010: 0.15→0.08 — cap total tightening so eff_min never exceeds 0.78

    # Smart Fee Guard — RR-aware fee tolerance
    # qFTD-008-EDGE: fee ceilings cut in half. At round-trip cost 0.09% and TP=3%,
    # cost_fraction ≈ 3% — well below new 10% ceiling. Threshold is now meaningful
    # and will block genuinely fee-heavy micro-move setups.
    SFG_HIGH_RR_THRESHOLD: float = 3.0  # RR above this → high-RR tolerance
    SFG_HIGH_RR_FEE_MAX: float = 0.15   # qFTD-008-EDGE: 0.35→0.15 — high-RR still gets some slack
    SFG_NORMAL_FEE_MAX: float = 0.10    # qFTD-008-EDGE: 0.20→0.10 — aligned with MAX_COST_FRACTION

    # ── Execution Drive Policy (EDP) ────────────────────────────────────────────
    # Prevents system idle and forces execution when quality gates are too tight.
    EDP_ENABLED: bool = True                # Master switch for EDP
    EDP_IDLE_DETECTION_MIN: float = 1.0     # Declare DRIVE mode after this many minutes with no trades
    EDP_FORCE_SCORE: float = 0.58           # lowered 0.80→0.58 — reachable score; forces exec when score≥0.58 + RR≥2.0
    EDP_FORCE_RR: float = 2.0               # RR threshold for force-execute
    EDP_DRIVE_SCORE_OVERRIDE: float = 0.46  # lowered 0.55→0.46 — DRIVE mode threshold below MIN_TRADE_SCORE to actually override

    # Trade Flow Monitor — frequency and health tracking
    TFM_WINDOW_MIN: int = 60             # Rolling window for trade flow metrics

    # Trade frequency — paper-speed mode with BYPASS_ALL_GATES=True; lean gate is the quality filter
    MAX_TRADES_PER_HOUR: int = 1200      # paper-speed mode: 20 trades/min × 60
    MAX_TRADES_PER_DAY:  int = 28800     # paper-speed mode: 20 trades/min × 24h

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
    LCC_PAUSE_MINUTES: int = 10         # lowered 30→10 — FTD-054 forensics: 30-min pauses chained into 246-min dry spells (1400 LCC_PAUSED skips/session); 10 min breaks the cluster without freezing the engine
    LCC_REDUCE_SIZE_MULT: float = 0.50  # Size multiplier when clustering detected

    # Streak Intelligence Engine — hot/cold streak detection
    SE_WIN_STREAK_MIN: int = 3          # Consecutive wins to declare HOT streak
    SE_LOSS_STREAK_MIN: int = 3         # Consecutive losses to declare COLD streak
    SE_HOT_SCORE_ADJ: float = -0.03     # Score_min delta on HOT (negative = relax)
    SE_COLD_SCORE_ADJ: float = 0.07     # Score_min delta on COLD (raised 0.05→0.07 — firmer tightening during losing streaks)

    # Capital Recovery Engine — intelligent size restoration after drawdown
    CRE_DEFENSIVE_DD: float = 0.05      # Begin defensive sizing above this DD
    CRE_RECOVERY_SIZE_MIN: float = 0.70 # Minimum size during defensive/early recovery
    CRE_RECOVERY_STEP_PCT: float = 0.10 # Fraction of full recovery per step (unused directly)

    # ── FTD-040: Consistency Engine ──────────────────────────────────────────
    # Equity Volatility Control — rolling std-dev of equity returns
    CE_EQUITY_VOL_WINDOW: int   = 20     # Rolling window size (equity return points)
    CE_EQUITY_VOL_HIGH: float   = 0.015  # >1.5% std-dev → high volatility → brake size
    CE_EQUITY_VOL_NORMAL: float = 0.008  # >0.8% std-dev → elevated → soft 10% brake
    CE_EQUITY_VOL_HIGH_MULT: float = 0.75  # Size mult when equity volatility is high

    # Profit Smoothing — consecutive-win brake (prevents over-excitement scaling)
    CE_WIN_BRAKE_START: int    = 3       # Consecutive wins before brake engages
    CE_WIN_BRAKE_PER_WIN: float = 0.05  # Size reduction per additional win beyond start
    CE_WIN_BRAKE_MIN: float    = 0.70   # Floor for win-streak brake multiplier

    # Trend vs Noise Filter
    CE_NOISE_FILTER_MIN_TRADES: int = 3  # Min completed trades before hard vol brake

    # Rolling per-trade DD analysis window
    CE_ROLLING_DD_WINDOW: int = 10       # Last N trades tracked for pattern analysis

    # Exploration Guard — prevents exploration from causing uncontrolled damage
    EG_DAILY_LOSS_CAP_PCT: float = 0.02 # Disable exploration when daily loss ≥ 2%

    # ── Phase 6.5: Data Stability + Boot Readiness ───────────────────────────
    # Data Health Monitor
    # FTD-REF-055: 30→60s — ticks can arrive up to 60s apart during low-volume periods
    DHM_STALE_TICK_SEC: float = 60.0       # Tick older than this → stale (was 30.0)
    DHM_MAX_MISSING_CANDLE_PCT: float = 0.20  # >20% missing candles → unhealthy
    DHM_MIN_HEALTH_SCORE: float = 60.0     # Below this → block trading
    DHM_LATENCY_WARN_MS: float = 500.0     # Warn if WS latency > 500ms
    DHM_LATENCY_BLOCK_MS: float = 2000.0   # Block if WS latency > 2000ms

    # Indicator Validator
    # qFTD-032-R3: candle requirements reduced to align with STARTUP_GRACE (900s=15min).
    # RSI(14) requires period+1=15 candles minimum; IV_MIN_CANDLES must match to avoid
    # the coarse gate (_ind_ok_coarse = n>=14) passing while the full validator fails
    # (rsi_warmup: 14 < 15). At 14 candles: coarse=True but iv_result.ok=False → mismatch.
    IV_MIN_CANDLES: int = 15               # qFTD-fix: 14→15 — RSI(14) needs period+1=15
    IV_RSI_MIN_CANDLES: int = 15           # RSI needs at least RSI_PERIOD+1 candles
    IV_ADX_MIN_CANDLES: int = 14           # qFTD-032-R3: 20→14 — ADX_PERIOD=14, functional at period
    IV_ATR_MIN_CANDLES: int = 14           # qFTD-032-R3: 15→14 — ATR_PERIOD=14
    IV_VOLUME_MIN_CANDLES: int = 14        # qFTD-032-R3: 20→14 — 14-candle volume avg is sufficient

    # WS Stability Engine
    WSS_MAX_RECONNECTS_SAFE_MODE: int = 3  # Reconnects above this → safe mode
    WSS_LATENCY_WARN_MS: float = 500.0     # Log warning above this latency
    WSS_LATENCY_BLOCK_MS: float = 2000.0   # Block trading above this latency
    WSS_HEARTBEAT_INTERVAL_SEC: float = 15.0  # Heartbeat check interval
    WSS_STABILITY_WINDOW: int = 10         # Recent ticks to measure stability score

    # Boot Deployability Engine (Phase 6.5 — data-readiness gate)
    # FTD-REF-055: Max achievable score at boot (data=0, ind=0) = ws×0.25 + risk×0.20 = 45.0
    # Threshold must be ≤ 45 so gate can open during warmup; per-trade PTG still enforces safety.
    BDE_MIN_SCORE: float = 45.0            # FTD-REF-055: 70→45 — warmup-safe threshold
    BDE_DATA_HEALTH_WEIGHT: float = 0.30
    BDE_INDICATOR_WEIGHT: float = 0.25
    BDE_WS_STABILITY_WEIGHT: float = 0.25
    BDE_RISK_ENGINE_WEIGHT: float = 0.20

    # Safe Mode Controller
    SMC_RESUME_AFTER_MIN: float = 5.0      # Auto-resume safe mode check interval (minutes)
    # FTD-REF-055: 75→47→44 — must be < BDE_MIN_SCORE (45.0) so safe mode can exit during
    # warmup when indicators not ready. Max warmup score = ws×0.25+risk×0.20 = 45.0;
    # setting 47.0 > 45.0 caused permanent deadlock (score-based recovery impossible).
    SMC_MIN_SCORE_RESUME: float = 44.0     # Deployability score needed to exit safe mode (was 47.0)

    # ── Phase 6.6: Hard Gating + Safety Enforcement ───────────────────────────
    # Global Gate Controller — master trading permission authority
    # FTD-REF-055: thresholds aligned with warmup-safe BDE_MIN_SCORE
    GGL_DEPLOY_MIN_SCORE: float = 45.0     # FTD-REF-055: 70→45 — warmup-safe (was 70.0)
    GGL_WS_MIN_SCORE: float = 50.0         # Min WS stability score to allow trading
    GGL_DATA_MIN_HEALTH: float = 20.0      # FTD-REF-055: 60→20 — PTG enforces per-trade (was 60.0)
    GGL_CACHE_TTL_SEC: float = 1.0         # Seconds to cache last gate result

    # Hard Start Validator — pre-boot stop gate
    HSV_EXIT_ON_FAIL: bool = False          # True = sys.exit(1) on failure (set True for prod)
    HSV_MIN_CANDLES_BOOT: int = 20          # FTD-REF-055: 30→20 — boot hard-stop; higher than IV_MIN_CANDLES(15) intentional

    # Safe Mode Enforcer — runtime auto-protection
    # FTD-REF-055: triggers only on genuine WS/risk failures, not boot warmup
    SME_DEPLOY_LOW_THRESHOLD: float = 40.0  # FTD-REF-055: 65→40 — don't enter safe mode at boot
    SME_WS_LOW_THRESHOLD: float = 40.0      # Activate safe mode if WS stability drops here
    SME_DATA_LOW_THRESHOLD: float = 50.0    # Activate safe mode if data health drops here

    # Pre-Trade Gate — final validation before every trade execution
    PTG_REQUIRE_INDICATORS: bool = True      # Must indicators be validated for each trade
    PTG_REQUIRE_DATA_FRESH: bool = True      # Must data be fresh for each trade
    PTG_LOG_ALLOWED: bool = False            # Log allowed trades (set True for debugging)

    # Gate Logger
    GL_HISTORY_SIZE: int = 500              # Max gate events to retain in memory

    # ── Gate Bypass Mode ─────────────────────────────────────────────────────
    # True = bypass all 38 inline quality gates; only hard risk limits apply
    # (max drawdown halt, max leverage cap). Lean gate handles essential safety.
    # Paper mode: safe to run True. Flip False to re-engage full gate chain.
    # False = full quality-gate stack active (signal filter, RR gate, hour gate,
    # confidence threshold, fee check, sector guard).  True = paper warmup / data
    # collection mode — all gates bypassed, disabled strategy IDs allowed to trade.
    # Root cause of 29% WR: True lets noise generators trade without any filtering.
    BYPASS_ALL_GATES: bool = Field(default=False, env="BYPASS_ALL_GATES")

    # ── Phase 7: Profit Maximization + Edge Amplification ─────────────────────
    # Trade Ranker — edge prioritization engine
    # qFTD-008: was 0.60 — with EV_WEIGHT=0.55 and bootstrap ev=0.0, max achievable
    # rank during bootstrap = 0.45, making the 0.60 gate mathematically impossible.
    # Lowered to 0.30 so bootstrap trades (with trade_score≥0.65, good regime fit)
    # can execute and accumulate the 10-trade history needed for real EV computation.
    # After 10 trades, genuine EV drives rank above 0.30 naturally.
    TR_MIN_RANK_SCORE: float = 0.30       # qFTD-008: 0.60→0.30 — break EV bootstrap deadlock
    TR_EV_WEIGHT: float = 0.55            # Phase 7B: EV is dominant (was 0.30)
    TR_TRADE_SCORE_WEIGHT: float = 0.20   # Phase 7B: reduced (was 0.25)
    TR_REGIME_WEIGHT: float = 0.15        # Phase 7B: reduced (was 0.25)
    TR_HISTORY_WEIGHT: float = 0.10       # Phase 7B: reduced (was 0.20)

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
    TCE_MAX_CONCURRENT: int = 20          # paper-speed mode: allow high parallel order intake
    TCE_MIN_RANK_GAP: float = 0.05        # Minimum rank difference to prefer one over another

    # Edge Memory Engine — remember what works
    EM_WINDOW: int = 50                   # Rolling trades per (strategy, symbol, regime) key
    EM_MIN_TRADES: int = 5                # Minimum trades before memory boost activates
    EM_BOOST_MAX: float = 0.15            # Maximum positive boost to rank score
    EM_PENALTY_MAX: float = 0.15          # Maximum negative penalty to rank score
    EM_WIN_RATE_BOOST_THRESHOLD: float = 0.60   # Win rate above this → boost
    EM_WIN_RATE_PENALTY_THRESHOLD: float = 0.40 # Win rate below this → penalize

    # ── Phase 7B: EV Engine Evolution ────────────────────────────────────────
    # Performance-history scaling (applied inside EVEngine.evaluate)
    P7B_PERF_MIN_TRADES: int = 5               # Trades before perf scaling activates
    P7B_PERF_WIN_THRESHOLD: float = 0.65       # Win-rate above this → perf boost
    P7B_PERF_LOSS_THRESHOLD: float = 0.40      # Win-rate below this → perf penalty
    P7B_PERF_BOOST: float = 1.20               # EV multiplier for strong historical perf
    P7B_PERF_PENALTY: float = 0.80             # EV multiplier for weak historical perf

    # Drawdown dampening
    P7B_DD_MAX: float = 0.20                   # DD fraction above which EV is forced ≤ 0

    # Regime-confidence scaling
    P7B_REGIME_CONF_HIGH: float = 0.70         # Confidence above this → regime boost
    P7B_REGIME_CONF_LOW: float = 0.30          # Confidence below this → regime penalty
    P7B_REGIME_BOOST: float = 1.15             # EV multiplier for high regime confidence
    P7B_REGIME_PENALTY: float = 0.85           # EV multiplier for low regime confidence

    # CapitalConcentrator direct-EV sizing
    P7B_EV_HIGH_THRESHOLD: float = 0.15        # EV above this → CC boost
    P7B_EV_LOW_THRESHOLD: float = 0.03         # EV below this → CC penalty
    P7B_EV_CC_BOOST: float = 1.50              # Proposed-risk multiplier for high-EV trades
    P7B_EV_CC_PENALTY: float = 0.70            # Proposed-risk multiplier for low-EV trades

    # ── FTD-029: Correction Proposal — confidence-scaled change bounds ────────
    CORRECTION_CONF_HIGH: float = 80.0              # Confidence >= this → high change bound
    CORRECTION_CONF_MED: float = 60.0               # Confidence >= this → medium change bound
    CORRECTION_MAX_CHANGE_HIGH: float = 0.15        # Max param change at high confidence
    CORRECTION_MAX_CHANGE_MED: float = 0.10         # Max param change at medium confidence
    CORRECTION_MAX_CHANGE_LOW: float = 0.05         # Max param change at low confidence

    # ── FTD-030: Autonomous Background Intelligence Loop ──────────────────────
    AUTO_INTELLIGENCE_ENABLED: bool = True          # Master switch for autonomous loop
    AUTO_INTELLIGENCE_INTERVAL_MIN: float = 5.0     # Minutes between correction cycles
    AUTO_INTELLIGENCE_MIN_TRADES: int = 30          # Minimum trades before auto-correction fires
    AUTO_INTELLIGENCE_MIN_SCORE: float = 55.0       # Min FTD-028 meta_score to allow correction
    AUTO_INTELLIGENCE_POST_WAIT_TRADES: int = 5     # Trades to wait before post-correction check
    AUTO_INTELLIGENCE_MAX_DAILY_CYCLES: int = 12    # Hard cap: corrections per 24h session

    # ── FTD-031: Performance Optimization + Latency Control ───────────────────
    # Master switch
    PERF_ENABLED: bool = True                       # Enable FTD-031 performance layer

    # Latency targets (ms)
    PERF_LATENCY_TARGET_MS: float = 100.0           # Q1-B: recommended target per cycle
    PERF_LATENCY_WARN_MS: float = 75.0              # Warn at 75% of target
    PERF_LATENCY_BREACH_MS: float = 100.0           # Alert + degrade above this

    # Cache TTLs (seconds)
    PERF_CACHE_PATTERN_TTL_SEC: float = 60.0        # Pattern index cache TTL
    PERF_CACHE_VALIDATION_TTL_SEC: float = 30.0     # Validation result cache TTL
    PERF_CACHE_SIGNAL_TTL_SEC: float = 5.0          # Last signal state cache TTL
    PERF_CACHE_CONFIG_TTL_SEC: float = 300.0        # Config snapshot cache TTL

    # Async task queue
    PERF_QUEUE_MAX_SIZE: int = 500                  # Max pending background tasks
    PERF_QUEUE_WORKERS: int = 2                     # Concurrent background workers
    PERF_QUEUE_BACKLOG_WARN: int = 100              # Alert when backlog exceeds this

    # Rate limiting
    PERF_MAX_CYCLES_PER_MIN: int = 600              # Max run_cycle() calls per minute
    PERF_DASHBOARD_REFRESH_MAX_PER_SEC: float = 5.0 # Dashboard WS push rate cap
    PERF_API_RATE_MAX_PER_MIN: int = 300            # REST API request cap per minute

    # Memory management
    PERF_MAX_PATTERN_RECORDS: int = 10_000          # Hard cap on in-memory pattern entries
    PERF_JSONL_COMPACTION_THRESHOLD: int = 5_000    # Trigger JSONL compaction above this
    PERF_ARCHIVE_DAYS: int = 7                      # Archive records older than N days
    PERF_MEMORY_WARN_MB: float = 512.0              # Warn when process RSS exceeds this
    PERF_MEMORY_CRITICAL_MB: float = 1024.0         # Enter safe mode above this

    # Logging mode: "full" (dev) | "reduced" (prod) | "dynamic" (auto-switch)
    PERF_LOG_MODE: str = "dynamic"                  # Q10-C: dynamic logging strategy

    # Fail-safe / degraded mode
    PERF_SAFE_MODE_LATENCY_CONSECUTIVE: int = 5     # Breaches in a row → enter DEGRADED
    PERF_DEGRADED_SKIP_MODULES: list = []           # Modules to skip in DEGRADED mode
    PERF_SAFE_MODE_SKIP_MODULES: list = []          # Modules to skip in SAFE_MODE

    # Benchmark baseline
    PERF_BENCHMARK_ENABLED: bool = True             # Q17-A: mandatory benchmark
    PERF_BENCHMARK_WARMUP_CYCLES: int = 100         # Cycles before baseline is locked
    PERF_BENCHMARK_SYMBOLS: int = 5                 # Symbols for multi-symbol benchmark

    # Real-time vs batch classification (informational, used by async queue)
    # Real-time: signal, risk, correction  |  Batch: validation, learning, export
    PERF_BATCH_MODULES: list = [                    # Q12: modules routed to batch queue
        "export_engine",
        "deep_validation",
        "learning_engine",
    ]

    # ── FTD-031C: Diagnostics (disabled by default — developer use only) ──────
    DIAGNOSTICS_ENDPOINT_ENABLED: bool = False      # Enable /api/diagnostics/* endpoints

    # ── FTD-RCAF-001: Root Cause Attribution Framework ───────────────────────
    RCAF_ENABLED: bool = Field(default=True, env="RCAF_ENABLED")
    # Gates to shadow-log (all active by default; remove any to stop tracking it)
    RCAF_GATES: list = [
        "frequency_cooldown",
        "frequency_hourly_cap",
        "hour_avoidance",
        "atr_volatility",
        "volume_sleep",
        "sector_correlation",
        "risk_engine",
        "market_structure",
        "edge_engine",
        "adaptive_edge_engine",
        "regime_stability",
        "profit_guard",
        "smart_fee_guard",
        "ev_engine",
        "ev_confidence",
        "drawdown_controller",
    ]

    # ── Truth Engine (FTD-PHOENIX-ENTRY-EXIT-TRUTH-ENGINE-001) ──────────────────
    ETE_GATE_ENABLED:         bool  = Field(default=False, env="ETE_GATE_ENABLED")
    ETE_MIN_SCORE:            float = Field(default=45.0,  env="ETE_MIN_SCORE")
    XTE_FORCE_CLOSE_ENABLED:  bool  = Field(default=False, env="XTE_FORCE_CLOSE_ENABLED")
    XTE_ADVISORY_TSL_SCORE:   float = Field(default=35.0,  env="XTE_ADVISORY_TSL_SCORE")
    # FTD-094A: XTE observation layer — evidence generation only, no execution authority.
    # Default MUST remain False; flip only for an XTE calibration-collection phase.
    XTE_OBSERVE_ENABLED:      bool  = Field(default=False, env="XTE_OBSERVE_ENABLED")
    XTE_OBSERVE_ARCHIVE:      str   = Field(default="reports/xte_observations/xte_observations.jsonl", env="XTE_OBSERVE_ARCHIVE")
    # FTD-094A blueprint X1+X2: Exit Coordinator SHADOW — observes/validates live
    # exit-authority transitions, no write authority. Default MUST remain False.
    EXIT_COORDINATOR_SHADOW_ENABLED: bool = Field(default=False, env="EXIT_COORDINATOR_SHADOW_ENABLED")
    # GAP-C4: per-tick path capture for path-accurate counterfactual replay.
    # Extra storage; separate from observation so it can be enabled independently.
    XTE_OBSERVE_PATH_ENABLED: bool = Field(default=False, env="XTE_OBSERVE_PATH_ENABLED")
    XTE_PATH_ARCHIVE:         str  = Field(default="reports/xte_observations/xte_paths.jsonl", env="XTE_PATH_ARCHIVE")
    TRUTH_ENGINE_ENABLED:     bool  = Field(default=True,  env="TRUTH_ENGINE_ENABLED")

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
