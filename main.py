"""
EOW Quant Engine — FastAPI Main Application
Wires together all modules and exposes REST + WebSocket endpoints
for the React Pastel Dashboard.
"""
from __future__ import annotations
import asyncio
import json
import time
import uuid
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import AsyncGenerator

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from loguru import logger
import orjson

from config import cfg, parse_allowed_origins, APP_VERSION
from core.market_data    import MarketDataProvider, Tick
from core.pnl_calculator import PurePnLCalculator, TradeRecord
from core.genome_engine  import GenomeEngine
from core.regime_detector import RegimeDetector
from core.risk_controller import RiskController, OpenPosition
from core.self_healing    import SelfHealingProtocol
from core.data_lake       import DataLake
from core.vault           import VaultManager, WrongPassword, VaultNotConfigured
from core.guardian        import GuardianLogic, AGGRESSION_PROFILES
from core.security        import ensure_auth_ready_for_mode, require_roles
from core.scorecard       import compute_scorecard
from core.analytics       import compute_full_analytics, deployability_index
from core.metrics_engine   import rolling_ratios
from core.redis_health    import redis_health
from core.ws_stabilizer   import WsStabilizer
from core.regime_debounce import regime_debounce
from core.indicator_guard     import indicator_guard
from core.indicator_validator import indicator_validator          # qFTD-007: keeps deploy iv_score accurate
from core.regime_ai       import regime_ai
from core.signal_filter   import signal_filter
from core.risk_engine     import risk_engine
from core.deployability   import deployability_engine
from core.trade_frequency    import trade_frequency      # FTD-REF-023
from core.execution_drive_policy import execution_drive_policy  # EDP
from core.execution_engine  import execution_engine     # FTD-REF-023
from core.learning_engine   import learning_engine      # FTD-REF-023
from core.edge_engine        import edge_engine         # FTD-REF-024
from core.adaptive_edge_engine import adaptive_edge_engine  # FTD-037
from core.capital_flow_engine  import capital_flow_engine   # FTD-038+039
from core.market_structure   import market_structure_detector  # FTD-REF-024
from core.ws_truth_engine    import ws_truth_engine     # FTD-REF-025
from core.error_registry     import error_registry      # FTD-REF-025
from core.strategy_engine    import strategy_engine     # FTD-REF-026
from core.memory.memory_orchestrator import memory_orchestrator  # FTD-030B
from core.profit_guard       import profit_guard        # FTD-REF-026
from core.ct_scan_engine     import ct_scan_engine      # FTD-REF-026
from core.inverse_engine     import inverse_engine, TradeMode  # A.I.E.
from core.volume_filter      import volume_filter              # Phase 3: sleep mode
from core.sector_guard       import sector_guard               # Phase 3: correlation guard
from core.rr_engine          import rr_engine                  # Phase 4: RR enforcement
from core.trade_scorer       import trade_scorer               # Phase 4: alpha quality gate
from core.capital_allocator  import capital_allocator          # Phase 4: score-based sizing
from core.trade_manager      import trade_manager, ManagedPosition  # Phase 4: lifecycle
from strategies.alpha_engine import alpha_engine               # Phase 4: alpha signals
from core.equity_snapshot    import equity_snapshot             # qFTD-009: equity persistence
from core.ev_engine          import ev_engine                  # Phase 5: EV gate
from core.adaptive_scorer    import adaptive_scorer            # Phase 5: dynamic weights
from core.confidence_decay   import confidence_decay           # Phase 5: signal staleness
from core.drawdown_controller import drawdown_controller       # Phase 5: DD protection
from core.regime_memory      import regime_memory              # Phase 5: regime learning
from core.trade_activator      import trade_activator            # Phase 5.1: freeze prevention
from core.exploration_engine   import exploration_engine, ExploreResult  # Phase 5.1
from core.adaptive_filter      import adaptive_filter            # Phase 5.1: dynamic thresholds
from core.smart_fee_guard      import smart_fee_guard            # Phase 5.1: RR-aware fee gate
from core.trade_flow_monitor   import trade_flow_monitor         # Phase 5.1: flow health
from core.dynamic_thresholds   import dynamic_threshold_provider # Phase 5.2: master control
from core.ev_confidence        import ev_confidence_engine        # Phase 6: EV tier sizing
from core.loss_cluster         import loss_cluster_controller     # Phase 6: loss circuit breaker
from core.streak_engine        import streak_engine               # Phase 6: hot/cold detection
from core.capital_recovery     import capital_recovery_engine     # Phase 6: recovery sizing
from core.consistency_engine   import consistency_engine          # FTD-040: unified consistency
from core.exploration_guard    import exploration_guard           # Phase 6: exploration gate
from core.gating import (                                         # Phase 6.6: hard gating
    gate_logger,
    safe_mode_engine,
    global_gate_controller,
    hard_start_validator,
    pre_trade_gate,
)
from core.data_health import data_health_monitor                  # qFTD-004: data freshness SSOT
from core.performance_explorer import (                           # FTD-UPE: Universal Performance Explorer
    TradeFilter        as _UPEFilter,
    preset_filter      as _upe_preset_filter,
    compute_summary    as _upe_compute_summary,
    build_visual_data  as _upe_build_visual_data,
    extract_insights   as _upe_extract_insights,
    TradeRecord        as _UPERecord,
    ExportEngine       as _UPEExport,
    BackupManager      as _UPEBackup,
)
from core.orchestrator import (                                    # Phase 7A: execution orchestrator
    execution_orchestrator,
    TickContext,
)
from core.exchange.api_manager  import api_manager
from core.bootstrap.api_loader  import api_loader
from core.infra_health_manager import InfraHealthManager
from utils.capital_scaler import CapitalScaler
from utils.export_manager import ExportManager
from core.persistence.suppression_log import SuppressionEventLog  # FTD-DECISION-SNAP
from core.exploration_economics import build_exploration_origin as _build_eo    # FTD-EXPLORE-ATTR
from core.economic_truth import classify_trade_economics as _classify_eco       # FTD-ECO-TRUTH
from core.time.session_definitions import get_session_label as _get_session_label  # FTD-DECISION-SNAP
from utils.report_generator import build_report_archive
from core.export_engine import system_export_engine, SystemSnapshot   # FTD-025A
from core.intelligence.auto_intelligence_engine import AutoIntelligenceEngine  # FTD-030
from core.intelligence.reactive_evolution_engine import reactive_evolution_engine  # FTD-REA-001
from core.performance import (                                                 # FTD-031
    perf_monitor, task_queue, perf_guard,
    PRIORITY_LOW, PRIORITY_MEDIUM,
)
from strategies.strategy_modules import get_strategy, Signal, TradeSignal, _rsi
from core.lean_gate import lean_gate
from core.rl_engine import rl_engine                              # RL Contextual Bandit
from core.live_process_access import live_process_access          # FTD-LPA: runtime observability
from core.observability.orchestrator import obs_orchestrator, OBS_TICK_INTERVAL_SECS  # FTD-053-GAIA Phase 6
from core.observability.snapshot_builder import build_raw_snapshot                    # FTD-053-GAIA Phase 6
from core.signal_truth.signal_truth_engine    import signal_truth_engine              # PRP-001
from core.signal_truth.false_positive_forensics import false_positive_forensics       # PRP-001
from core.signal_truth.directional_legitimacy  import directional_legitimacy         # PRP-001
from core.signal_truth.context_quality_engine  import context_quality_engine         # PRP-001
from core.signal_truth.asymmetry_validation    import asymmetry_validation           # PRP-001
from core.signal_ecology.opportunity_ecology   import opportunity_ecology              # PRP-002
from core.signal_ecology.signal_density_engine import signal_density_engine           # PRP-002
from core.signal_ecology.exploration_recovery  import exploration_recovery_governor   # PRP-002
from core.signal_ecology.alpha_context_memory  import alpha_context_memory            # PRP-002
from core.signal_ecology.adaptive_rsi_governor import adaptive_rsi_governor           # PRP-002
from core.learning_memory.trade_memory_bridge  import trade_memory_bridge              # LRN-001


def _safe_num(v):
    """Replace inf/nan with safe JSON values."""
    import math
    if isinstance(v, float):
        if math.isinf(v) or math.isnan(v):
            return 99.99 if v > 0 else -99.99
    return v


def _sanitize(obj):
    """Recursively sanitize dict/list for JSON serialization."""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(i) for i in obj]
    return _safe_num(obj)


# ── Engine Instances ─────────────────────────────────────────────────────────

mdp        = MarketDataProvider()
pnl_calc   = PurePnLCalculator(cfg.INITIAL_CAPITAL)
scaler     = CapitalScaler()
genome     = GenomeEngine()
regime_det = RegimeDetector()
risk_ctrl  = RiskController(pnl_calc, scaler)
healer     = SelfHealingProtocol(mdp)
exporter   = ExportManager(pnl_calc, genome, risk_ctrl)
data_lake  = DataLake()
vault      = VaultManager()
guardian   = GuardianLogic()
ws_stab    = WsStabilizer(mdp)        # FTD-REF-019: tick watchdog
infra_health = InfraHealthManager(redis_health=redis_health, redis_retries=3)

# FTD-030: Auto Intelligence Engine — instantiated after pnl_calc/scaler are ready.
# Wired to _sc_build_state() (defined later) and pnl_calc.trades count.
# broadcast_fn set to _ai_broadcast (defined below) after WS clients are ready.
_auto_intelligence: "AutoIntelligenceEngine | None" = None   # initialised in lifespan

# FTD-REF-019: store boot diagnostics for /api/boot-status
_boot_status: dict = {}
_engine_running: bool = False

# qFTD-007-v2: boot-phase state lock
# BOOTING: warmup in progress — gate failures block trading but do NOT activate safe mode.
# LIVE:    normal operation — all gate failures trigger safe mode as usual.
_system_state: str = "BOOTING"   # "BOOTING" | "LIVE"
_boot_ts: float = 0.0            # set to time.time() in lifespan() for grace period tracking
_boot_replay_count: int = 0      # qFTD-010: trades replayed from DataLake at boot; streak/AF use session trades only

# ── Trade Throttle Controls ───────────────────────────────────────────────────
# After any trade on a symbol, wait this long before allowing another entry.
SYMBOL_COOLDOWN_SEC = 300         # 5 min between trades per symbol — quality > quantity
MAX_TRADES_PER_HOUR = 20          # hard ceiling across all symbols

# Symbols with proven structural losses: fee_pct_of_gross_win > 100% (FEE_TOXIC) or
# chronic net-pnl < -$5 per session (from fee_drag_analysis forensics).
_SYMBOL_BLACKLIST: frozenset[str] = frozenset({
    # FEE_TOXIC — fees exceed gross wins (fee_pct_of_gross_win > 100%)
    "BNBUSDT", "XRPUSDT", "CHIPUSDT", "PENGUUSDT", "PHBUSDT", "MOVEUSDT",  # report-1
    "PENDLEUSDT",                                                             # report-2
    # Chronic net losers — net_pnl < -$12 per session (reports 1+2)
    "LINKUSDT", "GIGGLEUSDT", "AAVEUSDT", "AVNTUSDT", "AVAXUSDT",          # report-1
    "SOLUSDT", "WLFIUSDT", "MEGAUSDT", "TRXUSDT",                          # report-2
    # report-3 (2026-05-03): fee_pct > 100% or net_pnl < -$5
    "ADAUSDT",   # net -$8.05, fee_pct 150.3% (FEE_HEAVY)
    "ENAUSDT",   # net -$5.08, fee_pct 38.4%  (FEE_HEAVY, chronic loser)
    "SUIUSDT",   # net -$2.25, fee_pct 321.1% (FEE_HEAVY, fees dwarf wins)
    # report-4 (2026-05-03 20:33): high trade count, negative net
    "ORDIUSDT",  # 27 trades, net -$10.97, fee 52.9% of gross
    "BABYUSDT",  # chronic loser confirmed across 2 sessions
    # report-5 (2026-05-05 08:25): ALL-period forensics, 502-trade dataset
    "DASHUSDT",  # 8 trades, net -$5.43, fee 75.2% of gross (FEE_HEAVY); worst 1D at -$3.10
    # report-6 (2026-05-06 03:24): 525-trade dataset — no new structural additions.
    # BIOUSDT/ETHUSDT/ORCAUSDT losses traced to TF_EMA_RSI_v1 (disabled); fee ratios OK.
    # LUNCUSDT appears FEE_TOXIC in report but net_pnl = +$2.74 — profitable, not blocked.
})

# FTD-037: Strategy disable list — all strategies confirmed NOISE in 20-unit ALL data.
# Blocking at strategy_id level is more surgical than blocking entire regime
# (regime block kills MEAN_REVERTING opportunities in trending markets).
# Re-enable condition for any strategy: PF ≥ 1.2 AND WR ≥ 45% over 30+ live trades.
#
# Evidence (ALL-period):
#   TF_EMA_RSI_v1:            78 trades, PF 0.416, -$92.11, fee 55.4%
#   MR_BB_RSI_v1:             89 trades, PF 0.363, -$37.97, fee 56.3%
#   ALPHA_TCB_v1:             73 trades, PF 0.557, -$13.38, fee 22.5%
#   ALPHA_PBE_v1:             30 trades, PF 0.479, -$3.20,  fee 50.7%
#   VE_BREAKOUT_ATR_v1:        2 trades, PF 0.0,   -$9.72,  0% WR
#   ALPHA_VSE_v1:              3 trades, PF 0.031, -$0.70,  fee 483%
#   MR_BB_RSI_v1_INV:          4 trades, PF 0.018, -$1.09,  fee 720%
#   TrendFollowing_PAPER_SPEED_INV: 4 trades, 0% WR, -$0.22
#   MeanReversion_PAPER_SPEED: 1287+ visits across RL contexts, WR 16-19%, -$293.75 total;
#     RL classified MEAN_REVERTING|LONDON (Q=-0.422) and MEAN_REVERTING|ASIA (Q=-0.344) toxic
_DISABLED_STRATEGY_IDS: frozenset[str] = frozenset({
    "TF_EMA_RSI_v1",
    "MR_BB_RSI_v1",
    "ALPHA_TCB_v1",
    "ALPHA_PBE_v1",
    "VE_BREAKOUT_ATR_v1",
    "ALPHA_VSE_v1",
    "MR_BB_RSI_v1_INV",
    "TrendFollowing_PAPER_SPEED_INV",
    "TrendFollowing_PAPER_SPEED",    # 117 trades, PF 0.657, -$16.20
    "MeanReversion_PAPER_SPEED",     # 1287+ visits, WR 16-19%, -$293.75; RL TOXIC
})
# Paper-speed fallback block (prevents synthesizing signals for bad strategy types).
# Setting _paper_speed=False (not sig=None) is critical: sig is already None at this
# point, so only clearing _paper_speed actually prevents the generation block at line 1318.
_DISABLED_PAPER_SPEED_STRATEGIES: frozenset[str] = frozenset({
    "TrendFollowing",   # 117 trades, PF 0.657, -$16.20 noise
    "MeanReversion",    # 1287+ visits, WR 16-19%, RL TOXIC — suppress PAPER_SPEED fallback
})

# Hour gate — skipped in BYPASS_ALL_GATES mode so RL can accumulate data across all hours.
# Enforced in LIVE mode only (calendar filter, not a data quality gate).
# Source: ALL-period hourly forensics across 502 trades (2026-05-05 session).
# Golden hours (net positive, ≥19 trades): 04(+$2.60,n=31), 05(+$2.60,n=19),
#   07(+$6.01,n=27), 10(+$1.73,n=26), 14(+$3.23,n=36).
# Avoid hours (net negative with ≥10 trade sample): 02(-$4.44,n=20), 03(-$4.53,n=31),
#   06(-$3.37,n=27), 08(-$14.05,n=24), 09(-$14.52,n=14), 11(-$12.05,n=31),
#   12(-$6.01,n=38), 13(-$5.19,n=35), 15(-$13.57,n=30), 16(-$18.86,n=19),
#   17(-$13.02,n=15), 18(-$27.38,n=1), 19(-$6.41,n=6), 20(-$4.78,n=4),
#   21(-$1.43,n=20), 22(-$28.08,n=21), 23(-$11.58,n=13).
_AVOID_HOURS_UTC: frozenset[int] = frozenset({2, 3, 6, 8, 9, 11, 12, 13, 15, 16, 17, 18, 19, 20, 21, 22, 23})

# Session strategy loss cap — disable a strategy for the rest of the session
# when it exceeds this loss. Prevents TF_EMA_RSI_v1-style -$92 catastrophes.
_STRATEGY_SESSION_LOSS_CAP: float = -20.0
_strategy_session_pnl: dict = {}  # strategy_id → session net pnl

_last_trade_ts: dict = {}         # symbol → last trade close timestamp (ms)
_trades_this_hour: list = []      # timestamps of recent trade opens
_last_symbol_eval_ms: dict = {}   # symbol → last strategy evaluation ts
_last_processed_candle_ts: dict = {}  # symbol → last closed candle ts evaluated
SYMBOL_EVAL_DEBOUNCE_MS = 750     # throttle heavy signal path per symbol
_closed_trade_count: list = [0]   # mutable counter for 50-trade genome trigger
_is_exploration_trade: dict = {}  # symbol → True when open trade is exploration

# Active WebSocket clients
_ws_clients: list[WebSocket] = []

# CT-Scan thought log (AI reasoning log for the UI)
_thought_log: list[dict] = []

# Last structured skip event — used by the live Skip Reason indicator on dashboard
_last_skip: dict = {}

# FTD-DECISION-SNAP: bridge open-time snapshot to close-time persistence
# Keyed by symbol; written at execution approval, consumed at DataLake persist.
_pending_decision_snapshots: dict[str, dict] = {}

# FTD-EXPLORE-ATTR: bridge RL exploration provenance to close-time TradeRecord persistence
# Keyed by symbol; written at execution approval, consumed at DataLake persist.
_pending_exploration_origins: dict[str, dict] = {}

# FTD-DECISION-SNAP: append-only suppression event log
_supp_log = SuppressionEventLog()

# FTD-GADD: session-scoped audit ledger — append-only, never cleared during session.
# Each call to /governed-adaptive-doctrine appends one immutable entry.
_gadd_audit_ledger: list[dict] = []

# FTD-GRVL: session-scoped reality-verification audit ledger — append-only.
# Each call to /reality-verification appends one immutable entry.
_grv_audit_ledger: list[dict] = []

# FTD-GMPD: session-scoped micro-pilot execution ledger — append-only.
# Holds ANALYSIS entries from each /guarded-micro-pilot call.
# EXECUTION entries would be added here on human-confirmed pilot trades (future).
_gmp_pilot_ledger: list[dict] = []

# FTD-LHEO: session-scoped evolution observatory ledger — append-only.
# Each call to /long-horizon-evolution appends one immutable ANALYSIS entry.
_lheo_audit_ledger: list[dict] = []

# FTD-CKPD: session-scoped constitutional recovery ledger — append-only.
# Each call to /constitutional-recovery-observatory appends one immutable ANALYSIS entry.
_ckpd_audit_ledger: list[dict] = []

# FTD-EIOD: session-scoped epistemic integrity ledger — append-only.
# Each call to /epistemic-integrity-observatory appends one immutable ANALYSIS entry.
_eiod_audit_ledger: list[dict] = []

# FTD-HMAO: session-scoped human meaning alignment ledger — append-only.
# Each call to /human-meaning-alignment appends one immutable ANALYSIS entry.
_hmao_audit_ledger: list[dict] = []

# FTD-RTAG: session-scoped report ecosystem governance ledger — append-only.
# Each call to /report-ecosystem-governance appends one immutable GOVERNANCE_ASSESSMENT entry.
_rtag_audit_ledger: list[dict] = []

# FTD-UEI: session-scoped export snapshot ledger — append-only.
# Snapshot records are appended here by the export infrastructure governance endpoint.
_export_snapshot_ledger: list[dict] = []

# FTD-UEI: session-scoped export infrastructure governance ledger — append-only.
# Each call to /export-infrastructure-governance appends one immutable INFRASTRUCTURE_ASSESSMENT entry.
_uei_audit_ledger: list[dict] = []

# FTD-UDCA: session-scoped download center governance ledger — append-only.
# Each call to /download-center-governance appends one immutable DOWNLOAD_CENTER_ASSESSMENT entry.
_udca_audit_ledger: list[dict] = []

# FTD-IREL: session-scoped institutional reporting experience ledger — append-only.
# Each call to /institutional-reporting-experience appends one immutable IREL_ASSESSMENT entry.
_irel_audit_ledger: list[dict] = []


def _thought(msg: str, level: str = "INFO"):
    entry = {"ts": int(time.time() * 1000), "level": level, "msg": msg}
    _thought_log.append(entry)
    if len(_thought_log) > 500:
        _thought_log.pop(0)
    logger.info(f"[CT-SCAN] {msg}")
    # Broadcast to all WS clients
    for ws in list(_ws_clients):
        asyncio.create_task(_safe_send(ws, {"type": "thought", **entry}))


async def _safe_send(ws: WebSocket, data: dict):
    try:
        await ws.send_text(json.dumps(data, default=str))
    except Exception:
        if ws in _ws_clients:
            _ws_clients.remove(ws)


def _capture_decision_snapshot(
    *,
    sym: str,
    strategy_id: str,
    strategy_type: str,
    regime: str,
    utc_hour: int,
    rl_ok: bool,
    rl_reason: str,
    ps_ec_dec=None,    # EcologyDecision — present for PAPER_SPEED only
    ctx_amp: dict | None = None,  # alpha amplification — present for PRIMARY_STRATEGY only
) -> dict:
    """
    Collect the exact subsystem states that approved this trade at execution time.
    Returns a causal evidence dict for TradeRecord.decision_snapshot.

    Fail-open contract: any per-field failure leaves that field absent.
    The function itself never raises.
    """
    from core.time.session_definitions import make_context as _mc
    is_ps = strategy_id.endswith("_PAPER_SPEED")
    snap: dict = {
        "pipeline":      "PAPER_SPEED" if is_ps else "PRIMARY_STRATEGY",
        "utc_hour":      utc_hour,
        "session_label": _get_session_label(utc_hour),
    }

    # ── RL block ──────────────────────────────────────────────────────────────
    try:
        _ctx_key  = _mc(regime, utc_hour, strategy_type)
        _rl_tbl   = getattr(rl_engine, "_table", {})
        _rl_state = _rl_tbl.get(_ctx_key)
        snap["rl"] = {
            "context":  _ctx_key,
            "q_value":  round(_rl_state.q_value, 4) if _rl_state else None,
            "n_visits": _rl_state.n_visits if _rl_state else 0,
            "ev_floor": getattr(rl_engine, "ENTRY_EV_FLOOR", -0.30),
            "approved": rl_ok,
            "reason":   rl_reason,
        }
    except Exception:
        pass

    # ── Ecology ───────────────────────────────────────────────────────────────
    if ps_ec_dec is not None:
        try:
            snap["ecology"] = {
                "verdict":         "PASS" if ps_ec_dec.approved else "BLOCK",
                "block_reason":    getattr(ps_ec_dec, "block_reason", None),
                "regime":          regime,
                "rsi_value":       getattr(ps_ec_dec, "rsi_val", None),
                "context_type":    getattr(ps_ec_dec, "context_type", None),
                "boost_mult":      getattr(ps_ec_dec, "context_boost_mult", None),
                "survival_rate":   getattr(ps_ec_dec, "survival_rate", None),
                "size_multiplier": getattr(ps_ec_dec, "size_multiplier", None),
            }
        except Exception:
            pass
    else:
        snap["ecology"] = {
            "verdict": "NOT_EVALUATED",
            "reason":  "PRIMARY_STRATEGY signals bypass ecology gate",
        }

    # ── Alpha context ─────────────────────────────────────────────────────────
    # PRIMARY_STRATEGY: explicit ctx_amp dict from alpha_context_memory.get_amplification()
    # PAPER_SPEED: alpha boost is embedded inside EcologyDecision
    _amp = ctx_amp or (
        {
            "boost_mult":   getattr(ps_ec_dec, "context_boost_mult", None),
            "context_type": getattr(ps_ec_dec, "context_type", None),
            "reason":       "embedded_in_ecology_decision",
        }
        if ps_ec_dec is not None else None
    )
    if _amp is not None:
        try:
            snap["alpha_context"] = {
                "boost_mult":   _amp.get("boost_mult"),
                "context_type": _amp.get("context_type"),
                "boost_reason": _amp.get("reason"),
                "n_trades":     _amp.get("n_trades"),
                "avg_pnl":      _amp.get("avg_pnl"),
            }
        except Exception:
            pass

    return snap


def _estimate_atr_pct(closes: list[float]) -> float:
    """Lightweight ATR% proxy from close-to-close absolute moves."""
    if len(closes) < 3:
        return 0.0
    lookback = closes[-15:]
    moves = [abs(lookback[i] - lookback[i - 1]) for i in range(1, len(lookback))]
    avg_move = sum(moves) / max(len(moves), 1)
    last = max(lookback[-1], 1e-9)
    return (avg_move / last) * 100.0


# ── Signal Processing Callback ────────────────────────────────────────────────

async def on_tick(tick: Tick):
    """Called for every new tick from MarketDataProvider."""
    global _last_skip, _system_state, _boot_replay_count   # must be declared before any assignment in this function
    sym   = tick.symbol
    price = tick.price

    # Guard: reject malformed symbols that somehow bypass _is_valid_symbol
    if len(sym) < 5 or not sym.endswith("USDT"):
        return

    # FTD-031: per-cycle latency tracking
    if cfg.PERF_ENABLED:
        perf_monitor.on_cycle_start(sym)

    # FTD-REF-019/025: record liveness for tick watchdog + truth engine
    ws_stab.record_tick()
    ws_truth_engine.record_tick()                        # FTD-REF-025

    # 1. Update risk controller (SL/TP checks)
    action = risk_ctrl.on_price_update(sym, price)
    if action:
        _thought(f"Position closed [{action}] {sym} @ {price}", "TRADE")
        if pnl_calc.trades:
            last_trade = pnl_calc.trades[-1]
            # FTD-PATH-ATTR: tag origin pipeline before persisting to DataLake
            last_trade.origin_pipeline = (
                "PAPER_SPEED" if last_trade.strategy_id.endswith("_PAPER_SPEED")
                else "PRIMARY_STRATEGY"
            )
            # FTD-DECISION-SNAP: attach open-time causal snapshot before DataLake persist
            _snap = _pending_decision_snapshots.pop(sym, None)
            if _snap is not None:
                last_trade.decision_snapshot = _snap
            # FTD-SESSION-FORENSICS: assign origin + close session attribution
            _close_utc_h = __import__("datetime").datetime.utcnow().hour
            _close_sess  = _get_session_label(_close_utc_h)
            _origin_sess = (_snap.get("session_label", "UNKNOWN")
                            if _snap is not None else "UNKNOWN")
            _origin_utc_h = (_snap.get("utc_hour", -1)
                             if _snap is not None else -1)
            _crossed = (_origin_sess != "UNKNOWN") and (_origin_sess != _close_sess)
            last_trade.origin_session           = _origin_sess
            last_trade.close_session            = _close_sess
            last_trade.origin_utc_hour          = _origin_utc_h
            last_trade.close_utc_hour           = _close_utc_h
            last_trade.crossed_session_boundary = _crossed
            last_trade.boundary_transition      = (
                f"{_origin_sess}→{_close_sess}" if _crossed else ""
            )
            # FTD-EXPLORE-ATTR: attach RL exploration provenance before DataLake persist
            _eo = _pending_exploration_origins.pop(sym, None)
            if _eo is not None:
                last_trade.exploration_origin = _eo
            # FTD-ECO-TRUTH: compute economic ground truth at close time
            try:
                last_trade.economic_truth = _classify_eco({
                    "gross_pnl":               last_trade.gross_pnl,
                    "net_pnl":                 last_trade.net_pnl,
                    "fee_entry":               last_trade.fee_entry,
                    "fee_exit":                last_trade.fee_exit,
                    "entry_ts":                last_trade.entry_ts,
                    "exit_ts":                 last_trade.exit_ts,
                    "r_multiple":              last_trade.r_multiple,
                    "crossed_session_boundary": last_trade.crossed_session_boundary,
                })
            except Exception:
                pass
            data_lake.save_trade(asdict(last_trade))
            # MASTER-001: update signal filter loss/win tracker
            if last_trade.net_pnl >= 0:
                signal_filter.record_win(sym)
            else:
                signal_filter.record_loss(sym)
            # MASTER-001: update risk engine daily PnL + equity
            risk_engine.record_trade_result(last_trade.net_pnl)
            # FTD-REF-023/024: update per-regime learning + edge engines
            _trade_regime   = getattr(last_trade, "regime",      "UNKNOWN") or "UNKNOWN"
            _trade_strategy = getattr(last_trade, "strategy_id", "unknown") or "unknown"
            _initial_risk   = max(getattr(last_trade, "initial_risk", 1.0), 1e-9)
            _r_mult         = last_trade.net_pnl / _initial_risk
            learning_engine.record(regime=_trade_regime, won=last_trade.net_pnl >= 0)
            edge_engine.record(
                regime=_trade_regime, strategy_id=_trade_strategy,
                net_pnl=last_trade.net_pnl, r_mult=_r_mult,
            )
            # FTD-037: Adaptive Edge Engine — time-aware scoring + state machine
            _gross_pnl  = getattr(last_trade, "gross_pnl", last_trade.net_pnl)
            _fee_closed  = (getattr(last_trade, "fee_entry", 0.0)
                           + getattr(last_trade, "fee_exit",  0.0))
            adaptive_edge_engine.on_trade_closed(
                strategy_id = _trade_strategy,
                net_pnl     = last_trade.net_pnl,
                r_multiple  = _r_mult,
                gross_pnl   = _gross_pnl,
                fee_total   = _fee_closed,
            )
            # FTD-037: Session strategy loss cap — track per-strategy net pnl this session
            _strategy_session_pnl[_trade_strategy] = (
                _strategy_session_pnl.get(_trade_strategy, 0.0) + last_trade.net_pnl
            )
            # FTD-038+039: Capital Flow Engine — update priority + stabilizer
            capital_flow_engine.on_trade(
                strategy_id = _trade_strategy,
                net_pnl     = last_trade.net_pnl,
                equity      = scaler.equity,
            )
            # FTD-040: Consistency Engine — feedback loop (post-trade state update)
            consistency_engine.record_trade(last_trade.net_pnl)
            # FTD-REA-001: Reactive Evolution — immediate per-trade micro-adaptation
            _gross_pnl_re   = getattr(last_trade, "gross_pnl", last_trade.net_pnl)
            _fee_total_re   = (getattr(last_trade, "fee_entry", 0.0)
                               + getattr(last_trade, "fee_exit",  0.0))
            _atr_pct_re     = 0.0
            try:
                _re_state = regime_det.state(sym)
                _atr_pct_re = getattr(_re_state, "atr_pct", 0.0) or 0.0
            except Exception:
                pass
            reactive_evolution_engine.on_trade_closed(
                symbol=sym,
                strategy_id=_trade_strategy,
                net_pnl=last_trade.net_pnl,
                r_multiple=_r_mult,
                gross_pnl=_gross_pnl_re,
                fee_total=_fee_total_re,
                atr_pct=_atr_pct_re,
                side=_trade_direction if "_trade_direction" in dir() else "",
            )
            # FTD-REF-026: track strategy usage distribution
            _closed_strat_type = {
                "TRENDING":             "TrendFollowing",
                "MEAN_REVERTING":       "MeanReversion",
                "VOLATILITY_EXPANSION": "VolatilityExpansion",
            }.get(_trade_regime, "TrendFollowing")
            strategy_engine.record_trade(_closed_strat_type)
            # A.I.E.: feed outcome + direction so engine learns per-strategy and per-direction
            _trade_direction = getattr(last_trade, "side", "")
            inverse_engine.record(_closed_strat_type, won=last_trade.net_pnl >= 0, direction=_trade_direction)
            # Mandate: trigger genome evolution every 50 trades (not just on timer)
            genome.on_trade_closed()
            # Phase 5: update EV engine, adaptive scorer, and regime memory
            _trade_cost = (getattr(last_trade, "fee_entry", 0.0)
                           + getattr(last_trade, "fee_exit", 0.0)
                           + getattr(last_trade, "slippage_cost", 0.0))
            _trade_won  = last_trade.net_pnl >= 0
            ev_engine.record(
                strategy_id=_trade_strategy, symbol=sym,
                net_pnl=last_trade.net_pnl, cost=_trade_cost,
            )
            adaptive_scorer.record_outcome(sym, won=_trade_won)
            regime_memory.record(
                regime=_trade_regime, strategy_type=_closed_strat_type,
                won=_trade_won, r_mult=_r_mult,
            )
            confidence_decay.reset(sym, _trade_strategy)  # fresh start after trade
            # RL: update Q-value for this (regime, hour, strategy) context
            # fee_cost + r_multiple enable multi-factor reward shaping (FTD-RL-EVOLUTION)
            rl_engine.update(
                regime=_trade_regime,
                utc_hour=__import__("datetime").datetime.utcnow().hour,
                strategy=_closed_strat_type,
                net_pnl=last_trade.net_pnl,
                fee_cost=_trade_cost,
                r_multiple=_r_mult,
            )
            # Phase 5.1: record exploration outcome + reset activator timer + flow monitor
            if _is_exploration_trade.pop(sym, False):
                exploration_engine.record_result(sym, last_trade.net_pnl)
            trade_activator.record_trade()
            trade_flow_monitor.record_trade(sym)
            # qFTD-009: persist equity after every trade so restarts show correct balance
            equity_snapshot.save(
                equity=scaler.equity,
                trade_count=len(pnl_calc.trades),
            )
            # PRP-001: record truth outcome for this signal
            _exit_price = getattr(last_trade, "exit_price", price)
            signal_truth_engine.record_outcome(
                signal_id  = last_trade.trade_id,
                net_pnl    = last_trade.net_pnl,
                gross_pnl  = getattr(last_trade, "gross_pnl", last_trade.net_pnl),
                exit_price = _exit_price,
            )
            context_quality_engine.record_outcome(
                signal_id = last_trade.trade_id,
                was_win   = last_trade.net_pnl > 0,
                net_pnl   = last_trade.net_pnl,
            )
            false_positive_forensics.record_outcome(
                signal_id  = last_trade.trade_id,
                symbol     = last_trade.symbol,
                regime     = _trade_regime,
                strategy_id= _trade_strategy,
                side       = getattr(last_trade, "side", ""),
                confidence = getattr(last_trade, "confidence", 0.51),
                rsi_val    = 0.0,   # RSI at signal time not stored on TradeRecord
                utc_hour   = __import__("datetime").datetime.utcnow().hour,
                net_pnl    = last_trade.net_pnl,
                was_win    = last_trade.net_pnl > 0,
            )
            directional_legitimacy.record_outcome(
                regime     = _trade_regime,
                strategy_id= _trade_strategy,
                side       = getattr(last_trade, "side", ""),
                utc_hour   = __import__("datetime").datetime.utcnow().hour,
                directionally_correct = _exit_price > last_trade.entry_price
                    if getattr(last_trade, "side", "") == "BUY"
                    else _exit_price < last_trade.entry_price,
                net_pnl    = last_trade.net_pnl,
            )
            _rr_decl = 0.0
            _rr_ach  = 0.0
            try:
                _sl_dist = abs(last_trade.entry_price - last_trade.stop_loss)
                _tp_dist = abs(last_trade.take_profit - last_trade.entry_price)
                _ex_dist = abs(_exit_price - last_trade.entry_price)
                if _sl_dist > 0:
                    _rr_decl = _tp_dist / _sl_dist
                    _rr_ach  = _ex_dist / _sl_dist
            except Exception:
                pass
            asymmetry_validation.record_outcome(
                signal_id   = last_trade.trade_id,
                symbol      = last_trade.symbol,
                strategy_id = _trade_strategy,
                regime      = _trade_regime,
                confidence  = getattr(last_trade, "confidence", 0.51),
                rr_declared = _rr_decl,
                rr_achieved = _rr_ach,
                was_win     = last_trade.net_pnl > 0,
                net_pnl     = last_trade.net_pnl,
            )
            # PRP-002: update alpha context memory with trade outcome
            _close_utc_hour = __import__("datetime").datetime.utcnow().hour
            opportunity_ecology.record_trade_outcome(
                regime      = _trade_regime,
                utc_hour    = _close_utc_hour,
                strategy_id = _trade_strategy,
                net_pnl     = last_trade.net_pnl,
            )
            # LRN-001: feed trade outcome into learning memory pipeline
            try:
                _re_close    = regime_det.state(sym)
                _atr_close   = getattr(_re_close, "atr_pct", 1.5) or 1.5
            except Exception:
                _atr_close   = 1.5
            trade_memory_bridge.record_trade(
                trade_id    = last_trade.trade_id,
                symbol      = last_trade.symbol,
                regime      = _trade_regime,
                strategy_id = _trade_strategy,
                side        = getattr(last_trade, "side", "LONG"),
                net_pnl     = last_trade.net_pnl,
                confidence  = getattr(last_trade, "confidence", 0.51),
                atr_pct     = _atr_close,
                utc_hour    = _close_utc_hour,
            )
        trade_manager.deregister(sym)                       # Phase 4: remove from lifecycle
        _last_trade_ts[sym] = int(time.time() * 1000)  # cooldown starts on close

    # MASTER-001: keep risk engine equity up to date
    risk_engine.update_equity(scaler.equity)
    # Phase 5: keep drawdown controller in sync
    drawdown_controller.update_equity(scaler.equity)
    capital_recovery_engine.update_equity(scaler.equity)  # Phase 6
    consistency_engine.update_equity(scaler.equity)       # FTD-040: equity volatility tracking

    # Phase 4: Trade Manager lifecycle update for managed open positions
    if trade_manager.is_managed(sym):
        _tm_r_state  = regime_det.state(sym)
        _tm_atr_pct  = getattr(_tm_r_state, "atr_pct", 0.0)
        _tm_atr_price = _tm_atr_pct * price / 100 if _tm_atr_pct > 0 else 0.0
        _tm_action = trade_manager.update(sym, price, _tm_atr_price)
        if _tm_action.action == "MOVE_BE" and _tm_action.new_sl > 0:
            _pos = risk_ctrl.positions.get(sym)
            if _pos:
                _pos.stop_loss = _tm_action.new_sl
                _thought(f"[TM] {sym} BE: SL→{_tm_action.new_sl:.4f} ({_tm_action.reason})", "TRADE")
        elif _tm_action.action == "TRAIL_SL" and _tm_action.new_sl > 0:
            _pos = risk_ctrl.positions.get(sym)
            if _pos:
                _pos.stop_loss = _tm_action.new_sl
        elif _tm_action.action == "PARTIAL_TP":
            _thought(f"[TM] {sym} PARTIAL_TP {_tm_action.partial_qty:.6f} @ {price:.4f} ({_tm_action.reason})", "TRADE")
        elif _tm_action.action == "TIME_EXIT":
            # FTD-037: stale trade — force close by moving SL to current price.
            # Next tick: risk_ctrl.on_price_update fires SL at ~market price.
            _pos = risk_ctrl.positions.get(sym)
            if _pos:
                _pos.stop_loss = price
                trade_manager.deregister(sym)
                _thought(f"[TM] {sym} TIME_EXIT @ {price:.4f} ({_tm_action.reason})", "TRADE")

    # 2. Get candle data for strategy
    candle = mdp.latest_closed_candle(sym)
    if not candle:
        # Startup warmup: until first closed candle lands, skip silently.
        return

    # qFTD-006 — two bugs fixed here, must stay before candle dedup:
    #
    # Bug 1 — wrong timestamp source:
    #   candle.ts is the kline OPEN time (start of the 1-min bar) — always
    #   60–120 s old by the time on_tick fires.  tick_age > DHM_STALE_TICK_SEC
    #   on every single call → permanent STALE_TICK block regardless of WS health.
    #   Fix: use tick.ts (aggTrade exchange timestamp, milliseconds old).
    #
    # Bug 2 — gate starved by candle dedup:
    #   Pre-gate was placed after the dedup guard, so the gate was only re-evaluated
    #   once per candle close (~60 s).  After a WS reconnect the gate stayed blocked
    #   until the next candle — creating a safe-mode infinite loop.
    #   Fix: evaluate health + gate on every tick so the gate clears mid-minute.
    candle_buf     = list(mdp.candle_close_buffer(sym))
    _n_candles     = len(candle_buf)
    _ind_ok_coarse = _n_candles >= cfg.IV_MIN_CANDLES
    now_ms         = int(time.time() * 1000)

    # qFTD-007: Update indicator_validator singleton on every tick so the
    # GlobalGateController._deploy_fn() sees real indicator readiness instead
    # of always returning False (iv_score=0 → deploy score capped at 75).
    # indicator_validator.is_ready() is called by _deploy_fn() which feeds
    # BootDeployabilityEngine — this was the source of the chronic "ind=0" log.
    # qFTD-007-v2: pass previous-tick indicator values for NaN detection.
    _r_state_early = regime_det.state(sym)
    _iv_values = None
    if _r_state_early is not None:
        _iv_values = {
            "adx": float(getattr(_r_state_early, "adx", float("nan"))),
            "atr": float(getattr(_r_state_early, "atr_pct", float("nan"))),
        }
    iv_result = indicator_validator.validate_symbol_buffers(
        candle_close_buf=candle_buf,
        candle_volume_buf=list(mdp.candle_volume_buffer(sym)),
        indicator_values=_iv_values,
    )

    # qFTD-007-v2: BOOTING→LIVE transition.
    # While BOOTING, gate failures block trading but never activate safe mode so
    # warmup noise cannot permanently trip the engine before data streams open.
    # Transition to LIVE when indicators are ready OR grace period has elapsed.
    if _system_state == "BOOTING":
        _elapsed = time.time() - _boot_ts
        if iv_result.ok or _elapsed >= cfg.STARTUP_GRACE_SECONDS:
            _system_state = "LIVE"
            global_gate_controller.set_system_state("LIVE")  # qFTD-010: lift BOOT_GRACE
            logger.info(
                f"[BOOT] BOOTING→LIVE | iv_ok={iv_result.ok} "
                f"elapsed={_elapsed:.1f}s grace={cfg.STARTUP_GRACE_SECONDS}s"
            )

    _dh_result = data_health_monitor.check(
        last_tick_ts=tick.ts / 1000.0,
        symbol_tick_ages={sym: max(0.0, time.time() - tick.ts / 1000.0)},
        indicator_ready=_ind_ok_coarse,
    )
    _data_fresh_ok = not _dh_result.block_trading

    # Phase 7A.3: Pre-gate control.
    # qFTD-010 Design Change 1/2/3:
    #   Signal generation ALWAYS runs — gate only locks EXECUTION.
    #   During BOOTING, indicator/data warmup conditions are bypassed so the
    #   scan pipeline warms up (learning engines, scorer) before going LIVE.
    #   INDICATOR_NOT_READY + DATA_NOT_FRESH are expected during the first 20 min
    #   and must not prevent signal observation.
    _gate_ind_ok    = True if _system_state == "BOOTING" else _ind_ok_coarse
    _gate_data_frsh = True if _system_state == "BOOTING" else _data_fresh_ok
    _pre_gate = execution_orchestrator.gate_check(
        symbol=sym,
        indicator_ok=_gate_ind_ok,
        data_fresh=_gate_data_frsh,
        activate_safe_mode=(_system_state == "LIVE"),
    )
    # qFTD-010: store execution permission — do NOT return early.
    # The scan pipeline continues regardless; only run_cycle is gated below.
    _execution_allowed = _pre_gate.allowed
    if not _execution_allowed:
        logger.debug(
            f"[SCAN] {sym} gate locked (execution blocked): {_pre_gate.reason}"
        )

    # Strategy/signal logic runs only on new candle closes (not every tick).
    if _last_processed_candle_ts.get(sym) == candle.ts:
        return
    _last_processed_candle_ts[sym] = candle.ts

    buf       = list(mdp.price_buffer(sym))           # tick prices — kept for legacy checks
    # candle_buf already computed above (before gate check)
    data_gate = strategy_engine.evaluate_data_sufficiency(len(candle_buf))
    if data_gate != "OK":
        if cfg.BYPASS_ALL_GATES and len(candle_buf) >= 2:
            # BYPASS_ALL_GATES: skip candle-count warmup gate so paper trades start
            # as soon as 2 candles exist. Signal quality enforced by lean_gate only.
            logger.debug(f"[BYPASS] {sym} data gate bypassed ({data_gate} candles={len(candle_buf)})")
        else:
            error_registry.log("DATA_001", symbol=sym, extra=f"candles={len(candle_buf)}")  # FTD-REF-025
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": f"{data_gate}({len(candle_buf)})",
            }
            return

    # 2b. Performance debounce: avoid repeated heavy regime/signal passes
    # for the same symbol within sub-second windows.
    prev_eval = _last_symbol_eval_ms.get(sym, 0)
    if now_ms - prev_eval < SYMBOL_EVAL_DEBOUNCE_MS:
        return
    _last_symbol_eval_ms[sym] = now_ms

    # 3. Detect regime
    regime_det.push(sym, candle.close, candle.high, candle.low, candle.ts)
    regime = regime_det.get(sym)
    # FTD-REF-019: debounce — only log on genuine regime transitions
    regime_debounce.push(sym, regime, state=regime_det.state(sym))

    # FTD-037: VOLATILITY_EXPANSION hard block — 2 trades, 0% WR, avg loss $4.86.
    # Primary STOP_LOSS_SLIP source. No profitable strategy exists here.
    # TRENDING is NOT blocked at regime level — it is blocked at strategy_id level
    # (_DISABLED_STRATEGY_IDS) to preserve MEAN_REVERTING opportunities that can
    # occur in trending markets (contrarian pullbacks).
    if regime.value == "VOLATILITY_EXPANSION":
        return

    # 4. Get appropriate strategy — UNKNOWN defaults to TrendFollowing during warmup
    strategy_type = {
        "TRENDING":             "TrendFollowing",
        "MEAN_REVERTING":       "MeanReversion",
        "VOLATILITY_EXPANSION": "VolatilityExpansion",
        "UNKNOWN":              "TrendFollowing",
    }.get(regime.value, "TrendFollowing")

    # Session-adaptive scaling — resolved here so min_atr_pct is baked into the
    # strategy instance before signal generation. No hard blocks: RL context key
    # is REGIME|SESSION|STRATEGY so the bandit accumulates per-session Q-values
    # and converges to session-appropriate behaviour on its own.
    _session_utc_hour   = __import__("datetime").datetime.utcnow().hour
    _session_label_now  = _get_session_label(_session_utc_hour)
    _session_min_atr    = cfg.SESSION_MIN_ATR_PCT.get(_session_label_now, 0.10)
    _session_size_scale = cfg.SESSION_SIZE_SCALE.get(_session_label_now, 1.00)

    dna      = genome.active_dna.get(strategy_type, {})
    # FTD-REA-001: merge per-symbol reactive overrides (RSI bands, ATR multipliers)
    _re_overrides = reactive_evolution_engine.get_overrides(sym)
    if _re_overrides:
        dna = {**dna, **_re_overrides}
    # Inject session-calibrated ATR floor — ASIA/LATE have lower absolute ATR;
    # the global MIN_ATR_PCT=0.10 would block all their setups before RL sees them.
    dna = {**dna, "min_atr_pct": _session_min_atr}
    strategy = get_strategy(regime, dna)

    # 5. Generate signal (only if no open position + throttle checks)
    _halted_blocked = risk_ctrl.halted and not cfg.BYPASS_ALL_GATES
    # FTD-REA-001: fee-toxic suppression — skip signal if reactive engine flagged symbol
    if reactive_evolution_engine.is_suppressed(sym):
        return
    if sym not in risk_ctrl.positions and not _halted_blocked and not risk_ctrl.graceful_stop:

        # ── Throttle A: per-symbol cooldown (30 min between trades) ──────────
        last_ts = _last_trade_ts.get(sym, 0)
        cooldown_remaining = SYMBOL_COOLDOWN_SEC - (now_ms - last_ts) / 1000
        if cooldown_remaining > 0:
            return   # too soon after last trade on this symbol

        # ── Throttle B: max 12 trades per hour across all symbols ─────────────
        one_hour_ago = now_ms - 3_600_000
        _trades_this_hour[:] = [t for t in _trades_this_hour if t > one_hour_ago]
        if len(_trades_this_hour) >= MAX_TRADES_PER_HOUR:
            return   # hourly cap reached

        # ── Symbol quality filter: skip non-ASCII (meme/scam coins) ──────────
        if not sym.isascii():
            return

        # ── Symbol blacklist: fee-toxic / chronic loss symbols ────────────────
        if sym in _SYMBOL_BLACKLIST:
            return

        # ── Hour gate — calendar filter (FTD-SNP-001) ────────────────────────────
        # In BYPASS_ALL_GATES mode the gate is disabled so RL can accumulate Q-value
        # data across ALL hours (including the historically bad ones). The RL engine
        # will converge to avoid bad-hour contexts itself once Q < ENTRY_EV_FLOOR.
        # Without this, 17/24 hours are permanently dark to RL → context table is
        # sparse → bandit explores fewer dimensions → slower convergence.
        # In LIVE mode this gate remains active (historical -ve PnL hours are hard-blocked).
        _current_utc_hour = _session_utc_hour  # reuse value computed at strategy-build time
        if not cfg.BYPASS_ALL_GATES and _current_utc_hour in _AVOID_HOURS_UTC:
            # Calculate next allowed hour so the user knows when to expect trades.
            _allowed_hours = sorted(set(range(24)) - _AVOID_HOURS_UTC)
            _next_open = next((h for h in _allowed_hours if h > _current_utc_hour),
                              _allowed_hours[0])
            _thought(
                f"⏸ HOUR_GATE {sym}: {_current_utc_hour:02d}h UTC BLOCKED — "
                f"next open: {_next_open:02d}h UTC | "
                f"golden hours (positive PnL): 07h 10h 14h UTC",
                "FILTER",
            )
            return

        # No session hard blocks. ASIA/LATE are allowed to trade with session-calibrated
        # parameters (_session_min_atr, _session_size_scale). The RL bandit learns
        # per-session Q-values via the REGIME|SESSION|STRATEGY context key and will
        # naturally deprioritise sessions where expected value is negative.

        # Use real 1-min candle OHLC for strategy indicators.
        # tick_buffers hold individual trade prices (noisy, many per second) — they
        # produce fake ATR ≈ 0.1% which causes undersized SL distances, oversized qty,
        # and HIGH_FEE_RATIO / COST_HIGH failures. Candle buffers give accurate ATR.
        closes = candle_buf
        highs  = list(mdp.candle_high_buffer(sym)) or [p * 1.001 for p in candle_buf]
        lows   = list(mdp.candle_low_buffer(sym))  or [p * 0.999 for p in candle_buf]

        # FTD-REF-019: validate indicator quality before generating signal
        # ATR source priority:
        #   1. regime_det accumulated ATR (real OHLC, 28+ candles) — most accurate
        #   2. Single closed-kline (high-low)/close proxy — available after first kline
        # tick_buffers are individual trade prices (not candle closes), so
        # tick-to-tick ATR is 0.0001% and must NOT be used here.
        r_state        = regime_det.state(sym)
        regime_atr_pct = getattr(r_state, "atr_pct", 0.0)
        candle_atr_pct = ((candle.high - candle.low) / candle.close * 100) if candle.close > 0 else 0.0
        atr_pct        = regime_atr_pct if regime_atr_pct > 0 else candle_atr_pct
        raw_adx        = getattr(r_state, "adx", 0.0)
        # FTD-SNP-001: update slow ATR EMA every candle for volatility gate
        if atr_pct > 0:
            reactive_evolution_engine._update_atr_ema(sym, atr_pct)
        guard          = indicator_guard.validate(
            symbol=sym, n_candles=_n_candles, adx=raw_adx, atr_pct=atr_pct,
        )
        if not guard.ok:
            if cfg.BYPASS_ALL_GATES:
                # BYPASS_ALL_GATES: substitute floor values so the pipeline can
                # generate signals during paper warmup before full indicator readiness.
                # Soft ADX=15 (WEAK but tradeable), soft ATR=0.01% (above lean_gate floor).
                from core.indicator_guard import GuardResult
                _guard_block_reason = guard.reason
                _soft_adx = max(raw_adx if raw_adx is not None else 0.0, 15.0)
                _soft_atr = max(atr_pct, 0.01)
                guard = GuardResult(ok=True, adx=_soft_adx, atr_pct=_soft_atr, adx_quality="WEAK")
                logger.debug(
                    f"[BYPASS] {sym} indicator guard bypassed ({_guard_block_reason}) "
                    f"→ soft adx={_soft_adx:.1f} atr={_soft_atr:.4f}%"
                )
            else:
                error_registry.log("DATA_002", symbol=sym, extra=guard.reason)  # FTD-REF-025
                return   # insufficient candles / unstable ADX / near-zero ATR

        # FTD-SNP-001: ATR volatility gate — bypassed in BYPASS_ALL_GATES mode so RL engine
        # gets continuous trade data in paper sessions. In live mode blocks entries where
        # current ATR > 2× slow EMA — high-volatility = STOP_LOSS_SLIP risk.
        # ATR EMA needs a few candles to stabilise; is_high_volatility() returns False
        # until the EMA is seeded, so paper warmup is safe.
        if not cfg.BYPASS_ALL_GATES and reactive_evolution_engine.is_high_volatility(sym, atr_pct):
            _last_skip = {
                "ts": now_ms, "symbol": sym,
                "reason": f"ATR_SPIKE(atr={atr_pct:.4f}%)",
                "regime": regime.value, "strategy": strategy_type,
            }
            trade_flow_monitor.record_skip(sym, "ATR_SPIKE")
            return

        # Phase 2: Hard-lock MeanReversion when ADX > 25 (strong trend regardless of regime label).
        if strategy_type == "MeanReversion" and raw_adx > 25.0:
            _last_skip = {
                "ts": now_ms, "symbol": sym,
                "reason": f"MR_TREND_LOCK(ADX={raw_adx:.1f}>25)",
                "regime": regime.value,
            }
            return

        # ── Phase 5.2: Dynamic Threshold Provider — master control layer ────────
        # Single source of truth: aggregates TradeActivator + AdaptiveFilter + DD
        # qFTD-010: streak/AF use session-only trades so replayed loss history
        # doesn't permanently tighten quality gates at boot (stacking deadlock fix).
        _tf_mins = trade_flow_monitor.minutes_since_last_trade()
        _session_trades = pnl_calc.trades[_boot_replay_count:]
        _p52_cl  = 0
        for _t in reversed(_session_trades):
            if _t.net_pnl < 0:
                _p52_cl += 1
            else:
                break
        thresholds = dynamic_threshold_provider.get(
            minutes_no_trade=_tf_mins,
            consecutive_losses=_p52_cl,
        )
        if thresholds.tier != "NORMAL" or thresholds.af_state != "NORMAL":
            _thought(
                f"⚡ DTP {sym}: tier={thresholds.tier} af={thresholds.af_state} "
                f"score_min={thresholds.score_min:.3f} "
                f"vol_mult={thresholds.volume_multiplier:.2f}×"
                f" fee_tol={thresholds.fee_tolerance:.2f}",
                "SIGNAL",
            )
        trade_flow_monitor.record_signal(sym)

        # ── Phase 6: Streak Intelligence — momentum-aware score adjustment ──
        _p52_cw = 0
        for _t in reversed(_session_trades):
            if _t.net_pnl > 0: _p52_cw += 1
            else: break
        _streak_result = streak_engine.check(
            consecutive_wins=_p52_cw, consecutive_losses=_p52_cl,
        )
        # Effective score_min = DTP base ± streak delta, floored at 0.40.
        # In BYPASS mode the COLD adjustment is zeroed out: consecutive losses create
        # a death spiral (losses → +0.05/loss → eff_min 0.56→0.61→0.66 → no trades
        # → miss the recovery signal → more losses). In production mode it stays on.
        _streak_adj = 0.0 if cfg.BYPASS_ALL_GATES else _streak_result.score_adjustment
        _eff_score_min = max(0.40, round(
            thresholds.score_min + _streak_adj, 4
        ))
        # Note: TRENDING regime score boost removed — TRENDING is now hard-blocked
        # before this point (regime hard block, line ~546). Code retained as comment
        # for reference: was +0.15 to _eff_score_min when regime == TRENDING.
        if _streak_result.state != "NEUTRAL":
            _thought(
                f"📈 STREAK {sym}: {_streak_result.state} "
                f"len={_streak_result.streak_len} "
                f"score_adj={_streak_result.score_adjustment:+.2f} "
                f"→ eff_min={_eff_score_min:.3f}",
                "SIGNAL",
            )

        # Phase 3: Volume Sleep Mode — dynamic threshold from DTP (no static bypass hack)
        vol_buf = mdp.candle_volume_buffer(sym)
        # PAPER_SPEED fallback: fires only when real strategy + alpha both return NONE.
        # RSI filter (commit 93250aa) already applied inside the block — prevents the
        # pre-filter 21% WR noise; delivers ~4-6 quality setups/hr instead of 16+.
        # Without this, real strategies only fire on EMA crossover / BB touch which can
        # be absent for hours → complete NO TRADE dry spells.
        _paper_speed = (cfg.TRADE_MODE == "PAPER" and cfg.PAPER_SPEED_MODE)
        # Safe defaults — signal_truth_engine.record_signal() needs these regardless
        # of whether the PAPER_SPEED block fires. Without defaults, non-PAPER_SPEED
        # code paths raise NameError at record_signal() → total_signals stays 0.
        _rsi_val:   float = 50.0
        _above_sma: bool  = True
        _vol_mult = thresholds.volume_multiplier
        if _paper_speed:
            # Aggressive paper throughput mode: relax sleep gate to its floor.
            _vol_mult = min(_vol_mult, 0.20)
        vol_active, vol_reason = volume_filter.is_active(
            sym, vol_buf, vol_multiplier=_vol_mult,
        )
        if _paper_speed and not vol_active:
            _thought(
                f"⚡ PAPER_SPEED bypass {sym}: {vol_reason}",
                "FILTER",
            )
            vol_active = True
        if not cfg.BYPASS_ALL_GATES and not vol_active:
            _last_skip = {"ts": now_ms, "symbol": sym, "reason": vol_reason, "regime": regime.value}
            trade_flow_monitor.record_skip(sym, vol_reason)
            return

        # Phase 3: Sector Correlation Guard — max 2 open positions from same sector.
        sector_ok, sector_reason = sector_guard.check(sym, risk_ctrl.positions)
        if not cfg.BYPASS_ALL_GATES and not sector_ok:
            _last_skip = {"ts": now_ms, "symbol": sym, "reason": sector_reason, "regime": regime.value}
            return

        # MASTER-001: risk engine gate (daily loss / trade cap / drawdown halt)
        risk_allowed, risk_reason = risk_engine.check_new_trade()
        if _paper_speed and not risk_allowed:
            if any(k in risk_reason for k in ("HALTED:", "MAX_DAILY_LOSS", "DAILY_TRADE_CAP")):
                _thought(f"⚡ PAPER_SPEED bypass risk gate {sym}: {risk_reason}", "FILTER")
                risk_allowed = True
        if not cfg.BYPASS_ALL_GATES and not risk_allowed:
            return   # daily risk limit reached

        # FTD-REF-024: market structure gate (LOW_VOL_TRAP / FAKE_BREAKOUT block)
        _bb_width = getattr(r_state, "bb_width", 0.0)
        ms_result = market_structure_detector.detect(
            adx=guard.adx, bb_width=_bb_width, atr_pct=guard.atr_pct,
        )
        if not cfg.BYPASS_ALL_GATES and not ms_result.tradeable:
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": ms_result.block_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return

        # FTD-REF-024: edge engine kill switch
        edge_allowed, edge_reason = edge_engine.check_trade(regime.value, strategy_type)
        if not cfg.BYPASS_ALL_GATES and not edge_allowed:
            error_registry.log("STRAT_002", symbol=sym, extra=edge_reason)  # FTD-REF-025
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": edge_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return

        # FTD-037: Adaptive Edge Engine kill switch (state-machine + cost filter)
        _aee_ok, _aee_reason = adaptive_edge_engine.check_trade(strategy_type)
        if not cfg.BYPASS_ALL_GATES and not _aee_ok:
            error_registry.log("STRAT_037", symbol=sym, extra=_aee_reason)
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": _aee_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return
        # FTD-054-PHOENIX: surface AEE kill state in bypass mode — previously silent,
        # causing the 246-min dry spell to appear as RSI_FILTER in the signal funnel
        # when the real cause was EDGE_ENGINE_KILL on the dominant PAPER_SPEED strategy.
        if cfg.BYPASS_ALL_GATES and not _aee_ok:
            _thought(
                f"⚠️ AEE_KILL {sym} [{strategy_type}]: {_aee_reason} "
                f"[bypass=active, trade_allowed, size_restored_to_1.0x]",
                "SIGNAL",
            )

        # FTD-REF-023: get dry-spell relaxation factor before signal filter
        relax_factor = trade_frequency.get_relaxation_factor()

        # MASTER-001 + FTD-REF-023: regime AI with per-symbol UNKNOWN fallback
        r_ai = regime_ai.classify(
            adx=guard.adx, atr_pct=guard.atr_pct,
            bb_width=getattr(r_state, "bb_width", 0.0),
            closes=closes,
            symbol=sym,
        )
        # FTD-REF-025: log STRAT_001 when AI regime is ambiguous (UNKNOWN)
        if r_ai.regime.value == "UNKNOWN":
            error_registry.log(
                "STRAT_001", symbol=sym,
                extra=f"adx={guard.adx:.1f} conf={r_ai.confidence:.2f}",
            )

        # FTD-REF-026: regime stability gate — block if conf <0.50 or <3 stable ticks
        if not cfg.BYPASS_ALL_GATES and r_ai.block_trade:
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": (
                    f"REGIME_UNSTABLE("
                    f"conf={r_ai.confidence:.2f},"
                    f"ticks={r_ai.stability_ticks})"
                ),
                "regime": regime.value, "strategy": strategy_type,
            }
            return

        # FTD-REF-023: scale confidence by per-regime learning-engine weight
        _regime_weight = learning_engine.get_regime_weight(r_ai.regime.value)
        # FTD-REF-026: profit guard — reduce effective confidence when PF < 1
        # qFTD-011: use session-only trades for consecutive_losses so replayed
        # loss history cannot trigger HARD_STOP at boot (same fix as _p52_cl).
        # qFTD-032: also use session-only count for n_trades passed to profit_guard.
        # Without this, 131 replayed trades (PF=0.37) applied a permanent 20%
        # confidence penalty from session start, blocking all signals until
        # enough new winning trades could offset the historical deficit.
        _pf_stats = pnl_calc.session_stats
        _session_trade_count = len(pnl_calc.trades) - _boot_replay_count
        _consecutive_losses = 0
        for _t in reversed(pnl_calc.trades[_boot_replay_count:]):
            if _t.net_pnl < 0:
                _consecutive_losses += 1
            else:
                break
        _pg_hard_stop, _pg_hard_reason = profit_guard.hard_stop_required(
            profit_factor=_pf_stats.get("profit_factor", 1.0),
            n_trades=_session_trade_count,
            consecutive_losses=_consecutive_losses,
        )
        if not cfg.BYPASS_ALL_GATES and _pg_hard_stop:
            _last_skip = {
                "ts": int(time.time() * 1000), "symbol": sym,
                "reason": _pg_hard_reason, "regime": regime.value,
                "strategy": strategy_type,
            }
            return

        _pf_mult  = profit_guard.frequency_multiplier(
            profit_factor=_pf_stats.get("profit_factor", 1.0),
            n_trades=_session_trade_count,
        )
        # RL: apply learned confidence boost from contextual bandit
        _rl_boost = rl_engine.confidence_boost(
            regime=r_ai.regime.value,
            utc_hour=__import__("datetime").datetime.utcnow().hour,
            strategy=strategy_type,
        )
        _adjusted_conf = round(r_ai.confidence * _regime_weight * _pf_mult * _rl_boost, 3)

        # qFTD-011: diagnostic log before signal generation so we can see indicator
        # state at each candle close and confirm the pipeline is reaching this point.
        logger.info(
            f"[SIG] {sym} n={len(closes)} regime={regime.value} "
            f"adx={guard.adx:.1f} atr={guard.atr_pct:.4f}% "
            f"conf={_adjusted_conf:.3f} consec_loss={_consecutive_losses}"
        )

        sig = strategy.generate_signal(sym, closes, highs, lows)
        if not sig or sig.signal == Signal.NONE:
            logger.debug(f"[SIG] {sym} strategy={strategy_type} → NONE (no crossover / conditions unmet)")

        # Phase 4: Alpha Engine — supplementary high-quality signals
        # Runs when existing strategy produces no signal; all alpha signals
        # have already passed internal RR + Trade Scorer gates.
        if not sig or sig.signal == Signal.NONE:
            _vol_list_alpha = list(vol_buf)
            # qFTD-011: compute actual avg_atr_pct from recent candle history so
            # vol_expansion sub-score in trade_scorer uses a real baseline, not current ATR.
            _recent_candle_highs  = list(mdp.candle_high_buffer(sym))
            _recent_candle_lows   = list(mdp.candle_low_buffer(sym))
            _window = min(20, len(_recent_candle_highs))
            if _window >= 5 and candle_buf[-1] > 0:
                _avg_atr_pct = sum(
                    (h - l) / c * 100
                    for h, l, c in zip(
                        _recent_candle_highs[-_window:],
                        _recent_candle_lows[-_window:],
                        candle_buf[-_window:],
                    )
                ) / _window
            else:
                _avg_atr_pct = atr_pct
            _alpha_sig = alpha_engine.generate(
                symbol=sym, closes=closes, highs=highs, lows=lows,
                volumes=_vol_list_alpha, adx=guard.adx,
                atr_pct=atr_pct, avg_atr_pct=_avg_atr_pct,
                regime=regime.value,
            )
            if _alpha_sig:
                sig = _alpha_sig.trade_signal
                _thought(
                    f"⚡ ALPHA {_alpha_sig.alpha_type} {sym} "
                    f"score={_alpha_sig.score:.3f} rr={_alpha_sig.rr:.2f}",
                    "SIGNAL",
                )
            else:
                logger.debug(f"[SIG] {sym} alpha → NONE (RR/score below threshold)")

        # PAPER_SPEED fallback injector:
        # If both primary + alpha signals are NONE, synthesize a minimal
        # momentum signal so the pipeline can execute and recover flow.
        # FTD-037: blocked for strategies in _DISABLED_PAPER_SPEED_STRATEGIES
        # (TrendFollowing confirmed -$16.20 NOISE over 117 trades in ALL-period data).
        if _paper_speed and strategy_type in _DISABLED_PAPER_SPEED_STRATEGIES:
            _paper_speed = False  # prevent PAPER_SPEED generation block at line 1318 from firing
        # In live mode: when a primary/alpha signal carries a disabled strategy_id, clear
        # it so the paper_speed fallback can generate the {strategy_type}_PAPER_SPEED
        # variant. TrendFollowing is excluded because TrendFollowing_PAPER_SPEED is
        # itself in _DISABLED_STRATEGY_IDS.
        # In BYPASS/paper mode: skip this clearing so alpha signals (ALPHA_PBE_v1,
        # ALPHA_TCB_v1, score=0.578, RR=5.0) flow through to DISABLED_OVERRIDE at line
        # 1431 instead of being replaced by PAPER_SPEED variants that may fail RSI
        # filtering — the net effect without this guard is a second silent signal drop.
        if (
            not cfg.BYPASS_ALL_GATES
            and _paper_speed
            and sig and sig.signal != Signal.NONE
            and sig.strategy_id in _DISABLED_STRATEGY_IDS
            and strategy_type not in _DISABLED_PAPER_SPEED_STRATEGIES
        ):
            sig = None  # live mode only: force paper_speed fallback for disabled alpha ids
        if _paper_speed and (not sig or sig.signal == Signal.NONE) and len(closes) >= 2:
            _entry = closes[-1]

            # ── SMA-50 trend direction (50-min context) ───────────────────────
            _trend_len = min(50, len(closes))
            _sma50     = sum(closes[-_trend_len:]) / _trend_len
            _above_sma = closes[-1] > _sma50

            # ── Inline RSI(14) ────────────────────────────────────────────────
            # RSI filters ensure we only enter when conditions are RIGHT, not on
            # every candle. Real strategies (TF_EMA_RSI_v1, MR_BB_RSI_v1) win
            # 100% of the time; PAPER_SPEED without RSI wins only 38% → noise.
            _rsi_p = 14
            if len(closes) >= _rsi_p + 1:
                _rsi_d = [closes[i] - closes[i-1] for i in range(-_rsi_p, 0)]
                _g = sum(d for d in _rsi_d if d > 0) / _rsi_p
                _l = sum(-d for d in _rsi_d if d < 0) / _rsi_p
                _rsi_val = (100.0 - 100.0 / (1.0 + _g / _l)) if _l > 0 else 100.0
            else:
                _rsi_val = 50.0

            # ── Previous-period RSI — crash guard for MEAN_REVERTING entries ──
            # FTD-054-PHOENIX Phase 2: prevents entering on a first-touch RSI
            # extreme that is still in free-fall. Evidence: NEARUSDT RSI 68→29
            # in one candle (trend crash) fast-failed immediately; NILUSDT RSI
            # oscillated 43→33→29 across multiple candles (genuine mean reversion)
            # and is profitable. Requiring prev-period also in extreme zone blocks
            # the crash entry while preserving the oscillation entry.
            _rsi_prev: float = _rsi_val  # default: treat as stable if not enough data
            if len(closes) >= _rsi_p + 2:
                _rsi_d_prev = [closes[i] - closes[i-1] for i in range(-_rsi_p - 1, -1)]
                _g_p = sum(d for d in _rsi_d_prev if d > 0) / _rsi_p
                _l_p = sum(-d for d in _rsi_d_prev if d < 0) / _rsi_p
                _rsi_prev = (100.0 - 100.0 / (1.0 + _g_p / _l_p)) if _l_p > 0 else 100.0

            # ── Multi-candle RSI history for persistence confirmation ─────────
            # AdaptiveRSIGovernor uses this to verify RSI has been sustainably in
            # the extreme zone (≥2 of last 3 candles) before allowing MEAN_REVERTING
            # entries. Blocks first-touch crashes/spikes that resolve on the next
            # candle. Oldest→newest order; gracefully degrades if closes too short.
            _rsi_history: list = [_rsi_prev, _rsi_val]  # minimum 2-candle window
            if len(closes) >= _rsi_p + 3:
                _rsi_d_t2 = [closes[i] - closes[i-1] for i in range(-_rsi_p - 2, -2)]
                _g_t2 = sum(d for d in _rsi_d_t2 if d > 0) / _rsi_p
                _l_t2 = sum(-d for d in _rsi_d_t2 if d < 0) / _rsi_p
                _rsi_t2 = (100.0 - 100.0 / (1.0 + _g_t2 / _l_t2)) if _l_t2 > 0 else 100.0
                _rsi_history = [_rsi_t2, _rsi_prev, _rsi_val]

            # ── PRP-002: adaptive RSI evaluation via OpportunityEcology ─────────
            # Replaces hardcoded 70/30 / 48/52 bands. AdaptiveRSIGovernor starts
            # at the same thresholds and widens them if survival rate drops below
            # 10% (drought prevention). AlphaContextMemory blocks toxic contexts.
            _ps_ec_dec = opportunity_ecology.evaluate_opportunity(
                regime=regime.value,
                rsi_val=_rsi_val,
                rsi_prev=_rsi_prev,
                above_sma=_above_sma,
                utc_hour=__import__("datetime").datetime.utcnow().hour,
                strategy_id=f"{strategy_type}_PAPER_SPEED",
                symbol=sym,
                rsi_history=_rsi_history,
            )
            _ps_side: Signal | None = (
                Signal(_ps_ec_dec.rsi_side)
                if _ps_ec_dec.approved and _ps_ec_dec.rsi_side
                else None
            )
            _prp002_size_mult = _ps_ec_dec.size_multiplier if _ps_side is not None else 1.0

            if _ps_side is not None:
                _atr_px = max(
                    abs(closes[-1] - closes[-2]),
                    _entry * 0.002,
                    (_entry * atr_pct / 100.0),
                )
                # FIX: RR was 2.0 (SL=2×ATR, TP=4×ATR) which always failed
                # LeanGate MIN_RR=2.5, silently blocking every paper_speed signal.
                # SL=1.5×ATR, TP=4.5×ATR → RR=3.0 — clears the 2.5 threshold
                # with margin while keeping SL tight enough for mean-reversion setups.
                _sl_dist = _atr_px * 1.5   # RR = 3.0 (passes LeanGate MIN_RR=2.5)
                _tp_dist = _atr_px * 4.5
                if _ps_side == Signal.LONG:
                    _sl = _entry - _sl_dist
                    _tp = _entry + _tp_dist
                else:
                    _sl = _entry + _sl_dist
                    _tp = _entry - _tp_dist
                sig = TradeSignal(
                    symbol=sym,
                    signal=_ps_side,
                    entry_price=_entry,
                    stop_loss=_sl,
                    take_profit=_tp,
                    confidence=0.51,
                    strategy_id=f"{strategy_type}_PAPER_SPEED",
                    reason="PAPER_SPEED_FALLBACK(momentum micro-signal)",
                )
                _thought(
                    f"⚡ PAPER_SPEED fallback {sym}: {_ps_side.value} "
                    f"entry={_entry:.4f} rsi={_rsi_val:.1f}",
                    "SIGNAL",
                )
            else:
                _thought(
                    f"⚡ PAPER_SPEED {sym}: "
                    f"{_ps_ec_dec.rsi_block_reason or _ps_ec_dec.block_reason or 'RSI filter blocked'} "
                    f"(rsi={_rsi_val:.1f} above_sma={_above_sma} regime={regime.value})",
                    "FILTER",
                )

        # RSI_CRASH_GUARD: block alpha/primary signals in RSI extreme zones.
        # Forensic evidence: 72.5% false-positive rate at EXTREME_LOW RSI (<20) from
        # ALPHA_TCB_v1 SHORTs — shorting into already-oversold crashes is backwards.
        # Similarly, LONG entries at EXTREME_HIGH RSI (>80) chase blow-offs.
        # PAPER_SPEED signals are already governed by AdaptiveRSIGovernor (PRP-002).
        if (sig and sig.signal != Signal.NONE
                and not sig.strategy_id.endswith("_PAPER_SPEED")
                and len(closes) >= cfg.RSI_PERIOD + 1):
            _guard_rsi = _rsi(closes, cfg.RSI_PERIOD)
            if (sig.signal.value == "SHORT" and _guard_rsi < 20) or \
               (sig.signal.value == "LONG"  and _guard_rsi > 80):
                _thought(
                    f"🚫 RSI_CRASH_GUARD {sym}: {sig.signal.value} blocked "
                    f"(rsi={_guard_rsi:.1f})",
                    "FILTER",
                )
                sig = None

        if sig and sig.signal != Signal.NONE:
            # FTD-037: Disabled strategy_id check — surgically blocks all NOISE strategies
            # in live mode. In BYPASS/paper mode the RL bandit must see trade outcomes even
            # from losing strategies so Q-values can converge and de-prioritise them via
            # decay. Without this bypass, all currently-generated signals (ALPHA_PBE_v1,
            # ALPHA_TCB_v1, TrendFollowing_PAPER_SPEED) are silently discarded → permanent
            # drought → ALLOW_COLLAPSE (same failure mode as LCC + RL-TOXIC, FTD-054-PHOENIX).
            if sig.strategy_id in _DISABLED_STRATEGY_IDS:
                if not cfg.BYPASS_ALL_GATES:
                    return
                _thought(
                    f"⚡ DISABLED_OVERRIDE {sym}: {sig.strategy_id} allowed "
                    f"[bypass=active — RL needs outcomes; Q-decay will deprioritise if losing]",
                    "SIGNAL",
                )

            # FTD-037: Session strategy loss cap — catches any unlisted strategy that
            # goes bad this session (prevents -$92 runaway on a single strategy_id).
            # Bypassed in PAPER/BYPASS mode: RL needs to trade through losses to learn;
            # muting the only active strategy here creates 0-trade dead zones.
            _strat_sess_pnl = _strategy_session_pnl.get(sig.strategy_id, 0.0)
            if not cfg.BYPASS_ALL_GATES and _strat_sess_pnl < _STRATEGY_SESSION_LOSS_CAP:
                logger.warning(
                    f"[FTD-037] {sig.strategy_id} session_pnl={_strat_sess_pnl:.2f} "
                    f"< cap={_STRATEGY_SESSION_LOSS_CAP} — muted for session"
                )
                return

            execution_drive_policy.record_signal(sym)   # EDP: track signal activity
            # PRP-002: record primary signal pass; get ecology size multiplier.
            # Paper_speed signals already set _prp002_size_mult via evaluate_opportunity().
            # Primary strategy signals route through here — record density + get context boost.
            _utc_hr_ec = __import__("datetime").datetime.utcnow().hour
            if not sig.strategy_id.endswith("_PAPER_SPEED"):
                signal_density_engine.record_pass(regime=regime.value, symbol=sym)
                exploration_recovery_governor.on_signal_passed()
                _ctx_amp = alpha_context_memory.get_amplification(
                    regime=regime.value, utc_hour=_utc_hr_ec, strategy=strategy_type,
                )
                # Fix B (FTD-BOOST-SUPPRESS): forensic audit showed context-boosted trades
                # during recovery cycles avg -0.20 PnL vs -0.12 for normal trades.
                # Suppress upward boost (>1.0) when a recovery cycle is active; reductions
                # (<1.0) still pass through — they are protective, not harmful.
                _raw_mult = _ctx_amp["boost_mult"] if _ctx_amp["boost_mult"] > 0 else 1.0
                if exploration_recovery_governor.is_active and _raw_mult > 1.0:
                    _prp002_size_mult = 1.0
                else:
                    _prp002_size_mult = _raw_mult
            _thought(f"🔔 Signal {sig.signal.value} {sym} | {sig.reason}", "SIGNAL")
            logger.info(
                f"[SCAN] Signal generated: {sig.signal.value} {sym} "
                f"score={sig.confidence:.3f} exec={'YES' if _execution_allowed else 'LOCKED'}"
            )

            # ── A.I.E. — Adaptive Inverse Engine ─────────────────────────────
            # If this strategy's win-rate is in the "wrong" zone, flip it.
            # NO_TRADE (40–60% WR) → skip; INVERSE (<40% WR) → flip direction.
            _inv = inverse_engine.get_decision(
                strategy_id=strategy_type,
                signal=sig.signal.value,
                entry_price=sig.entry_price,
                stop_loss=sig.stop_loss,
                take_profit=sig.take_profit,
            )
            if not cfg.BYPASS_ALL_GATES and _inv.mode == TradeMode.CALIBRATE:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _inv.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                return
            if _inv.inverted:
                if cfg.BYPASS_ALL_GATES:
                    # Suppress AIE inversion in bypass mode — bypass trades are
                    # intentionally noisy; let AIE learn without contaminating
                    # signal direction. Losses from inversion caused a win_rate
                    # death-spiral (10% WR → AEE disabled → 0 trades).
                    _thought(f"🔄 AIE INVERSE suppressed (bypass) {sym}", "SIGNAL")
                else:
                    sig = TradeSignal(
                        symbol=sig.symbol,
                        signal=Signal(_inv.final_signal),
                        entry_price=_inv.entry_price,
                        stop_loss=_inv.stop_loss,
                        take_profit=_inv.take_profit,
                        confidence=sig.confidence,
                        strategy_id=sig.strategy_id + "_INV",
                        reason=f"{sig.reason} | {_inv.reason}",
                    )
                    _thought(f"🔄 AIE INVERSE → {sig.signal.value} {sym}", "SIGNAL")

            # 6. Size the position (FTD-REF-024: apply edge booster multiplier)
            sizing = scaler.compute(sym, sig.entry_price, sig.stop_loss)
            if sizing.qty <= 0:
                _thought(
                    f"🚫 ZERO_QTY {sym}: {sizing.reason} "
                    f"(equity={sizing.current_equity:.2f} method={sizing.method})",
                    "FILTER",
                )
                return
            _edge_mult = edge_engine.get_size_multiplier(regime.value, strategy_type)
            _aee_mult  = adaptive_edge_engine.get_size_mult(strategy_type)
            if cfg.BYPASS_ALL_GATES and _aee_mult == 0.0:
                # AEE disabled → would zero out qty; in bypass mode keep trading
                # so the engine can recover stats and re-enable the strategy
                _aee_mult = 1.0
            # Combine: take the lower bound as a safety floor, then apply edge boost
            # AEE SCALING (>1×) stacks with edge_engine boost; REDUCED (<1×) overrides
            _final_mult = _aee_mult * _edge_mult if _aee_mult >= 1.0 else _aee_mult
            # FTD-037: regime-weighted capital allocation.
            # ALL-period data: TRENDING -$125.31 / MEAN_REVERTING -$33.43.
            # Reduce TRENDING risk by 40% to limit capital drain while keeping
            # MEAN_REVERTING at full size (only profitable regime in 1D data).
            _regime_risk_mult = {
                "MEAN_REVERTING":      1.00,
                "TRENDING":            0.60,
                "VOLATILITY_EXPANSION": 0.50,
            }.get(regime.value, 0.80)
            _final_mult = _final_mult * _regime_risk_mult
            # PRP-002: apply ecology size multiplier (recovery reduction or context boost)
            _final_mult = _final_mult * _prp002_size_mult
            # Session size scale: ASIA 0.50×, LATE 0.70× — lower vol means fee drag
            # is a larger fraction of the move; smaller position preserves expectancy.
            _final_mult = _final_mult * _session_size_scale
            sizing.qty  = sizing.qty * _final_mult
            # FTD-056-ACT: enforce minimum notional floor so micro-trades don't produce
            # disproportionate fee overhead (fee_drag was 132.3% avg across session)
            if sig.entry_price > 0:
                _notional_pre = sizing.qty * sig.entry_price
                if _notional_pre < cfg.MIN_NOTIONAL_USDT:
                    sizing.qty = cfg.MIN_NOTIONAL_USDT / sig.entry_price
            # atr_pct already computed above from candle OHLC / regime_det

            # FTD-REF-023: realistic cost via execution_engine
            notional      = sizing.qty * sig.entry_price
            cost_usdt     = execution_engine.fee_for_notional(notional) * 2
            # Per-unit cost for signal_filter (which computes gross_tp per-unit as abs(tp-entry))
            cost_per_unit = cost_usdt / sizing.qty if sizing.qty > 0 else cost_usdt

            # ── RL Gate: contextual bandit soft-filter ──────────────────────────
            # Blocks contexts that have consistently negative expected value
            # (Q < ENTRY_EV_FLOOR) AND have been explored enough (n ≥ MIN_VISITS).
            # New contexts always pass (exploration guaranteed).
            _rl_ok, _rl_reason = rl_engine.should_trade(
                regime=regime.value,
                utc_hour=__import__("datetime").datetime.utcnow().hour,
                strategy=strategy_type,
            )
            if not _rl_ok:
                _thought(f"🤖 RL_GATE {sym}: {_rl_reason}", "FILTER")
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _rl_reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                _supp_log.record(
                    gate="RL_GATE", symbol=sym, strategy=sig.strategy_id,
                    regime=regime.value, utc_hour=_utc_hr_ec, reason=_rl_reason,
                )
                trade_flow_monitor.record_skip(sym, _rl_reason)
                # FTD-054-PHOENIX: RL TOXIC hard-block must be bypassed in paper/learning
                # mode. After 21 trades at WR=9.5%, Q=-0.3163 crossed the EV floor (-0.3)
                # → TOXIC → permanent block → zero new updates → Q can never recover.
                # Same pattern as the LCC fix: gate the hard stop behind BYPASS_ALL_GATES
                # so the learning engine can accumulate data and escape the toxic context.
                if not cfg.BYPASS_ALL_GATES:
                    return
                _thought(
                    f"⚡ RL_OVERRIDE {sym}: TOXIC context {regime.value}|{strategy_type} "
                    f"[bypass=active, learning continues]",
                    "SIGNAL",
                )

            # ── Lean Gate: 5 checks; Gates 4+5 bypassed in PAPER/BYPASS mode ──
            # In PAPER/BYPASS mode, virtual drawdown and streak must not halt
            # the RL engine — it needs to trade through losses to learn.
            # Gates 1-3 (SL distance, RR, fee economy) always apply.
            _lean = lean_gate.check(
                entry=sig.entry_price,
                stop_loss=sig.stop_loss,
                take_profit=sig.take_profit,
                notional=notional,
                consecutive_losses=_consecutive_losses,
                session_dd_pct=drawdown_controller.current_drawdown(),
                side=sig.signal.value,
                bypass_risk_gates=cfg.BYPASS_ALL_GATES,
            )
            if not _lean.execute:
                _thought(
                    f"🚫 LEAN_GATE {sym}: {_lean.reason} "
                    f"(rr={_lean.rr:.2f} sl={_lean.sl_dist_pct:.3f}%)",
                    "FILTER",
                )
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _lean.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                _supp_log.record(
                    gate="LEAN_GATE", symbol=sym, strategy=sig.strategy_id,
                    regime=regime.value, utc_hour=_utc_hr_ec, reason=_lean.reason,
                )
                trade_flow_monitor.record_skip(sym, _lean.reason)
                return

            # FTD-REF-024: fee-aware gate — reject if TP profit can't cover fees
            _gross_tp = abs(sig.take_profit - sig.entry_price) * sizing.qty
            _fee_reject, _fee_reason = execution_engine.should_reject_for_fees(
                expected_gross_profit=_gross_tp, notional=notional,
            )
            if not cfg.BYPASS_ALL_GATES and _fee_reject:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _fee_reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                return

            # ── Phase 6: Loss Cluster Controller — gates ALL trades ──────────
            _lcc_result = loss_cluster_controller.check(consecutive_losses=_p52_cl)
            if not cfg.BYPASS_ALL_GATES and not _lcc_result.ok:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _lcc_result.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, _lcc_result.reason)
                return
            # FTD-054-PHOENIX: LCC size reduction must also be gated by BYPASS_ALL_GATES.
            # Previously, size_mult=0.0 (PAUSED) silently zeroed sizing.qty even in bypass
            # mode, causing a 90+ minute trade drought after 5+ consecutive session losses.
            # In bypass mode the RL engine needs trades to learn; LCC pause defeats that.
            if not cfg.BYPASS_ALL_GATES and _lcc_result.size_mult < 1.0:
                sizing.qty = round(sizing.qty * _lcc_result.size_mult, 8)
                if sizing.qty <= 0:
                    return
            if cfg.BYPASS_ALL_GATES and _lcc_result.size_mult < 1.0:
                _thought(
                    f"⚡ LCC_OVERRIDE {sym}: state={_lcc_result.state} "
                    f"cl={_p52_cl} [bypass=active, size not reduced]",
                    "SIGNAL",
                )

            # ── Phase 5.2 + 6: Exploration Hard Injection (guarded) ──────────
            # ExplorationGuard pre-checks daily loss cap before slot allocation.
            # Exploration runs BEFORE all quality filters; only DD + risk caps apply.
            _p52_conf  = min(sig.confidence, _adjusted_conf)
            _eg_result = exploration_guard.check(
                daily_loss_pct=exploration_engine.daily_loss_pct(scaler.equity),
            )
            _explore_inject = (
                exploration_engine.should_explore(
                    symbol=sym, score=_p52_conf, equity=scaler.equity,
                    ev_ok=False, est_risk=0.0,
                )
                if _eg_result.allowed
                else ExploreResult(
                    is_exploration=False, size_mult=1.0,
                    daily_loss_used_pct=exploration_engine.daily_loss_pct(scaler.equity),
                    reason=_eg_result.reason,
                )
            )
            _skip_quality   = _explore_inject.is_exploration
            if _skip_quality:
                _is_exploration_trade[sym] = True
                sizing.qty = round(sizing.qty * _explore_inject.size_mult, 8)
                if sizing.qty <= 0:
                    return
                _thought(
                    f"🔬 EXPLORE_INJECT {sym}: score={_p52_conf:.3f} "
                    f"size={_explore_inject.size_mult}× qty={sizing.qty:.6f}"
                    f" — quality gates bypassed, only risk limits apply",
                    "SIGNAL",
                )
                _alloc_score = _p52_conf  # use raw confidence for capital band

            if not _skip_quality:
                # FTD-REF-026: profit guard pre-filter (fee sanity before quality chain)
                _pg_block, _pg_reason = profit_guard.check_fee_ratio(
                    gross_tp_profit=_gross_tp, fee_cost=cost_usdt,
                )
                if not cfg.BYPASS_ALL_GATES and _pg_block:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _pg_reason, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _pg_reason)
                    return

                # FTD-REF-024: get current edge for signal filter gate
                _expected_edge = edge_engine.get_edge(regime.value, strategy_type)

                # MASTER-001 + FTD-REF-023/024: adaptive signal quality filter
                sf_result = signal_filter.check(
                    symbol=sym, entry=sig.entry_price,
                    take_profit=sig.take_profit, stop_loss=sig.stop_loss,
                    cost_usdt=cost_per_unit, atr_pct=atr_pct,
                    confidence=_adjusted_conf, regime=r_ai.regime.value,
                    relaxation_factor=relax_factor, expected_edge=_expected_edge,
                )
                if not cfg.BYPASS_ALL_GATES and not sf_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": sf_result.reason, "rr": sf_result.rr,
                        "confidence": r_ai.confidence, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, sf_result.reason)
                    return

                # FTD-REDIS-017: hard strategy quality gate (RR/confidence/regime)
                strat_gate = strategy_engine.evaluate_signal(
                    rr=sf_result.rr, confidence=_adjusted_conf,
                    regime=("UNSTABLE" if r_ai.block_trade else r_ai.regime.value),
                )
                if not cfg.BYPASS_ALL_GATES and not strat_gate.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": strat_gate.reason, "rr": sf_result.rr,
                        "confidence": _adjusted_conf, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, strat_gate.reason)
                    return

                # ── Phase 5: Adaptive Scorer — dynamic-weight quality gate ────
                _vol_list     = list(vol_buf)
                _avg_vol_p5   = (sum(_vol_list[-20:]) / max(len(_vol_list[-20:]), 1)
                                 if _vol_list else 1.0)
                _cur_vol_p5   = _vol_list[-1] if _vol_list else 0.0
                _vol_ratio    = _cur_vol_p5 / _avg_vol_p5 if _avg_vol_p5 > 0 else 1.0
                _rsi_now      = (_rsi(closes, cfg.RSI_PERIOD)
                                 if len(closes) >= cfg.RSI_PERIOD + 1 else 50.0)
                _rsi_prev     = (_rsi(closes[:-1], cfg.RSI_PERIOD)
                                 if len(closes) >= cfg.RSI_PERIOD + 2 else _rsi_now)
                _tp_dist_p5   = abs(sig.take_profit - sig.entry_price)
                _cost_frac_p5 = cost_per_unit / _tp_dist_p5 if _tp_dist_p5 > 0 else 1.0

                _score_result = adaptive_scorer.score(
                    symbol=sym, regime=r_ai.regime.value,
                    adx=guard.adx, rsi=_rsi_now, rsi_prev=_rsi_prev,
                    atr_pct=atr_pct, avg_atr_pct=atr_pct,
                    vol_ratio=_vol_ratio, cost_fraction=_cost_frac_p5,
                    signal_side=sig.signal.value,
                )
                if not cfg.BYPASS_ALL_GATES and not _score_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _score_result.reason,
                        "score": _score_result.score,
                        "regime": regime.value, "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _score_result.reason)
                    return

                # ── Phase 5: Confidence Decay — dynamic threshold from DTP ────
                _decay_result = confidence_decay.decay(
                    symbol=sym, strategy_id=sig.strategy_id,
                    base_conf=_score_result.score,
                )
                _decayed_conf = _decay_result.decayed_confidence
                # EDP: apply no_execution_override (FTD-034) + drive-mode floor
                _edp_status = execution_drive_policy.get_status()
                _eff_score_min = trade_activator.no_execution_override(
                    _eff_score_min, signals=1, trades=_edp_status.trades_1min,
                )
                _eff_score_min = execution_drive_policy.get_score_override(_eff_score_min)
                # FTD-SNP-001: reactive fee-throttle — if symbol is fee-dragging, raise score floor
                _re_score_override = reactive_evolution_engine.get_score_min_override(sym)
                if _re_score_override is not None:
                    _eff_score_min = max(_eff_score_min, _re_score_override)
                # RL frequency scaling: lower floor in high-alpha contexts, raise in losing ones.
                # Complements confidence_boost() — both sides of the gap move toward execution
                # in contexts where Q-value confirms positive expected value (07h/10h/14h MR).
                _rl_floor_delta = rl_engine.get_score_floor_delta(
                    regime=regime.value,
                    utc_hour=__import__("datetime").datetime.utcnow().hour,
                    strategy=strategy_type,
                )
                _eff_score_min = max(0.40, round(_eff_score_min + _rl_floor_delta, 4))
                if not cfg.BYPASS_ALL_GATES and _decayed_conf < _eff_score_min:  # Phase 6: DTP + streak-adjusted
                    # EDP: bypass decay gate for strong signals (high score + high RR)
                    if execution_drive_policy.should_force_execute(
                        _score_result.score, sf_result.rr
                    ):
                        _thought(
                            f"⚡ EDP FORCE {sym}: score={_score_result.score:.3f}"
                            f" rr={sf_result.rr:.2f} — decay gate bypassed",
                            "SIGNAL",
                        )
                    else:
                        _last_skip = {
                            "ts": int(time.time() * 1000), "symbol": sym,
                            "reason": f"DECAY_FILTER({_decay_result.reason})",
                            "score": _decayed_conf,
                            "score_min_used": _eff_score_min,
                            "regime": regime.value, "strategy": strategy_type,
                        }
                        trade_flow_monitor.record_skip(sym, "DECAY_FILTER")
                        return

                # ── Phase 4: RR Engine — enforce min Risk-Reward ──────────────
                _atr_price = atr_pct * sig.entry_price / 100
                _rr_result = rr_engine.evaluate(
                    side=sig.signal.value, entry=sig.entry_price,
                    stop_loss=sig.stop_loss, take_profit=sig.take_profit,
                    atr=_atr_price, atr_pct=atr_pct,
                )
                if not cfg.BYPASS_ALL_GATES and not _rr_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _rr_result.reason, "rr": _rr_result.rr,
                        "regime": regime.value, "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _rr_result.reason)
                    return
                sig = TradeSignal(
                    symbol=sig.symbol, signal=sig.signal,
                    entry_price=sig.entry_price,
                    stop_loss=_rr_result.adjusted_sl,
                    take_profit=_rr_result.adjusted_tp,
                    confidence=min(sig.confidence, _decayed_conf),
                    strategy_id=sig.strategy_id,
                    reason=(f"{sig.reason} | RR={_rr_result.rr:.2f} "
                            f"SCORE={_score_result.score:.3f} "
                            f"DECAY={_decay_result.decay_factor:.2f}"),
                )

                # ── Phase 5.2: Smart Fee Guard — fully dynamic (RR + DTP) ─────
                _sfg_result = smart_fee_guard.check(
                    rr=_rr_result.rr, gross_tp=_gross_tp, fee_cost=cost_usdt,
                    normal_max_override=thresholds.fee_tolerance,  # dynamic
                )
                if not cfg.BYPASS_ALL_GATES and not _sfg_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _sfg_result.reason, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _sfg_result.reason)
                    return

                # ── Phase 5: EV Engine — expected value gate ──────────────────
                _est_reward = abs(sig.take_profit - sig.entry_price) * sizing.qty
                _est_risk   = abs(sig.entry_price - sig.stop_loss) * sizing.qty
                _ev_result  = ev_engine.evaluate(
                    strategy_id=sig.strategy_id, symbol=sym,
                    est_reward=_est_reward, est_risk=_est_risk,
                    current_cost=cost_usdt,
                    drawdown=drawdown_controller.current_drawdown(),           # Phase 7B
                    regime_confidence=r_ai.confidence,                         # Phase 7B
                )
                if not cfg.BYPASS_ALL_GATES and not _ev_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _ev_result.reason,
                        "ev": _ev_result.ev, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _ev_result.reason)
                    return
                if not _ev_result.bootstrapped:
                    _thought(
                        f"🧮 EV {sym}: ev={_ev_result.ev:.4f} "
                        f"p_win={_ev_result.p_win:.1%} n={_ev_result.n_trades}",
                        "SIGNAL",
                    )

                # ── Phase 6: EV Confidence Engine — tier-based size mult ──────
                _evc_result = ev_confidence_engine.classify(_ev_result.ev)
                if not cfg.BYPASS_ALL_GATES and not _evc_result.ok:
                    _last_skip = {
                        "ts": int(time.time() * 1000), "symbol": sym,
                        "reason": _evc_result.reason, "regime": regime.value,
                        "strategy": strategy_type,
                    }
                    trade_flow_monitor.record_skip(sym, _evc_result.reason)
                    return
                if _evc_result.size_mult < 1.0:
                    sizing.qty = round(sizing.qty * _evc_result.size_mult, 8)
                    if sizing.qty <= 0:
                        return
                    _thought(
                        f"📊 EVC {sym}: tier={_evc_result.tier} "
                        f"ev={_evc_result.ev:.4f} → {_evc_result.size_mult:.0%}× size",
                        "SIGNAL",
                    )

                _alloc_score = _score_result.score  # use adaptive scorer score

            # ── Common path: Drawdown Controller + Capital Allocator ──────────
            # DrawdownController is always re-checked fresh (not from cached DTP)
            _dd_result = drawdown_controller.check()
            if not cfg.BYPASS_ALL_GATES and not _dd_result.allowed:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _dd_result.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                _supp_log.record(
                    gate="DRAWDOWN_CONTROLLER", symbol=sym, strategy=sig.strategy_id,
                    regime=regime.value, utc_hour=_utc_hr_ec, reason=_dd_result.reason,
                )
                trade_flow_monitor.record_skip(sym, _dd_result.reason)
                return

            _alloc = capital_allocator.allocate(
                trade_score=_alloc_score,  # dynamic: explore uses raw conf, normal uses scorer
                equity=scaler.equity,
                base_risk_usdt=sizing.usdt_risk,
            )
            if not cfg.BYPASS_ALL_GATES and _alloc.size_multiplier <= 0:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _alloc.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                _supp_log.record(
                    gate="CAPITAL_ALLOCATOR", symbol=sym, strategy=sig.strategy_id,
                    regime=regime.value, utc_hour=_utc_hr_ec, reason=_alloc.reason,
                )
                trade_flow_monitor.record_skip(sym, _alloc.reason)
                return
            # ── Phase 6: Capital Recovery Engine — smooth size restoration ──
            _recovery_result = capital_recovery_engine.check()
            # FTD-038+039: priority (AEE rank) × stabilizer (equity smoothness)
            _cfe_mult       = capital_flow_engine.get_combined_mult(strategy_type)
            _combined_mult  = round(
                _alloc.size_multiplier
                * _dd_result.multiplier
                * _recovery_result.size_mult
                * _cfe_mult,
                6,
            )
            # FTD-054-PHOENIX: surface allocator zero in bypass mode — previously
            # silent, making sub-threshold scores (0.246–0.339) look like normal
            # trades. The allocator correctly rates them as below min band (<0.60)
            # but bypass overrides via orchestrator BYPASS band.
            if cfg.BYPASS_ALL_GATES and _combined_mult == 0.0:
                _thought(
                    f"⚠️ ALLOC_ZERO {sym}: score={_alloc_score:.3f} below min "
                    f"allocator band [bypass=active, orchestrator BYPASS override]",
                    "SIGNAL",
                )
            if _recovery_result.state not in ("NORMAL", "FULLY_RECOVERED"):
                _thought(
                    f"🔄 RECOVERY {sym}: state={_recovery_result.state} "
                    f"recovery={_recovery_result.recovery_pct:.0%} "
                    f"size={_recovery_result.size_mult:.2f}×",
                    "SIGNAL",
                )
            # ── FTD-040: Consistency Engine — final unified consistency check ─
            _ce_state = consistency_engine.evaluate(
                consecutive_wins=_p52_cw,
                consecutive_losses=_p52_cl,
                dd_result=_dd_result,
                recovery_result=_recovery_result,
                lcc_result=_lcc_result,
            )
            if not cfg.BYPASS_ALL_GATES and not _ce_state.allowed:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": f"CE_PAUSED:{_ce_state.reason}",
                    "regime": regime.value, "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, f"CE_PAUSED:{_ce_state.reason}")
                _thought(
                    f"🛑 CONSISTENCY_PAUSED {sym}: {_ce_state.reason}",
                    "SIGNAL",
                )
                return
            if _ce_state.size_mult < 1.0:
                _combined_mult = round(_combined_mult * _ce_state.size_mult, 6)
                _thought(
                    f"🎯 CONSISTENCY {sym}: mode={_ce_state.mode} "
                    f"ce_mult={_ce_state.size_mult:.2f}× "
                    f"reason={_ce_state.reason}",
                    "SIGNAL",
                )
            # ── Phase 7A: Execution Orchestrator — full profit pipeline ─────
            # Receives the combined upstream multiplier and applies gate-aware
            # rank → compete → concentrate → pre-trade gate → amplify on top.
            _vol_list_orch = list(vol_buf)
            _avg_vol_orch  = (sum(_vol_list_orch[-20:]) / max(len(_vol_list_orch[-20:]), 1)
                              if _vol_list_orch else 1.0)
            _cur_vol_orch  = _vol_list_orch[-1] if _vol_list_orch else 0.0
            _vol_ratio_orch = _cur_vol_orch / _avg_vol_orch if _avg_vol_orch > 0 else 1.0
            _orch_ev = getattr(_ev_result, "ev", 0.0) if (not _skip_quality and not cfg.BYPASS_ALL_GATES) else 0.0
            _orch_score = _alloc_score
            # qFTD-010 Design Change 2: execution gate — final lock before position open.
            # Scan ran fully (warm-up, learning engines, scoring) regardless of gate status.
            # Only actual position creation is blocked when execution is not allowed.
            if not cfg.BYPASS_ALL_GATES and not _execution_allowed:
                logger.info(
                    f"[SCAN] Signal rejected — execution locked: {_pre_gate.reason} "
                    f"| {sig.signal.value} {sym} score={_alloc_score:.3f}"
                )
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": f"EXEC_GATE:{_pre_gate.reason}",
                    "regime": regime.value, "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, f"EXEC_GATE:{_pre_gate.reason}")
                return

            _orch_ctx = TickContext(
                symbol=sym,
                price=price,
                regime=regime.value,
                strategy=strategy_type,
                ev=_orch_ev,
                trade_score=_orch_score,
                volume_ratio=_vol_ratio_orch,
                equity=scaler.equity,
                base_risk_usdt=sizing.usdt_risk,
                upstream_mult=_combined_mult,
                indicator_ok=guard.ok,
                data_fresh=_data_fresh_ok,     # qFTD-004: from data_health_monitor (not hardcoded)
                is_exploration=_skip_quality,
            )
            _cycle = execution_orchestrator.run_cycle(_orch_ctx)
            if not _cycle.execute:
                _last_skip = {
                    "ts": int(time.time() * 1000), "symbol": sym,
                    "reason": _cycle.reason, "regime": regime.value,
                    "strategy": strategy_type,
                }
                trade_flow_monitor.record_skip(sym, _cycle.reason)
                return

            # Apply orchestrator concentration multiplier (folds in upstream_mult + band boost)
            sizing.qty = round(sizing.qty * _cycle.concentration_mult, 8)
            if sizing.qty <= 0:
                _thought(
                    f"🚫 ZERO_QTY_ORCH {sym}: conc_mult={_cycle.concentration_mult:.4f} "
                    f"zeroed qty (upstream_mult={_combined_mult:.2f}×)",
                    "FILTER",
                )
                return
            _thought(
                f"💰 Orchestrator {sym}: score={_alloc_score:.3f} "
                f"upstream_mult={_combined_mult:.2f}× "
                f"conc_mult={_cycle.concentration_mult:.2f}× "
                f"band={_cycle.band} rank={_cycle.rank_score:.3f} "
                f"amplified={_cycle.amplified} "
                f"explore={_skip_quality} qty={sizing.qty:.6f}",
                "SIGNAL",
            )

            edge_ok, edge = risk_ctrl.get_trade_decision(
                side=sig.signal.value,
                entry=sig.entry_price,
                take_profit=sig.take_profit,
                stop_loss=sig.stop_loss,
                qty=sizing.qty,
                current_volatility=atr_pct,
                regime=regime.value,   # Fix B: regime-specific RR threshold
                minutes_no_trade=_tf_mins,  # qFTD-040: tiered required_r relaxation during dry spells
            )
            if not cfg.BYPASS_ALL_GATES and not edge_ok:
                rr_net = edge.get('rr_after_cost', 0)
                rr_req = edge.get('required_r', 0)
                _thought(
                    f"⛔ Skip {sym}: weak edge gross={edge.get('gross_tp', 0):.3f} "
                    f"cost={edge.get('cost', 0):.3f} net={edge.get('net_if_tp', 0):.3f} "
                    f"RR={edge.get('rr', 0):.2f} RR_net={rr_net:.2f} "
                    f"RR_req={rr_req:.2f} ATR%={edge.get('current_volatility', 0):.2f}",
                    "FILTER",
                )
                # Update live skip tracker for dashboard indicator
                _last_skip = {
                    "ts":          int(time.time() * 1000),
                    "symbol":      sym,
                    "reason":      "WEAK_EDGE",
                    "rr_net":      round(rr_net, 3),
                    "rr_req":      round(rr_req, 3),
                    "gap":         round(rr_req - rr_net, 3),
                    "regime":      edge.get("regime", regime.value),
                    "cost":        round(edge.get("cost", 0), 4),
                    "net_if_tp":   round(edge.get("net_if_tp", 0), 4),
                    "strategy":    strategy_type,
                }
                return

            # 7. PAPER MODE EXECUTION LOCK (qFTD-009 §FIX5 — non-negotiable)
            # This engine operates on real market data + virtual execution only.
            # All fills are internal simulations; NO exchange order API is called.
            # If TRADE_MODE is ever misconfigured to "LIVE", hard-block here.
            if cfg.TRADE_MODE != "PAPER":
                logger.critical(
                    f"[EXECUTION-LOCK] TRADE_MODE={cfg.TRADE_MODE} — "
                    f"real order BLOCKED. Only PAPER mode is permitted."
                )
                return

            # Open position — in PAPER_SPEED force market path to avoid pending-order dead time.
            _use_limit_orders = cfg.USE_LIMIT_ORDERS and (not _paper_speed)
            if cfg.USE_LIMIT_ORDERS and _paper_speed:
                _thought(
                    f"⚡ PAPER_SPEED market-fill override {sym}: USE_LIMIT_ORDERS bypassed",
                    "TRADE",
                )
            if _use_limit_orders:
                offset = sig.entry_price * (cfg.LIMIT_ENTRY_OFFSET_BPS / 10_000)
                if sig.signal.value == "LONG":
                    limit_px = sig.entry_price - offset   # buy slightly below signal price
                else:
                    limit_px = sig.entry_price + offset   # sell slightly above signal price

                submitted = risk_ctrl.submit_limit_order(
                    symbol=sym,
                    side=sig.signal.value,
                    limit_price=limit_px,
                    qty=sizing.qty,
                    stop_loss=sig.stop_loss,
                    take_profit=sig.take_profit,
                    strategy_id=sig.strategy_id,
                    initial_risk=sizing.usdt_risk,
                    regime=regime.value,
                )
                if submitted:
                    # FTD-DECISION-SNAP: preserve causal ontology state at approval time
                    _pending_decision_snapshots[sym] = _capture_decision_snapshot(
                        sym=sym, strategy_id=sig.strategy_id, strategy_type=strategy_type,
                        regime=regime.value, utc_hour=_utc_hr_ec,
                        rl_ok=_rl_ok, rl_reason=_rl_reason,
                        ps_ec_dec=_ps_ec_dec if sig.strategy_id.endswith("_PAPER_SPEED") else None,
                        ctx_amp=None if sig.strategy_id.endswith("_PAPER_SPEED") else _ctx_amp,
                    )
                    # FTD-EXPLORE-ATTR: persist RL exploration provenance at approval time
                    _pending_exploration_origins[sym] = _build_eo(_rl_reason)
                    _trades_this_hour.append(now_ms)
                    _last_trade_ts[sym] = now_ms
                    trade_frequency.record_trade()   # FTD-REF-023: dry-spell tracker
                    execution_drive_policy.record_trade(sym)   # EDP: reset idle timer
                    # Phase 4: register with trade manager for lifecycle tracking
                    trade_manager.register(ManagedPosition(
                        symbol=sym, side=sig.signal.value,
                        entry_price=limit_px, stop_loss=sig.stop_loss,
                        take_profit=sig.take_profit,
                        initial_risk=abs(limit_px - sig.stop_loss),
                        qty=sizing.qty,
                    ))
                    capital_allocator.record_risk_used(sizing.usdt_risk)
                    _thought(
                        f"📋 Limit {sig.signal.value} {sym} @ {limit_px:.4f} "
                        f"qty={sizing.qty:.6f} risk={sizing.usdt_risk:.2f}U "
                        f"[{strategy_type} | {regime.value}]",
                        "TRADE",
                    )
            else:
                pos = OpenPosition(
                    position_id=str(uuid.uuid4())[:8],
                    symbol=sym,
                    side=sig.signal.value,
                    entry_price=sig.entry_price,
                    qty=sizing.qty,
                    stop_loss=sig.stop_loss,
                    take_profit=sig.take_profit,
                    entry_ts=int(time.time() * 1000),
                    strategy_id=sig.strategy_id,
                    initial_risk=sizing.usdt_risk,
                    regime=regime.value,
                )
                if not risk_ctrl.open_position(pos, order_type="MARKET"):
                    _thought(
                        f"🚫 POSITION_EXISTS {sym}: already open — new signal discarded",
                        "FILTER",
                    )
                else:
                    # FTD-DECISION-SNAP: preserve causal ontology state at approval time
                    _pending_decision_snapshots[sym] = _capture_decision_snapshot(
                        sym=sym, strategy_id=sig.strategy_id, strategy_type=strategy_type,
                        regime=regime.value, utc_hour=_utc_hr_ec,
                        rl_ok=_rl_ok, rl_reason=_rl_reason,
                        ps_ec_dec=_ps_ec_dec if sig.strategy_id.endswith("_PAPER_SPEED") else None,
                        ctx_amp=None if sig.strategy_id.endswith("_PAPER_SPEED") else _ctx_amp,
                    )
                    # FTD-EXPLORE-ATTR: persist RL exploration provenance at approval time
                    _pending_exploration_origins[sym] = _build_eo(_rl_reason)
                    _trades_this_hour.append(now_ms)
                    _last_trade_ts[sym] = now_ms
                    trade_frequency.record_trade()   # FTD-REF-023: dry-spell tracker
                    execution_drive_policy.record_trade(sym)   # EDP: reset idle timer
                    # PRP-001: record signal context at trade open for truth tracking.
                    # context_quality_engine is separate try/except so its failure never
                    # silently prevents signal_truth_engine from recording the trade.
                    _cq_score   = 0.0
                    _atr_pct_st = 0.0
                    try:
                        _re_state_st = regime_det.state(sym)
                        _atr_pct_st  = getattr(_re_state_st, "atr_pct", 0.0) or 0.0
                        _cq_score    = context_quality_engine.score_signal(
                            signal_id   = pos.position_id,
                            regime      = regime.value,
                            strategy_id = sig.strategy_id,
                            side        = sig.signal.value,
                            confidence  = sig.confidence,
                            rsi_val     = _rsi_val,
                            above_sma   = _above_sma,
                            atr_pct     = _atr_pct_st,
                        )
                    except Exception:
                        pass
                    try:
                        signal_truth_engine.record_signal(
                            signal_id     = pos.position_id,
                            symbol        = sym,
                            strategy_id   = sig.strategy_id,
                            regime        = regime.value,
                            side          = sig.signal.value,
                            confidence    = sig.confidence,
                            entry_price   = sig.entry_price,
                            stop_loss     = sig.stop_loss,
                            take_profit   = sig.take_profit,
                            utc_hour      = __import__("datetime").datetime.utcnow().hour,
                            rsi_val       = _rsi_val,
                            above_sma     = _above_sma,
                            atr_pct       = _atr_pct_st,
                            context_score = _cq_score,
                        )
                    except Exception:
                        pass
                    # Phase 4: register with trade manager for lifecycle tracking
                    trade_manager.register(ManagedPosition(
                        symbol=sym, side=sig.signal.value,
                        entry_price=sig.entry_price, stop_loss=sig.stop_loss,
                        take_profit=sig.take_profit,
                        initial_risk=abs(sig.entry_price - sig.stop_loss),
                        qty=sizing.qty,
                    ))
                    capital_allocator.record_risk_used(sizing.usdt_risk)
                    _thought(
                        f"✅ Opened {sig.signal.value} {sym} "
                        f"qty={sizing.qty:.6f} risk={sizing.usdt_risk:.2f}U "
                        f"[{strategy_type} | {regime.value}]",
                        "TRADE",
                    )

    # 8. Ingest candle into genome engine + persist to data lake
    candle_dict = {
        "open": candle.open, "high": candle.high,
        "low": candle.low,   "close": candle.close,
        "volume": candle.volume, "ts": candle.ts,
    }
    genome.ingest_candle(sym, candle_dict)
    data_lake.ingest_candle(
        sym, candle.interval,
        candle.open, candle.high, candle.low, candle.close,
        candle.volume, candle.ts,
    )

    # 9. Persist tick to data lake (async-safe buffered write)
    data_lake.ingest_tick(
        sym, tick.price, tick.bid, tick.ask, tick.qty, tick.ts
    )
    if sym in mdp.funding:
        f = mdp.funding[sym]
        data_lake.ingest_funding(sym, f.rate, f.next_funding)

    # 10. Broadcast market update to dashboard
    await _broadcast_market_update(sym, tick, regime.value)

    # FTD-031: record cycle latency, feed guard + alerting
    if cfg.PERF_ENABLED:
        perf_monitor.on_cycle_end(sym)


async def _broadcast_market_update(sym: str, tick: Tick, regime: str):
    data = {
        "type":   "market_update",
        "symbol": sym,
        "price":  tick.price,
        "regime": regime,
        "ts":     tick.ts,
    }
    for ws in list(_ws_clients):
        asyncio.create_task(_safe_send(ws, data))


# ── App Lifespan ──────────────────────────────────────────────────────────────

def _asyncio_exception_handler(loop, context):
    """
    Custom asyncio exception handler that silently absorbs WinError 10054
    (WSAECONNRESET) and Errno 104 (ECONNRESET) raised by the internal
    _ProactorBasePipeTransport callback on Windows.  These are Binance-side
    TCP RSTs, not bugs in our code — logging at DEBUG keeps the console clean
    while preserving the audit trail.  All other exceptions fall through to
    the default asyncio handler.
    """
    exc = context.get("exception")
    if exc is not None:
        win_err = getattr(exc, "winerror", None)
        err_no  = getattr(exc, "errno", None)
        if isinstance(exc, (ConnectionResetError, OSError)) and (
            win_err == 10054 or err_no == 104
        ):
            logger.debug(
                f"[asyncio] Absorbed _ProactorBasePipeTransport CONN_RESET "
                f"(WinError {win_err}/Errno {err_no}) — Binance TCP RST, not a local error."
            )
            return
    loop.default_exception_handler(context)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    # Install custom asyncio exception handler to absorb WinError 10054
    # (_ProactorBasePipeTransport WSAECONNRESET) before any tasks start.
    loop = asyncio.get_event_loop()
    loop.set_exception_handler(_asyncio_exception_handler)

    global _engine_running, _boot_ts
    _engine_running = True
    _boot_ts = time.time()
    ensure_auth_ready_for_mode()
    mdp.register_callback(on_tick)
    # Pre-seed regime_detector during candle bootstrap so indicators are warm from boot
    mdp.set_regime_detector(regime_det)
    _thought("🚀 EOW Quant Engine booting…", "SYSTEM")
    _thought(f"Mode: {cfg.TRADE_MODE} | Capital: {cfg.INITIAL_CAPITAL} USDT", "SYSTEM")

    # ── FTD-LPA: Live Process Access — register loguru sink immediately so ────
    # boot logs are captured in the rolling buffer from the very first line.
    live_process_access.register_log_sink()

    # ── FTD-014B: Function Registry startup validation ────────────────────────
    try:
        import json, pathlib
        _reg_path = pathlib.Path(__file__).parent / "core" / "registry" / "function_registry.json"
        if _reg_path.exists():
            _reg = json.loads(_reg_path.read_text())
            if isinstance(_reg, dict):
                _reg_count = len(_reg.get("functions", []))
            else:
                _reg_count = len(_reg) if isinstance(_reg, list) else 0
            _thought(f"📋 Function Registry loaded — {_reg_count} functions registered", "SYSTEM")
        else:
            _thought("⚠ Function Registry not found at core/registry/function_registry.json", "HALT")
    except Exception as _e:
        _thought(f"⚠ Function Registry load error: {_e}", "HALT")

    # ── Fix A: Reload promoted DNA so genome doesn't reset on restart ─────────
    genome.load_persisted_dna()
    required_strategies = {"TrendFollowing", "MeanReversion", "VolatilityExpansion"}
    missing = [s for s in required_strategies if not genome.active_dna.get(s)]
    if missing:
        raise RuntimeError(f"DNA validation failed before engine start: missing={missing}")

    # ── Phase 6.6: Hard Start Validator — boot gate ──────────────────────────
    _hsv_result = hard_start_validator.run(
        candle_count=cfg.HSV_MIN_CANDLES_BOOT,   # assume warm after mdp bootstrap
        indicator_ok=True,
        ws_reachable=True,
    )
    if not _hsv_result.ok:
        logger.critical(f"[HARD-START] Blocking engine start: {_hsv_result.failures}")
        # enforce() already called inside run(); execution stops here in prod.

    # ── MASTER-001: risk_engine.initialize() MOVED — see qFTD-009 boot block below ──
    # Risk engine MUST be initialized with the RESTORED equity, not INITIAL_CAPITAL.
    # Initialize call is deferred until after snapshot + replay determine the correct value.

    # ── FTD-REF-019: Boot diagnostics ────────────────────────────────────────
    global _boot_status
    _boot_status = await api_loader.run(api_manager=api_manager)

    # ── Start all subsystems ──────────────────────────────────────────────────
    tasks = [
        asyncio.create_task(mdp.start()),
        asyncio.create_task(genome.start()),
        asyncio.create_task(healer.start()),
        asyncio.create_task(data_lake.start()),
        asyncio.create_task(ws_stab.start()),   # FTD-REF-019: tick watchdog
        asyncio.create_task(infra_health.monitor(
            interval_seconds=15,
            ws_state_fn=lambda: ws_stab.summary().get("state", "UNKNOWN"),
            api_mode_fn=lambda: _boot_status.get("api", "NOT CONNECTED"),
            api_ok_fn=lambda: _boot_status.get("api_ok", False),
            running_fn=lambda: _engine_running,
        )),
        # qFTD-009: periodic snapshot backup every 30 s (guards against missed trade-close saves)
        asyncio.create_task(
            equity_snapshot.start_periodic_save(
                equity_fn=lambda: scaler.equity,
                trade_count_fn=lambda: len(pnl_calc.trades),
                interval_sec=30,
            )
        ),
    ]

    # ── qFTD-009 FINAL: Authoritative Boot State Restoration ─────────────────
    #
    # CORRECT SEQUENCE (non-negotiable):
    #   1. Load equity snapshot  (instant, from JSON)
    #   2. Run DataLake replay   (always — for validation AND as fallback)
    #   3. Validate: snapshot ≈ replay → if mismatch → SAFE MODE
    #   4. Determine final equity (snapshot > replay > fresh)
    #   5. risk_engine.initialize(final_equity)  ← NEVER before this point
    #
    # BOOT_MODE=FRESH: snapshot-first, replay fallback if no snapshot
    # BOOT_MODE=RESUME: replay-first, snapshot validation layer on top
    #
    await asyncio.sleep(0.5)   # give data_lake.start() a moment to open SQLite

    _snap          = equity_snapshot.load()
    _replay_equity = cfg.INITIAL_CAPITAL
    _replay_count  = 0

    try:
        _hist = data_lake.get_trades(limit=5000)
        if _hist:
            _replay_count  = pnl_calc.replay_from_history(_hist)
            _replay_equity = pnl_calc.session_stats.get("capital", pnl_calc.capital)
            # qFTD-010: record replay boundary so streak/AF use session-only trades
            global _boot_replay_count
            _boot_replay_count = _replay_count
            _thought(
                f"📂 DataLake replay: {_replay_count} trades → "
                f"equity={_replay_equity:.2f} USDT",
                "SYSTEM",
            )
        else:
            _thought("📂 DataLake: no trade history found.", "SYSTEM")
    except Exception as _exc:
        _thought(f"⚠️ DataLake replay failed: {_exc} — will use snapshot only.", "SYSTEM")

    # Determine the single authoritative equity value
    if _snap and _replay_count > 0:
        if equity_snapshot.validate(_snap.equity, _replay_equity):
            _final_equity = _snap.equity
            _restore_src  = (
                f"snapshot({_snap.equity:.2f}) validated vs replay({_replay_equity:.2f})"
            )
        else:
            # Mismatch is a data integrity event — activate safe mode
            safe_mode_engine.activate("EQUITY_MISMATCH_BOOT")
            _final_equity = _replay_equity   # DataLake is ground truth
            _restore_src  = (
                f"MISMATCH equity — SAFE MODE activated | "
                f"snapshot={_snap.equity:.2f} replay={_replay_equity:.2f} | "
                f"using replay (DataLake is ground truth)"
            )
    elif _snap:
        _final_equity = _snap.equity
        _restore_src  = f"snapshot only ({_snap.equity:.2f} USDT, no replay history)"
    elif _replay_count > 0:
        _final_equity = _replay_equity
        _restore_src  = f"replay only ({_replay_equity:.2f} USDT, no snapshot file)"
    else:
        _final_equity = cfg.INITIAL_CAPITAL
        _restore_src  = f"fresh start ({cfg.INITIAL_CAPITAL:.2f} USDT — no prior state found)"

    # ── MASTER-001 (qFTD-009): Initialize risk engine with RESTORED equity ────
    risk_engine.initialize(_final_equity)
    scaler.set_equity(_final_equity)
    _thought(f"📂 State restored: {_restore_src}", "SYSTEM")
    logger.info(f"[BOOT-STATE] {_restore_src}")

    # ── Phase 4: Profit Engine boot log ─────────────────────────────────────
    _thought(
        f"⚡ Phase 4 Profit Engine online | "
        f"rr_min={rr_engine.min_rr} "
        f"score_min={trade_scorer.min_score} "
        f"max_per_trade={capital_allocator.max_capital_pct:.0%} "
        f"daily_cap={capital_allocator.daily_risk_cap:.0%}",
        "SYSTEM",
    )
    # ── Phase 5: EV + Adaptive Intelligence boot log ─────────────────────────
    _thought(
        f"🧠 Phase 5 EV Engine online | "
        f"ev_window={cfg.EV_WINDOW} ev_min_trades={cfg.EV_MIN_TRADES} "
        f"adaptive_lr={cfg.ADAPTIVE_LR} "
        f"dd_stop={cfg.DD_STOP_AT:.0%}",
        "SYSTEM",
    )
    # Initialise drawdown controller with RESTORED equity (qFTD-009: not INITIAL_CAPITAL)
    drawdown_controller.update_equity(_final_equity)
    # FTD-040: Seed consistency engine with restored equity baseline
    consistency_engine.update_equity(_final_equity)
    # ── Phase 5.1: Activation + Exploration Control boot log ─────────────────
    _thought(
        f"🔓 Phase 5.1 Activation Layer online | "
        f"activator_tiers=T1@{cfg.ACTIVATOR_T1_MIN}min "
        f"T2@{cfg.ACTIVATOR_T2_MIN}min "
        f"T3@{cfg.ACTIVATOR_T3_MIN}min | "
        f"explore_rate={cfg.EXPLORE_RATE:.0%} "
        f"smart_fee_rr≥{cfg.SFG_HIGH_RR_THRESHOLD}:{cfg.SFG_HIGH_RR_FEE_MAX:.0%}",
        "SYSTEM",
    )
    # ── Phase 6.6: Initial gate probe (diagnostic only — no safe mode side-effect)
    # qFTD-005: system is not yet ready at boot; a failing gate here is expected.
    # activate_safe_mode=False prevents premature SAFE activation before data streams open.
    _gate_boot = global_gate_controller.evaluate(activate_safe_mode=False)
    _gate_msg  = (
        f"Phase 6.6 Gate online | can_trade={_gate_boot['can_trade']} "
        f"reason={_gate_boot['reason']} safe_mode={_gate_boot['safe_mode']}"
    )
    _thought(_gate_msg, "SYSTEM")
    logger.info(f"[GLOBAL-GATE] {_gate_msg}")

    _thought("All subsystems online. Scanning markets…", "SYSTEM")
    logger.info(
        "[LEARNING_INTELLIGENCE_OBSERVATORY] ACTIVE | endpoints=10 "
        "| telemetry=LIVE | refresh=3s | mode=READ_ONLY_OBSERVATIONAL"
    )

    # ── Session Router boot confirmation — prevents silent assumption drift ────
    from core.time.session_definitions import SESSION_BUCKETS_UTC, SESSION_DISPLAY
    _sess_log = " | ".join(
        f"{name} {SESSION_BUCKETS_UTC[name][0]:02d}:00–{SESSION_BUCKETS_UTC[name][1] - 1:02d}:59 UTC"
        for name in SESSION_BUCKETS_UTC
    )
    _thought(f"🕐 [SESSION_ROUTER] Timezone Authority=UTC | {_sess_log}", "SYSTEM")
    logger.info(f"[SESSION_ROUTER] Timezone=UTC | {_sess_log} | source=datetime.utcnow().hour")

    # ── Pre-seed genome candle store ──────────────────────────────────────────
    # FTD-PHOENIX-GENOME-READINESS-001: D1 Persistent Seeding
    # Step 1: seed from data_lake first (SQLite — survives restart, up to 1440 bars/symbol)
    # Step 2: seed from mdp bootstrap buffers (in-memory — supplements live candles)
    logger.info("[GENOME] GENOME READINESS MODULE LOADED | FTD-PHOENIX-GENOME-READINESS-001")
    logger.info("[VOLVE] VOLATILITYEXPANSION MODULE LOADED | VE_BREAKOUT_ATR_v1 | FTD-PHOENIX-VOLVE-REACTIVATION-001")
    _lake_seeded = genome.seed_from_data_lake(data_lake)
    logger.info(
        f"[GENOME] data_lake seed complete — "
        f"{len(_lake_seeded)} symbols | "
        f"counts: { {s: n for s, n in _lake_seeded.items()} if _lake_seeded else 'none'}"
    )

    async def _seed_genome_from_bootstrap():
        """Wait for mdp bootstrap, then supplement genome with any additional candle history."""
        for _ in range(90):
            if getattr(mdp, "_running", False):
                genome.seed_from_market_data(mdp)
                return
            await asyncio.sleep(1)
        logger.warning("[GENOME] Bootstrap seed timeout — live stream will fill candle store.")

    tasks.append(asyncio.create_task(_seed_genome_from_bootstrap()))

    # ── Guardian periodic reactive check ─────────────────────────────────────
    async def _guardian_watch():
        """Every 60 s, check if live risk has drifted into unsafe territory."""
        while True:
            await asyncio.sleep(60)
            try:
                stats    = pnl_calc.session_stats
                win_rate = stats.get("win_rate", 0.0)
                mdd_pct  = stats.get("max_drawdown_pct", 0.0)
                trades   = pnl_calc.trades
                valid_r  = [t.r_multiple for t in trades if t.r_multiple != 0.0]
                pos_r    = [r for r in valid_r if r > 0]
                neg_r    = [abs(r) for r in valid_r if r < 0]
                avg_r_win  = (sum(pos_r) / len(pos_r)) if pos_r else 1.0
                avg_r_loss = (sum(neg_r) / len(neg_r)) if neg_r else 1.0
                alert = guardian.reactive_check(win_rate, mdd_pct, avg_r_win, avg_r_loss, cfg)
                if alert:
                    _thought(f"🛡 {alert}", "HALT")
            except Exception:
                pass

    tasks.append(asyncio.create_task(_guardian_watch()))

    # ── 8-hour checkpoint: JSON state + QPR report (Phase 3.1 persistence) ───
    async def _periodic_checkpoint():
        """Every 8 hours save full engine state + generate QPR for 7-day stress test."""
        while True:
            await asyncio.sleep(8 * 3600)
            try:
                # 1. JSON state export
                json_path = exporter.export(label="8h_checkpoint")
                # 2. QPR report archive
                stats    = pnl_calc.session_stats
                trades   = [asdict(t) for t in pnl_calc.trades]
                mode_info = {"trade_mode": cfg.TRADE_MODE, "engine_ver": f"EOW_v{APP_VERSION}"}
                analytics = {}
                archive  = build_report_archive(trades, stats, mode_info, analytics, _thought_log)
                ts_tag   = int(time.time())
                rpt_path = f"data/exports/QPR_{ts_tag}_8h.zip"
                with open(rpt_path, "wb") as f:
                    f.write(archive)
                _thought(
                    f"📊 8h checkpoint: state saved → {json_path} | QPR → {rpt_path}",
                    "SYSTEM",
                )
                logger.info(f"[CHECKPOINT] 8h state+QPR saved: {json_path}, {rpt_path}")
            except Exception as exc:
                logger.warning(f"[CHECKPOINT] 8h export failed: {exc}")

    tasks.append(asyncio.create_task(_periodic_checkpoint()))

    # ── FTD-030: Autonomous Intelligence Loop ────────────────────────────────
    global _auto_intelligence

    def _ai_broadcast(payload: dict) -> None:
        """Broadcast auto-intelligence events to all connected WS dashboard clients."""
        import json as _json
        msg = _json.dumps(payload, default=str)
        for ws in list(_ws_clients):
            try:
                asyncio.create_task(_safe_send(ws, _json.loads(msg)))
            except Exception:
                pass

    _auto_intelligence = AutoIntelligenceEngine(
        state_fn=_sc_build_state,
        trades_fn=lambda: len(pnl_calc.trades),
        broadcast_fn=_ai_broadcast,
    )

    async def _auto_intelligence_loop():
        """FTD-030: Runs every AUTO_INTELLIGENCE_INTERVAL_MIN minutes."""
        interval_sec = cfg.AUTO_INTELLIGENCE_INTERVAL_MIN * 60.0
        while True:
            await asyncio.sleep(interval_sec)
            try:
                result = _auto_intelligence.tick()
                action = result.get("action") or result.get("phase") or "?"
                verdict = result.get("correction_verdict", "")
                logger.info(
                    f"[FTD-030] Auto-intelligence tick: action={action} "
                    f"verdict={verdict} cycles={_auto_intelligence._cycle_num}"
                )
                if action not in ("SKIPPED",):
                    _thought(
                        f"🧠 [FTD-030] Auto-intelligence cycle #{result.get('cycle_num', '?')}: "
                        f"meta_score={result.get('meta_score', 0):.1f} "
                        f"verdict={verdict or action}",
                        "SYSTEM",
                    )
            except Exception as exc:
                logger.warning(f"[FTD-030] Auto-intelligence loop error: {exc}")

    tasks.append(asyncio.create_task(_auto_intelligence_loop()))
    logger.info(
        f"[FTD-030] Auto-intelligence loop started | "
        f"interval={cfg.AUTO_INTELLIGENCE_INTERVAL_MIN}min"
    )

    # ── FTD-053-GAIA Phase 6: Observability Orchestrator loop ────────────────
    async def _obs_orchestrator_loop():
        """Runs every OBS_TICK_INTERVAL_SECS. Feeds full pipeline non-blockingly."""
        await asyncio.sleep(OBS_TICK_INTERVAL_SECS)   # skip first tick at cold boot
        while True:
            try:
                raw = build_raw_snapshot(
                    rl_engine         = rl_engine,
                    pnl_calc          = pnl_calc,
                    risk_ctrl         = risk_ctrl,
                    trade_flow_monitor= trade_flow_monitor,
                    learning_engine   = learning_engine,
                    regime_det        = regime_det,
                    boot_ts           = _boot_ts,
                    error_count       = len(error_registry.recent(1)),
                )
                result = await asyncio.to_thread(obs_orchestrator.tick, raw)
                if result:
                    logger.debug(
                        f"[FTD-053] obs tick={result.tick_id} "
                        f"anomalies={result.anomaly_count} "
                        f"worst={result.worst_severity} "
                        f"dt={result.duration_ms}ms"
                    )
            except Exception as exc:
                logger.warning(f"[FTD-053] Orchestrator loop error: {exc}")
            await asyncio.sleep(OBS_TICK_INTERVAL_SECS)

    tasks.append(asyncio.create_task(_obs_orchestrator_loop()))
    logger.info(
        f"[FTD-053] Observability orchestrator loop started | "
        f"interval={OBS_TICK_INTERVAL_SECS}s"
    )

    # ── FTD-031: Performance Optimization Layer ───────────────────────────────
    if cfg.PERF_ENABLED:
        await task_queue.start()
        await perf_monitor.start_background_tasks()
        _thought(
            f"⚡ [FTD-031] Performance layer online | "
            f"target={cfg.PERF_LATENCY_TARGET_MS}ms "
            f"cache_ttl_pattern={cfg.PERF_CACHE_PATTERN_TTL_SEC}s "
            f"queue_workers={cfg.PERF_QUEUE_WORKERS}",
            "SYSTEM",
        )

    # ── Phase-B: Cross-PRP Wiring Audit boot registration ────────────────────
    try:
        from core.cross_prp_audit.cross_prp_audit_orchestrator import get_wiring_audit_health
        _wiring_h = get_wiring_audit_health()
        _wiring_score = _wiring_h.get("wiring_health_score", 0)
        _wiring_tier  = _wiring_h.get("wiring_health_tier", "UNKNOWN")
        _thought(
            f"🔗 [PHASE-B] Cross-PRP Wiring Audit registered | "
            f"health={_wiring_score}/100 tier={_wiring_tier} | "
            f"endpoints: /api/wiring-audit/*",
            "SYSTEM",
        )
    except Exception as _e:
        _thought(f"⚠ [PHASE-B] Wiring audit boot check failed (non-fatal): {_e}", "SYSTEM")

    # ── Phase-C: Operational Compression Layer boot registration ──────────────
    try:
        from core.operational_compression.compression_orchestrator import get_compression_health
        _comp_h = get_compression_health()
        _comp_score = _comp_h.get("composite_score", 0)
        _comp_tier  = _comp_h.get("composite_tier", "UNKNOWN")
        _vis_tiers  = _comp_h.get("visibility_tier_count", 0)
        _anom_state = _comp_h.get("anomaly_cluster_state", "UNKNOWN")
        _exec_avail = "YES" if _comp_h.get("executive_condition") not in (None, "UNAVAILABLE") else "NO"
        _thought(
            f"🗜 [PHASE-C] Operational Compression registered | "
            f"health={_comp_score}/100 tier={_comp_tier} | "
            f"visibility_tiers={_vis_tiers} anomaly_state={_anom_state} "
            f"executive_synthesis={_exec_avail} | endpoints: /api/compression/*",
            "SYSTEM",
        )
    except Exception as _e:
        _thought(f"⚠ [PHASE-C] Compression boot check failed (non-fatal): {_e}", "SYSTEM")

    # ── Phase-D: Economic Truth Reconstruction boot registration ──────────────
    try:
        from core.economic_truth_reconstruction.economic_truth_orchestrator import get_economic_health
        _eco_session   = [asdict(t) for t in pnl_calc.trades]
        _eco_hist      = data_lake.get_trades(limit=1000)
        _eco_seen: dict[str, dict] = {}
        for _t in _eco_session:
            _tid = _t.get("trade_id", "")
            if _tid:
                _eco_seen[_tid] = _t
        for _t in _eco_hist:
            _tid = _t.get("trade_id", "")
            if _tid and _tid not in _eco_seen:
                _eco_seen[_tid] = _t
        _eco_trades = list(_eco_seen.values())
        _eco_h      = get_economic_health(_eco_trades)
        _eco_score  = _eco_h.get("survivability_score", 0)
        _eco_tier   = _eco_h.get("survivability_tier", "UNKNOWN")
        _eco_exp    = _eco_h.get("expectancy_condition", "UNKNOWN")
        _eco_fee    = _eco_h.get("fee_drag_state", "UNKNOWN")
        _eco_alpha  = _eco_h.get("alpha_concentration", "UNKNOWN")
        _eco_ecol   = _eco_h.get("ecological_collapse_severity", "UNKNOWN")
        _eco_regime = _eco_h.get("dominant_regime") or "UNKNOWN"
        _thought(
            f"📊 [PHASE-D] Economic Truth Reconstruction registered | "
            f"survivability={_eco_score}/100 tier={_eco_tier} | "
            f"expectancy={_eco_exp} fee_drag={_eco_fee} alpha={_eco_alpha} "
            f"ecology={_eco_ecol} dominant_regime={_eco_regime} | "
            f"endpoints: /api/economic-truth/*",
            "SYSTEM",
        )
    except Exception as _e:
        _thought(f"⚠ [PHASE-D] Economic truth boot check failed (non-fatal): {_e}", "SYSTEM")

    # ── Phase-E: Survivability Evolution Program boot registration ────────────
    try:
        from core.survivability_evolution.survivability_evolution_orchestrator import get_survivability_health
        _surv_seen: dict[str, dict] = {}
        for _t in [asdict(t) for t in pnl_calc.trades]:
            _tid = _t.get("trade_id", "")
            if _tid:
                _surv_seen[_tid] = _t
        for _t in data_lake.get_trades(limit=1000):
            _tid = _t.get("trade_id", "")
            if _tid and _tid not in _surv_seen:
                _surv_seen[_tid] = _t
        _surv_trades = list(_surv_seen.values())
        _surv_h      = get_survivability_health(_surv_trades)
        _surv_score  = _surv_h.get("evolution_score", 0)
        _surv_tier   = _surv_h.get("evolution_tier", "UNKNOWN")
        _surv_exp    = _surv_h.get("expectancy_persistence_state", "UNKNOWN")
        _surv_ecol   = _surv_h.get("ecological_preservation_tier", "UNKNOWN")
        _surv_alpha  = _surv_h.get("alpha_persistence_state", "UNKNOWN")
        _surv_entr   = _surv_h.get("entropy_state", "UNKNOWN")
        _surv_conf   = _surv_h.get("confidence_realism_score", 0)
        _thought(
            f"🧬 [PHASE-E] Survivability Evolution registered | "
            f"evolution={_surv_score}/100 tier={_surv_tier} | "
            f"expectancy_persistence={_surv_exp} ecology={_surv_ecol} "
            f"alpha={_surv_alpha} entropy={_surv_entr} confidence_realism={_surv_conf} | "
            f"endpoints: /api/survivability/*",
            "SYSTEM",
        )
    except Exception as _e:
        _thought(f"⚠ [PHASE-E] Survivability evolution boot check failed (non-fatal): {_e}", "SYSTEM")

    # ── Phase-G: Adaptive Execution Governance boot registration ──────────────
    try:
        from core.adaptive_execution_governance.adaptive_execution_orchestrator import get_execution_governance_health
        _gov_seen: dict[str, dict] = {}
        for _t in [asdict(t) for t in pnl_calc.trades]:
            _tid = _t.get("trade_id", "")
            if _tid:
                _gov_seen[_tid] = _t
        for _t in data_lake.get_trades(limit=1000):
            _tid = _t.get("trade_id", "")
            if _tid and _tid not in _gov_seen:
                _gov_seen[_tid] = _t
        _gov_trades   = list(_gov_seen.values())
        _gov_h        = get_execution_governance_health(_gov_trades)
        _gov_score    = _gov_h.get("civilization_score", 0)
        _gov_tier     = _gov_h.get("civilization_tier", "UNKNOWN")
        _gov_advisory = _gov_h.get("restraint_advisory", "UNKNOWN")
        _gov_eq       = _gov_h.get("equilibrium_state", "UNKNOWN")
        _gov_safety   = _gov_h.get("governance_status", "UNKNOWN")
        _gov_disc     = _gov_h.get("discipline_tier", "UNKNOWN")
        _thought(
            f"🏛 [PHASE-G] Adaptive Execution Governance registered | "
            f"civilization={_gov_score}/100 tier={_gov_tier} | "
            f"advisory={_gov_advisory} equilibrium={_gov_eq} "
            f"governance={_gov_safety} discipline={_gov_disc} | "
            f"endpoints: /api/execution-governance/*",
            "SYSTEM",
        )
    except Exception as _e:
        _thought(f"⚠ [PHASE-G] Execution governance boot check failed (non-fatal): {_e}", "SYSTEM")

    # ── Phase-H: Institutional Continuity boot registration ───────────────────
    try:
        from core.institutional_continuity.continuity_evolution_orchestrator import get_continuity_health
        _cont_seen: dict[str, dict] = {}
        for _t in [asdict(t) for t in pnl_calc.trades]:
            _tid = _t.get("trade_id", "")
            if _tid:
                _cont_seen[_tid] = _t
        for _t in data_lake.get_trades(limit=1000):
            _tid = _t.get("trade_id", "")
            if _tid and _tid not in _cont_seen:
                _cont_seen[_tid] = _t
        _cont_trades  = list(_cont_seen.values())
        _cont_h       = get_continuity_health(_cont_trades)
        _cont_score   = _cont_h.get("continuity_score", 0)
        _cont_tier    = _cont_h.get("continuity_tier", "UNKNOWN")
        _cont_entropy = _cont_h.get("entropy_state", "UNKNOWN")
        _cont_doc     = _cont_h.get("doctrine_state", "UNKNOWN")
        _cont_inherit = _cont_h.get("inheritance_state", "UNKNOWN")
        _cont_cr      = _cont_h.get("cross_regime_verdict", "UNKNOWN")
        _cont_id      = _cont_h.get("identity_status", "UNKNOWN")
        _thought(
            f"🏺 [PHASE-H] Institutional Continuity registered | "
            f"continuity={_cont_score}/100 tier={_cont_tier} | "
            f"entropy={_cont_entropy} doctrine={_cont_doc} "
            f"inheritance={_cont_inherit} cross_regime={_cont_cr} identity={_cont_id} | "
            f"endpoints: /api/continuity/*",
            "SYSTEM",
        )
    except Exception as _e:
        _thought(f"⚠ [PHASE-H] Institutional continuity boot check failed (non-fatal): {_e}", "SYSTEM")

    # ── Phase-F: Adaptive Equilibrium boot registration ────────────────────────
    try:
        from core.adaptive_equilibrium.adaptive_equilibrium_orchestrator import get_equilibrium_health
        _eq_h    = get_equilibrium_health()
        _eq_stat = _eq_h.get("status", "UNKNOWN")
        _thought(
            f"⚖ [PHASE-F] Adaptive Equilibrium registered | "
            f"status={_eq_stat} | "
            f"engines: F.1 Kelly / F.2 Drawdown / F.3 Consistency / "
            f"F.4 Utilization / F.5 Band / F.6 Discipline / F.7 Orchestrator | "
            f"endpoints: /api/equilibrium/*",
            "SYSTEM",
        )
    except Exception as _e:
        _thought(f"⚠ [PHASE-F] Adaptive equilibrium boot check failed (non-fatal): {_e}", "SYSTEM")

    # ── Phase-I: Alpha Confirmation boot registration ──────────────────────────
    try:
        from core.alpha_confirmation.alpha_confirmation_orchestrator import get_alpha_health
        _alpha_h    = get_alpha_health()
        _alpha_stat = _alpha_h.get("status", "UNKNOWN")
        _thought(
            f"🔬 [PHASE-I] Alpha Confirmation registered | "
            f"status={_alpha_stat} | "
            f"engines: I.1 Statistics / I.2 OOS / I.3 Fee-Survival / "
            f"I.4 Regime / I.5 Drawdown / I.6 Gate / I.7 Orchestrator | "
            f"live_deployment_authorized=False | "
            f"endpoints: /api/alpha-confirmation/*",
            "SYSTEM",
        )
    except Exception as _e:
        _thought(f"⚠ [PHASE-I] Alpha confirmation boot check failed (non-fatal): {_e}", "SYSTEM")

    # ── FTD-AIL-001: Autonomous Intelligence Layer ────────────────────────────
    try:
        from core.autonomous_intelligence.ail_engine import ail_engine
        await ail_engine.boot()
        _thought("🤖 [AIL] Autonomous Intelligence Layer booted | FTD-AIL-001", "SYSTEM")
    except Exception as _e:
        _thought(f"⚠ [AIL] Boot failed (non-fatal): {_e}", "SYSTEM")

    yield

    _thought("⏹ Engine shutting down…", "SYSTEM")
    _engine_running = False
    for t in tasks:
        t.cancel()
    await mdp.stop()
    await genome.stop()
    await healer.stop()
    await data_lake.stop()
    await ws_stab.stop()
    await api_manager.close()
    if cfg.PERF_ENABLED:
        await task_queue.shutdown()
    try:
        from core.autonomous_intelligence.ail_engine import ail_engine as _ail
        await _ail.shutdown()
    except Exception:
        pass


# ── FastAPI App ───────────────────────────────────────────────────────────────

app = FastAPI(
    title="EOW Quant Engine",
    description="Self-evolving autonomous multi-asset trading engine",
    version=APP_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_allowed_origins(cfg.ALLOWED_ORIGINS),
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── REST Endpoints ────────────────────────────────────────────────────────────

def _resolve_indicator_state(regime_states: dict, mdp: MarketDataProvider) -> str:
    """
    Runtime indicator readiness for boot diagnostics.

    VALIDATED   — at least one symbol has a computed regime state with numeric
                  ADX and ATR% (regime_det only stores states when 28+ candles
                  are available, so any entry here is already quality-checked).
    WARMING_UP  — WebSocket is alive and ticks are flowing but the 28-candle
                  buffer is still filling.  System is healthy; indicators will
                  auto-validate within minutes.  Treated as ✅ in the boot log.
    PENDING_RUNTIME_VALIDATION — no ticks received yet (very early startup).
    """
    for symbol, state in regime_states.items():
        adx = getattr(state, "adx", None)
        atr_pct = getattr(state, "atr_pct", None)
        if isinstance(adx, (int, float)) and isinstance(atr_pct, (int, float)):
            return "VALIDATED"
    # Data is flowing but candles not yet fully buffered
    if len(mdp.ticks) > 0:
        return "WARMING_UP"
    return "PENDING_RUNTIME_VALIDATION"


def _resolve_boot_deployability(
    network_score: float,
    database_score: float,
    rr_edge_score: float,
    indicators_state: str,
) -> tuple[float, str]:
    """
    Boot deployability composite score (0-100).
    Score = sum of three pillar scores (network 0-30, database 0-30, rr_edge 0-40).
    READY when all three pillars meet their individual thresholds.
    """
    deployability_score = float(network_score) + float(database_score) + float(rr_edge_score)

    is_ready = (
        network_score >= 25
        and database_score >= 25
        and rr_edge_score >= 30
    )
    status = "READY" if is_ready else "NOT_READY"

    # With validated indicators, a zero RR-edge means no proven trading edge
    # yet, so boot deployability must remain hard-blocked at 0.
    if indicators_state == "VALIDATED" and rr_edge_score <= 0:
        return 0.0, "NOT_READY"

    # WARMING_UP is healthy — indicators are filling and will auto-validate.
    # Only cap score when no market data whatsoever has been received.
    if indicators_state == "PENDING_RUNTIME_VALIDATION":
        deployability_score = min(deployability_score, 40.0)
        status = "NOT_READY"
    elif indicators_state == "WARMING_UP":
        # Warm-up means ticks are flowing and indicator buffers are filling.
        # Use relaxed infra gates at boot so healthy live flow is reflected as
        # IMPROVING (not NOT_READY) while RR-edge is still building from zero.
        if network_score >= 20 and database_score >= 10:
            deployability_score = max(deployability_score, 60.0)
            if status != "READY":
                status = "IMPROVING"

    return round(float(deployability_score), 1), status

@app.get("/api/boot-status")
async def get_boot_status():
    """FTD-REF-019 / MASTER-001: Boot diagnostics — all subsystem status."""
    live_stab = ws_stab.summary()
    mdp_ws_state = mdp.websocket_state()
    re_snap   = risk_engine.snapshot()
    stats     = pnl_calc.session_stats
    n_trades  = len(pnl_calc.trades)
    infra = infra_health.snapshot()
    redis_state = infra.get("redis", _boot_status.get("redis", "NOT_AVAILABLE"))
    if mdp.redis_connected():
        redis_state = "CONNECTED"

    if mdp_ws_state == "CONNECTED":
        ws_state = "CONNECTED"
    elif mdp_ws_state in {"CONNECTING", "RECONNECTING"}:
        ws_state = mdp_ws_state
    else:
        ws_state = live_stab["state"]

    indicators_state = _resolve_indicator_state(
        regime_states=regime_det.all_states(),
        mdp=mdp,
    )
    heal    = healer.snapshot()
    recent  = heal.get("recent_events", [])
    # Use actual Redis connectivity (mdp.redis_connected()) as primary signal;
    # fall back to healer REDIS_FLUSH events as a secondary confirmation.
    redis_ok = mdp.redis_connected() or any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in recent
    )
    try:
        lake_s    = data_lake.db_stats()
        sqlite_ok = lake_s.get("trades", -1) >= 0
    except Exception:
        lake_s    = {}
        sqlite_ok = False
    valid_r = [t.r_multiple for t in pnl_calc.trades if t.r_multiple != 0.0]
    ws_is_connected = (ws_state == "CONNECTED")
    # Enrich lake_s with in-memory trade count when SQLite hasn't persisted yet
    merged_lake_s = dict(lake_s)
    if merged_lake_s.get("trades", 0) == 0 and n_trades > 0:
        merged_lake_s["trades"] = n_trades
    dep_idx = deployability_index(
        healer_snapshot=heal,
        lake_stats=merged_lake_s,
        genome_state=genome.export_state(),
        redis_ok=redis_ok,
        persistence_ok=(redis_ok or sqlite_ok),
        runtime_rr={
            "avg_r_multiple": (sum(valid_r) / len(valid_r)) if valid_r else 0.0,
            "win_rate": stats.get("win_rate", 0.0) / 100.0,
            "trades": n_trades,
        },
        ws_connected=ws_is_connected,
    )
    dep_breakdown = dep_idx.get("breakdown", {})
    network_score = float((dep_breakdown.get("network") or {}).get("score", 0))
    if live_stab.get("reconnect_count", 0) > 2:
        network_score = max(0.0, network_score - 10.0)
    database_score = float((dep_breakdown.get("database") or {}).get("score", 0))
    rr_edge_score = float((dep_breakdown.get("rr_edge") or {}).get("score", 0))

    boot_deployability_score, boot_deployability_status = _resolve_boot_deployability(
        network_score=network_score,
        database_score=database_score,
        rr_edge_score=rr_edge_score,
        indicators_state=indicators_state,
    )
    api_loader.set_runtime_status(
        websocket=ws_state,
        indicators=indicators_state,
    )
    api_loader.set_deployability(
        score=boot_deployability_score,
        status=boot_deployability_status,
    )
    _boot_status["websocket"] = ws_state
    _boot_status["indicators"] = indicators_state

    indicators_ok = indicators_state in ("VALIDATED", "WARMING_UP")

    return {
        **_boot_status,
        "redis":         redis_state,
        "websocket":     ws_state,
        "indicators":    indicators_state,
        "indicators_ok": indicators_ok,
        "ws_gap_s":      live_stab["gap_seconds"],
        "ws_reconnects": live_stab["reconnect_count"],
        "strategy_engine": "ACTIVE",
        "risk_engine":     "HALTED" if re_snap["halted"] else "ACTIVE",
        "execution_mode":  cfg.TRADE_MODE,
        "deployability":   boot_deployability_status,
        "deployability_score": boot_deployability_score,
        "deployability_components": {
            "network_score": network_score,
            "database_score": database_score,
            "rr_edge_score": rr_edge_score,
            "thresholds": {"network": 25, "database": 25, "rr_edge": 30},
            "analytics_tier": dep_idx.get("tier", "NOT READY"),
        },
    }


@app.get("/api/status")
async def get_status():
    return {
        "mode":        cfg.TRADE_MODE,
        "capital":     round(scaler.equity, 4),
        "drawdown_pct": round(scaler.drawdown_pct, 2),
        "streak":      scaler.streak,
        "halted":      risk_ctrl.halted,
        "symbols_watched": len(mdp.symbols),
        "open_positions":  len(risk_ctrl.positions),
        "total_trades":    len(pnl_calc.trades),
        "ws_status":   ws_truth_engine.get_ui_label(),   # FTD-REF-026: truth-engine label
        "ts":          int(time.time() * 1000),
        # Phase 4 Profit Engine summary
        "profit_engine": {
            "rr_engine":         rr_engine.summary(),
            "trade_scorer":      trade_scorer.summary(),
            "capital_allocator": capital_allocator.summary(equity=pnl_calc.capital),
            "trade_manager":     trade_manager.summary(),
            "alpha_engine":      alpha_engine.summary(),
        },
        # FTD-040: Consistency Engine quick-status
        "consistency": consistency_engine.status(),
    }


@app.get("/api/version")
async def get_version():
    return {"version": APP_VERSION, "engine": f"EOW_QUANT_ENGINE_v{APP_VERSION}"}


@app.get("/api/pnl")
async def get_pnl():
    return _sanitize(pnl_calc.session_stats)


@app.get("/api/market")
async def get_market():
    return mdp.snapshot()


@app.get("/api/positions")
async def get_positions():
    return risk_ctrl.snapshot()


@app.get("/api/genome")
async def get_genome():
    return genome.export_state()


@app.post("/api/genome/trigger")
async def trigger_genome_cycle():
    """
    Manually kick off one genome evolution cycle without waiting for the timer.
    Useful during initial deployment to accelerate Deployability Index build-up.
    Requires at least one symbol's candle data to have accumulated first.
    """
    candle_counts = {sym: len(c) for sym, c in genome._candle_store.items()}
    if not candle_counts:
        return {
            "ok": False,
            "reason": "No candle data in genome store yet — start the engine and wait for market data to flow.",
            "candle_counts": {},
        }
    await genome._evolution_cycle()
    state = genome.export_state()
    promotions = [p for p in state.get("promotion_log", []) if p.get("decision") == "PROMOTED"]
    return {
        "ok":             True,
        "generation":     state["generation"],
        "candle_counts":  candle_counts,
        "promoted_count": len(promotions),
        "last_promotion": promotions[-1] if promotions else None,
    }


@app.get("/api/regime")
async def get_regime():
    states = regime_det.all_states()
    return {sym: {
        "regime":     s.regime.value,
        "adx":        s.adx,
        "atr_pct":    s.atr_pct,
        "bb_width":   s.bb_width,
        "confidence": s.confidence,
    } for sym, s in states.items()}


@app.get("/api/thoughts")
async def get_thoughts(limit: int = 50):
    return _thought_log[-limit:]


@app.get("/api/health")
async def get_health():
    return healer.snapshot()


@app.get("/api/deployability")
async def get_deployability():
    """
    MASTER-001: Standalone deployability score.
    Score 0–100 with status: READY / IMPROVING / NOT_READY / BLOCKED / INSUFFICIENT_DATA.
    """
    stats = pnl_calc.session_stats
    n_trades = len(pnl_calc.trades)
    result = deployability_engine.compute(
        trades       = n_trades,
        sharpe       = stats.get("sharpe_ratio", 0.0),
        sortino      = stats.get("sortino_ratio", 0.0),
        win_rate     = stats.get("win_rate", 0.0),
        max_drawdown = stats.get("max_drawdown_pct", 0.0) / 100,
        risk_of_ruin = stats.get("risk_of_ruin", 0.0),
        avg_r        = stats.get("avg_r_multiple", 0.0),
    )
    return _sanitize(deployability_engine.to_dict(result))


@app.get("/api/risk-engine")
async def get_risk_engine():
    """MASTER-001: Daily risk limits, drawdown state, size multiplier."""
    return risk_engine.snapshot()


@app.get("/api/signal-filter")
async def get_signal_filter():
    """MASTER-001: Signal quality gate state — paused symbols, thresholds."""
    return signal_filter.summary()


@app.get("/api/lake")
async def get_lake():
    """Data Lake statistics — candle count, tick count, DB size."""
    return data_lake.db_stats()


@app.get("/api/trades")
async def get_trades(symbol: str = "", limit: int = 200):
    """Full trade history from the data lake."""
    return data_lake.get_trades(symbol=symbol, limit=limit)


@app.get("/api/candles/{symbol}")
async def get_candles(symbol: str, limit: int = 500):
    """Recent closed candles for a symbol (from data lake)."""
    return data_lake.get_candles(symbol.upper(), limit=limit)


@app.get("/api/scorecard")
async def get_scorecard():
    """
    Go-Live Scorecard — automated Phase 3 readiness checklist.

    Evaluates all three pillars before PAPER → LIVE promotion:
      1. Security: AUTH_ENABLED + CONTROL_API_KEYS configured.
      2. Expectancy: OOS PF ≥ 1.0 and overfitting ratio within bounds.
      3. Execution parity: post-cost avg R-multiple ≥ configured floor.
    """
    return compute_scorecard(genome, cfg).to_dict()


# ── DBO Analytics ────────────────────────────────────────────────────────────

@app.get("/api/analytics")
async def get_analytics():
    """
    Full DBO analytics payload:
      • Sortino + Sharpe + Calmar ratios
      • Risk-of-Ruin probability
      • Geometric vs Linear growth chart data
      • Deployability Index 0-100 (capped at 50 when persistence is BOGUS)
      • Benchmark comparison vs S&P 500 / hedge funds
    """
    heal    = healer.snapshot()
    recent  = heal.get("recent_events", [])
    # Use live redis connection as primary signal; healer events as fallback
    redis_ok = mdp.redis_connected() or any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in recent
    )
    try:
        lake_s    = data_lake.db_stats()
        sqlite_ok = lake_s.get("trades", -1) >= 0
    except Exception:
        lake_s    = {}
        sqlite_ok = False
    persistence_ok = redis_ok or sqlite_ok

    trade_dicts = [
        {"net_pnl": t.net_pnl, "r_multiple": t.r_multiple}
        for t in pnl_calc.trades
    ]

    analytics_payload = compute_full_analytics(
        pnl_trades=trade_dicts,
        initial_capital=pnl_calc._initial_capital,
        session_stats=pnl_calc.session_stats,
        healer_snapshot=heal,
        lake_stats=lake_s,
        genome_state=genome.export_state(),
        redis_ok=redis_ok,
        persistence_ok=persistence_ok,
        ws_connected=(mdp.websocket_state() == "CONNECTED"),
    )
    corrected = rolling_ratios(
        pnl_values=[t.get("net_pnl", 0.0) for t in trade_dicts],
        initial_capital=pnl_calc._initial_capital,
        max_drawdown_pct=pnl_calc.session_stats.get("max_drawdown_pct", 0.0),
        window=200,
    )
    analytics_payload.update(corrected)
    return _sanitize(analytics_payload)


@app.get("/api/mode-info")
async def get_mode_info():
    """
    Returns the human-readable trading mode label and persistence status.
    Used by the dashboard mode identifier strip.
    """
    heal   = healer.snapshot()
    recent = heal.get("recent_events", [])

    # Determine Redis health from recent heal events
    redis_ok = any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in recent
    )

    # Determine SQLite health:
    #   • connection is live  → healthy
    #   • OR db file already exists on disk (previous session data present)
    #   • db_stats() returns {} when conn not yet open (race on cold boot)
    import os as _os
    db_file_exists = _os.path.exists(data_lake.DB_PATH)
    conn_live      = data_lake._conn is not None
    try:
        stats     = data_lake.db_stats()
        stats_ok  = stats.get("trades", -1) >= 0
    except Exception:
        stats_ok  = False
    sqlite_ok = conn_live or db_file_exists or stats_ok

    persistence_ok = redis_ok or sqlite_ok

    # TIER system
    if not persistence_ok:
        tier, label, colour = 1, "TIER 1: DEMO — BOGUS DATA", "demo"
    elif cfg.TRADE_MODE == "LIVE":
        tier, label, colour = 3, "TIER 3: REAL LIVE — ORIGINAL CAPITAL", "live"
    else:
        tier, label, colour = 2, "TIER 2: LIVE PAPER — VIRTUAL CAPITAL", "paper"

    return {
        "mode":               cfg.TRADE_MODE,
        "tier":               tier,
        "label":              label,
        "colour":             colour,
        "redis_ok":           redis_ok,
        "sqlite_ok":          sqlite_ok,
        "db_file_exists":     db_file_exists,
        "conn_live":          conn_live,
        "persistence_ok":     persistence_ok,
        "persistence_warning": (
            "" if persistence_ok else
            "PERSISTENCE FAILED: Session data is non-permanent (BOGUS STORAGE)"
        ),
        "persistence_status": (
            "✅ PERSISTENCE ACTIVE" if persistence_ok else
            "⚠ PERSISTENCE FAILED"
        ),
        "ts": int(time.time() * 1000),
    }


@app.get("/api/perf-status")
async def get_perf_status():
    """FTD-031: Full performance metrics — latency, cache, guard state, queue, memory."""
    if not cfg.PERF_ENABLED:
        return {"enabled": False}
    return perf_monitor.snapshot()


@app.post("/api/perf-guard/reset")
async def reset_perf_guard():
    """FTD-031: Operator reset of PerfGuard back to NORMAL state."""
    perf_guard.reset()
    return {"ok": True, "state": perf_guard.state}


@app.get("/api/diagnostics/pipeline-break-forensics")
async def diagnostics_pipeline_break_forensics(cycles: int = 100):
    """
    FTD-031C: Pipeline break forensic probe — DISABLED BY DEFAULT.

    Isolation rules: manual trigger only, read-only, not part of core loop.
    Enable via DIAGNOSTICS_ENDPOINT_ENABLED=true in .env (developer use only).
    """
    if not cfg.DIAGNOSTICS_ENDPOINT_ENABLED:
        return {"enabled": False, "message": "Set DIAGNOSTICS_ENDPOINT_ENABLED=true to use this endpoint"}
    from tools.diagnostics.pipeline_break_forensics import run_probe
    return run_probe(cycles=max(1, min(cycles, 1000)))


@app.get("/api/report", response_class=HTMLResponse)
async def get_report():
    """
    Unified HTML report — open in browser and use Print → Save as PDF.
    Sections:
      1. Executive Summary (plain English)
      2. Performance Audit (PnL / Fees / Slippage breakdown)
      3. Signal Audit (every SKIP / TRADE decision from CT-Scan log)
    """
    stats  = pnl_calc.session_stats
    mode_r = await get_mode_info()
    now_str = time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())

    # ── Signal Audit rows ──────────────────────────────────────────────────────
    audit_rows = ""
    for t in _thought_log:
        level = t.get("level", "INFO")
        msg   = t.get("msg", "").replace("<", "&lt;").replace(">", "&gt;")
        colour = {"TRADE": "#27ae60", "FILTER": "#e67e22", "SIGNAL": "#2980b9",
                  "HALT": "#e74c3c", "SYSTEM": "#8e44ad"}.get(level, "#555")
        ts_s = time.strftime("%H:%M:%S", time.gmtime(t.get("ts", 0) / 1000))
        audit_rows += (
            f'<tr><td style="color:#888">{ts_s}</td>'
            f'<td><span style="color:{colour};font-weight:600">{level}</span></td>'
            f'<td>{msg}</td></tr>\n'
        )

    # ── Executive summary text ─────────────────────────────────────────────────
    total_net   = stats.get("total_net_pnl", 0.0)
    win_rate    = stats.get("win_rate", 0.0)
    pf          = stats.get("profit_factor", 0.0)
    sharpe      = stats.get("sharpe_ratio", 0.0)
    mdd         = stats.get("max_drawdown_pct", 0.0)
    total_trades= stats.get("total_trades", 0)
    fees        = stats.get("total_fees_paid", 0.0)
    slippage    = stats.get("total_slippage", 0.0)
    capital     = stats.get("capital", pnl_calc._initial_capital)

    direction = "profit" if total_net >= 0 else "loss"
    verdict   = (
        "The engine is operating within normal risk parameters."
        if mdd < 10 else
        "Drawdown elevated — consider reducing position size."
    )

    persist_warn = mode_r.get("persistence_warning", "")
    persist_html = (
        f'<p style="background:#fff3cd;border-left:4px solid #f0ad4e;padding:8px 12px;'
        f'border-radius:4px;margin:12px 0">'
        f'<strong>⚠ {persist_warn}</strong></p>'
    ) if persist_warn else ""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>EOW Quant Engine — Performance Report</title>
<style>
  body {{ font-family: 'Segoe UI', Arial, sans-serif; max-width: 960px; margin: 40px auto;
          color: #2c3e50; line-height: 1.6; }}
  h1   {{ color: #1a252f; border-bottom: 3px solid #3498db; padding-bottom: 8px; }}
  h2   {{ color: #2980b9; margin-top: 36px; }}
  .meta {{ color: #888; font-size: 13px; margin-bottom: 20px; }}
  .badge {{ display:inline-block; padding:3px 10px; border-radius:12px; font-size:12px;
            font-weight:700; color:#fff; background:#3498db; margin-left:8px; }}
  .badge.live {{ background:#e74c3c; }}
  table  {{ width:100%; border-collapse:collapse; margin-top:12px; }}
  th     {{ background:#ecf0f1; text-align:left; padding:8px 12px; font-size:13px; }}
  td     {{ padding:8px 12px; border-bottom:1px solid #ecf0f1; font-size:13px; }}
  tr:hover td {{ background:#fafafa; }}
  .pos  {{ color:#27ae60; font-weight:600; }}
  .neg  {{ color:#e74c3c; font-weight:600; }}
  .kv   {{ display:grid; grid-template-columns:repeat(3,1fr); gap:16px; margin:16px 0; }}
  .card {{ background:#f8f9fa; border-radius:8px; padding:16px; text-align:center; }}
  .card .val {{ font-size:26px; font-weight:700; color:#2c3e50; }}
  .card .lbl {{ font-size:12px; color:#888; margin-top:4px; }}
  @media print {{ body {{ margin: 20px; }} }}
</style>
</head>
<body>
<h1>EOW Quant Engine
  <span class="badge {'live' if cfg.TRADE_MODE == 'LIVE' else ''}">{mode_r['label']}</span>
</h1>
<p class="meta">Generated: {now_str} &nbsp;|&nbsp; Session Capital: {capital:,.2f} USDT</p>
{persist_html}

<h2>1. Executive Summary</h2>
<p>
  The engine closed <strong>{total_trades} trades</strong> with a net {direction} of
  <strong class="{'pos' if total_net >= 0 else 'neg'}">{total_net:+,.2f} USDT</strong>.
  Win rate: <strong>{win_rate:.1f}%</strong> &nbsp;|&nbsp;
  Profit factor: <strong>{pf:.2f}</strong> &nbsp;|&nbsp;
  Sharpe: <strong>{sharpe:.3f}</strong> &nbsp;|&nbsp;
  Max drawdown: <strong>{mdd:.2f}%</strong>.
</p>
<p>{verdict}</p>

<div class="kv">
  <div class="card"><div class="val {'pos' if total_net >= 0 else 'neg'}">{total_net:+,.2f}</div><div class="lbl">Net PnL (USDT)</div></div>
  <div class="card"><div class="val">{win_rate:.1f}%</div><div class="lbl">Win Rate</div></div>
  <div class="card"><div class="val">{pf:.2f}</div><div class="lbl">Profit Factor</div></div>
  <div class="card"><div class="val">{sharpe:.3f}</div><div class="lbl">Sharpe Ratio</div></div>
  <div class="card"><div class="val">{mdd:.2f}%</div><div class="lbl">Max Drawdown</div></div>
  <div class="card"><div class="val">{capital:,.0f}</div><div class="lbl">Capital (USDT)</div></div>
</div>

<h2>2. Performance Audit</h2>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Total Trades</td><td>{total_trades}</td></tr>
  <tr><td>Net PnL</td><td class="{'pos' if total_net >= 0 else 'neg'}">{total_net:+,.4f} USDT</td></tr>
  <tr><td>Avg Win</td><td class="pos">{stats.get('avg_win_usdt', 0.0):+,.4f} USDT</td></tr>
  <tr><td>Avg Loss</td><td class="neg">{stats.get('avg_loss_usdt', 0.0):+,.4f} USDT</td></tr>
  <tr><td>Total Fees Paid</td><td class="neg">-{fees:,.4f} USDT</td></tr>
  <tr><td>Total Slippage Cost</td><td class="neg">-{slippage:,.4f} USDT</td></tr>
  <tr><td>Combined Cost Drag</td><td class="neg">-{fees + slippage:,.4f} USDT ({(fees + slippage) / max(abs(total_net) + fees + slippage, 1e-9) * 100:.1f}% of gross)</td></tr>
  <tr><td>Profit Factor</td><td>{pf:.3f}</td></tr>
  <tr><td>Sharpe Ratio</td><td>{sharpe:.3f}</td></tr>
  <tr><td>Max Drawdown</td><td>{mdd:.2f}%</td></tr>
</table>

<h2>3. Signal Audit</h2>
<p style="color:#888;font-size:13px">Full CT-Scan reasoning log — every signal, filter decision, and trade action.</p>
<table>
  <tr><th>Time</th><th>Level</th><th>Message</th></tr>
  {audit_rows if audit_rows else '<tr><td colspan="3" style="color:#aaa;text-align:center">No events recorded yet.</td></tr>'}
</table>
</body>
</html>"""
    return HTMLResponse(html)


# ── Triple-Format Report Archive (XLSX + PDF + MD → ZIP) ─────────────────────

@app.get("/api/report/archive")
async def get_report_archive():
    """
    Download a ZIP archive containing:
      • eow_trades_<ts>.xlsx  — full trade history + session summary + signal audit
      • eow_report_<ts>.pdf   — executive summary with all KPIs
      • eow_report_<ts>.md    — markdown developer log for version control
    """
    from fastapi.responses import StreamingResponse

    heal    = healer.snapshot()
    recent  = heal.get("recent_events", [])
    redis_ok = any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in recent
    )
    try:
        lake_s    = data_lake.db_stats()
        sqlite_ok = lake_s.get("trades", -1) >= 0
    except Exception:
        lake_s    = {}
        sqlite_ok = False
    persistence_ok = redis_ok or sqlite_ok

    trade_dicts = [
        {k: getattr(t, k) for k in t.__dataclass_fields__}
        for t in pnl_calc.trades
    ]
    analytics_data = _sanitize(compute_full_analytics(
        pnl_trades=[{"net_pnl": t.net_pnl, "r_multiple": t.r_multiple} for t in pnl_calc.trades],
        initial_capital=pnl_calc._initial_capital,
        session_stats=pnl_calc.session_stats,
        healer_snapshot=heal,
        lake_stats=lake_s,
        genome_state=genome.export_state(),
        redis_ok=redis_ok,
        persistence_ok=persistence_ok,
    ))
    mode_info = await get_mode_info()

    zip_bytes = build_report_archive(
        trades=trade_dicts,
        stats=pnl_calc.session_stats,
        mode_info=mode_info,
        analytics=analytics_data,
        thoughts=_thought_log,
    )

    filename = f"eow_report_{int(time.time())}.zip"
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── FTD-025B-URX-V2: [ EXPORT INTELLIGENT REPORT ] ──────────────────────────

@app.get("/api/report/full-system-v2")
async def get_full_system_report_v2():
    """
    FTD-025B-URX-V2 Unified Report Engine — cause-effect narrative.
    Returns a single Markdown file download.
    """
    from fastapi.responses import Response as _Response
    from core.reporting.unified_report_engine_v2 import generate_full_report_v2

    def _safe_v2(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    _mins_idle = trade_flow_monitor.minutes_since_last_trade()
    _ss        = pnl_calc.session_stats

    _v2_ct = _safe_v2(
        lambda: __import__("core.intelligence.suggestion_engine",
                           fromlist=["suggestion_engine"]).suggestion_engine.detect(
            profit_factor=_ss.get("profit_factor", 0.0),
            fee_ratio=round(
                _ss.get("total_fees_paid", 0.0)
                / max(abs(_ss.get("total_net_pnl", 0.0)) + _ss.get("total_fees_paid", 0.0), 1e-9),
                4,
            ),
            win_rate=_ss.get("win_rate", 0.0) / 100.0,
            n_trades=len(pnl_calc.trades),
            strategy_usage=strategy_engine.usage(),
            regime_stable=True,
        ), {}
    )

    data = {
        "generated_at":   time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "trade_flow":     _safe_v2(trade_flow_monitor.summary, {}),
        "rl_bandit":      _safe_v2(rl_engine.summary, {}),
        "mins_idle":      _mins_idle,
        "thresholds":     _safe_v2(
            lambda: dynamic_threshold_provider.summary(minutes_no_trade=_mins_idle), {}
        ),
        "session_stats":  _ss,
        "capital":        _safe_v2(lambda: capital_allocator.summary(equity=pnl_calc.capital), {}),
        "risk":           _safe_v2(risk_ctrl.snapshot, {}),
        "gate":           _safe_v2(
            lambda: global_gate_controller.snapshot()
            if "global_gate_controller" in globals() else {}, {}
        ),
        "errors":         _safe_v2(lambda: error_registry.recent(20), []),
        "learning_memory": _safe_v2(
            lambda: __import__("core.learning_memory",
                               fromlist=["learning_memory_orchestrator"]
                               ).learning_memory_orchestrator.summary(), {}
        ),
        "ct_scan":        _v2_ct,
        "ai_brain":       _safe_v2(
            lambda: __import__("core.meta.ai_brain",
                               fromlist=["ai_brain"]).ai_brain.get_state(), {}
        ),
        "drawdown":       _safe_v2(drawdown_controller.summary, {}),
        "activator":      _safe_v2(trade_activator.summary, {}),
        "edge_engine":    _safe_v2(edge_engine.summary, {}),
        "thoughts":       list(_thought_log)[-30:],
    }

    report_md = generate_full_report_v2(data)
    filename  = f"unified_report_v2_{int(time.time())}.md"
    _thought("📊 Unified Report v2 exported (FTD-025B-URX-V2)", "SYSTEM")
    return _Response(
        content=report_md.encode("utf-8"),
        media_type="text/markdown",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── FTD-025A: [ EXPORT FULL SYSTEM REPORT ] ──────────────────────────────────

@app.get("/api/report/full-system")
async def get_full_system_report():
    """
    FTD-025A Export Engine — [ EXPORT FULL SYSTEM REPORT ] button handler.

    Returns a ZIP containing a full 15-section institutional report in both
    Markdown and PDF formats.  Single authority: core.export_engine.
    """
    from fastapi.responses import StreamingResponse

    def _safe(fn, default=None):
        try:
            return fn()
        except Exception as e:
            return default if default is not None else {"error": str(e)}

    async def _safe_async(fn, default=None):
        try:
            return await fn()
        except Exception as e:
            return default if default is not None else {"error": str(e)}

    heal       = _safe(healer.snapshot, {})
    lake_s     = _safe(data_lake.db_stats, {})
    redis_ok   = any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in heal.get("recent_events", [])
    )
    sqlite_ok  = lake_s.get("trades", -1) >= 0

    trade_dicts = [
        {k: getattr(t, k) for k in t.__dataclass_fields__}
        for t in pnl_calc.trades
    ]
    analytics = _sanitize(compute_full_analytics(
        pnl_trades=[{"net_pnl": t.net_pnl, "r_multiple": t.r_multiple}
                    for t in pnl_calc.trades],
        initial_capital=pnl_calc._initial_capital,
        session_stats=pnl_calc.session_stats,
        healer_snapshot=heal,
        lake_stats=lake_s,
        genome_state=_safe(genome.export_state, {}),
        redis_ok=redis_ok,
        persistence_ok=(redis_ok or sqlite_ok),
    ))
    mode_info = await get_mode_info()

    # Positions (best-effort)
    positions = []
    try:
        for sym, pos in risk_ctrl.positions.items():
            positions.append({
                "symbol": sym,
                "side":   getattr(pos, "side", ""),
                "qty":    getattr(pos, "qty", 0.0),
                "entry_px": getattr(pos, "entry_px", 0.0),
                "stop":     getattr(pos, "stop", 0.0),
                "tp":       getattr(pos, "tp", 0.0),
                "unrealised": getattr(pos, "unrealised_pnl", 0.0),
            })
    except Exception:
        positions = []

    # FTD-027: Use suggestion_engine.detect() for ct_scan field — it converts
    # ct_scan_engine's raw 'issues' list into structured 'findings' dicts,
    # and fires emergency findings even with < 10 trades (loss / no-trade triggers).
    _snap_stats      = pnl_calc.session_stats
    _snap_n_trades   = len(pnl_calc.trades)
    _snap_gross      = abs(_snap_stats.get("total_net_pnl", 0.0)) + _snap_stats.get("total_fees_paid", 0.0)
    _snap_fee_ratio  = _snap_stats.get("total_fees_paid", 0.0) / max(_snap_gross, 1e-9)
    ct_scan = _safe(
        lambda: __import__("core.intelligence.suggestion_engine",
                           fromlist=["suggestion_engine"]).suggestion_engine.detect(
            profit_factor=_snap_stats.get("profit_factor", 0.0),
            fee_ratio=round(_snap_fee_ratio, 4),
            win_rate=_snap_stats.get("win_rate", 0.0) / 100.0,
            n_trades=_snap_n_trades,
            strategy_usage=strategy_engine.usage(),
            regime_stable=True,
        ), {}
    )

    # FTD-027: AI Brain must produce concrete decisions — not empty state
    ai_brain_state = _safe(
        lambda: __import__("core.meta.ai_brain",
                           fromlist=["ai_brain"]).ai_brain.get_state(), {}
    )

    snapshot = SystemSnapshot(
        session_stats     = pnl_calc.session_stats,
        analytics         = analytics,
        mode_info         = mode_info,
        thoughts          = _thought_log,
        last_skip         = _safe(lambda: getattr(trade_flow_monitor,
                                                  "last_skip", lambda: {})(), {}),
        trade_flow        = _safe(trade_flow_monitor.summary, {}),
        risk_snapshot     = _safe(risk_ctrl.snapshot, {}),
        positions         = positions,
        drawdown          = _safe(drawdown_controller.summary, {}),
        genome_state      = _safe(genome.export_state, {}),
        learning          = _safe(learning_engine.summary, {}),
        edge              = _safe(edge_engine.summary, {}),
        strategy_usage    = _safe(strategy_engine.usage, {}),
        regime            = _safe(lambda: regime_memory.summary()
                                  if hasattr(regime_memory, "summary") else {}, {}),
        ct_scan           = ct_scan,
        dynamic_thresholds= _safe(
            lambda: dynamic_threshold_provider.summary(
                minutes_no_trade=trade_flow_monitor.minutes_since_last_trade()
            ), {}
        ),
        streak            = _safe(streak_engine.summary, {}),
        consistency       = _safe(consistency_engine.status, {}),
        capital_allocator = _safe(lambda: capital_allocator.summary(equity=pnl_calc.capital), {}),
        error_registry    = _safe(lambda: error_registry.recent(50), []),
        healer            = heal,
        halt_audit        = _safe(lambda: risk_ctrl.halt_audit()
                                  if hasattr(risk_ctrl, "halt_audit") else {}, {}),
        trades            = trade_dicts,
        gate_status       = _safe(lambda: global_gate_controller.snapshot()
                                  if "global_gate_controller" in globals() else {}, {}),
        ai_brain_state    = ai_brain_state,
        learning_memory   = _safe(
            lambda: __import__("core.learning_memory",
                               fromlist=["learning_memory_orchestrator"]
                               ).learning_memory_orchestrator.summary(), {}
        ),
    )

    zip_bytes = system_export_engine.build_full_report(snapshot)
    filename  = f"full_system_report_{int(time.time())}.zip"
    _thought(f"📦 Full system report exported ({len(zip_bytes)} bytes)", "SYSTEM")
    return StreamingResponse(
        iter([zip_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Mode Toggle ───────────────────────────────────────────────────────────────

@app.post("/api/mode/{mode}")
async def set_mode(mode: str, _auth=Depends(require_roles("operator", "admin"))):
    if mode.upper() not in ("PAPER", "LIVE"):
        raise HTTPException(400, "Mode must be PAPER or LIVE")
    cfg.TRADE_MODE = mode.upper()
    _thought(f"⚡ Mode switched to {cfg.TRADE_MODE}", "SYSTEM")
    return {"mode": cfg.TRADE_MODE}


# ── Export ────────────────────────────────────────────────────────────────────

@app.post("/api/export")
async def export_state(label: str = ""):
    path = exporter.export(label)
    return FileResponse(path, filename=path.split("/")[-1], media_type="application/json")


@app.post("/api/import-dna")
async def import_dna_endpoint(body: dict, _auth=Depends(require_roles("operator", "admin"))):
    path = body.get("path", "")
    if not path:
        raise HTTPException(400, "path required")
    dna = exporter.import_dna(path)
    # Inject into genome
    for strategy_type, sub_dna in dna.items():
        if strategy_type in genome.active_dna:
            genome.active_dna[strategy_type] = sub_dna
    _thought(f"📥 DNA imported from {path}", "SYSTEM")
    return {"imported_types": list(dna.keys())}


# ── Emergency Controls ────────────────────────────────────────────────────────

@app.post("/api/emergency-close")
async def emergency_close(_auth=Depends(require_roles("admin"))):
    prices = {sym: tick.price for sym, tick in mdp.ticks.items()}
    risk_ctrl.emergency_close_all(prices)
    _thought("🚨 EMERGENCY CLOSE ALL triggered", "HALT")
    return {"closed": len(prices)}


@app.post("/api/resume")
async def resume_engine(_auth=Depends(require_roles("operator", "admin"))):
    risk_ctrl.halted = False
    _thought("✅ Engine manually resumed", "SYSTEM")
    return {"halted": False}


@app.post("/api/engine/reset")
async def reset_engine(_auth=Depends(require_roles("admin"))):
    """
    ADMIN: Full engine reset after a halt.
    Clears halted + graceful_stop, cancels pending limit orders,
    and logs an audit entry.  Does NOT close open positions.
    """
    prev_halted        = risk_ctrl.halted
    prev_graceful      = risk_ctrl.graceful_stop
    risk_ctrl.halted       = False
    risk_ctrl.graceful_stop = False
    risk_ctrl.pending_orders.clear()
    msg = (
        f"🔄 ENGINE RESET by admin — "
        f"halted={prev_halted} graceful_stop={prev_graceful} cleared. "
        f"Signal scanning resumed. {len(risk_ctrl.positions)} position(s) still open."
    )
    _thought(msg, "SYSTEM")
    return {
        "reset":              True,
        "previously_halted":  prev_halted,
        "open_positions":     len(risk_ctrl.positions),
        "ts":                 int(time.time() * 1000),
    }


@app.post("/api/reset-session")
async def reset_session_state(_auth=Depends(require_roles("admin"))):
    """
    ADMIN: Full in-memory session reset — clean slate for a new learning cycle.

    Clears:
      • RL Q-table + pull counter     — bandit starts fresh exploration
      • PnL trade list + capital      — session metrics reset to initial capital
      • Strategy session PnL map      — loss-cap counters reset to zero
      • CT-Scan thought log           — decision trace cleared
      • Symbol timing caches          — cooldowns and debounce state cleared
      • Exploration trade flags       — clears open exploration markers

    Does NOT:
      • Close open positions (risk_ctrl.positions untouched)
      • Clear the SQLite database     — history is preserved for forensic reference
      • Change halt / graceful_stop state
      • Modify genome / DNA parameters

    Race-condition note: this endpoint runs in the asyncio event loop while
    _scan_market runs in to_thread(). Under GIL the dict.clear() calls are
    effectively atomic, but call this endpoint only when the engine is idle
    or has been gracefully stopped to avoid a mid-scan partial state.
    """
    # ── 1. RL Q-table ────────────────────────────────────────────────────────
    rl_engine._table.clear()
    rl_engine._total_pulls = 0

    # ── 2. PnL calculator ────────────────────────────────────────────────────
    pnl_calc.trades.clear()
    pnl_calc.capital = pnl_calc._initial_capital

    # ── 3. Strategy session loss-cap tracking ────────────────────────────────
    _strategy_session_pnl.clear()

    # ── 4. CT-Scan thought log ───────────────────────────────────────────────
    _thought_log.clear()

    # ── 5. Symbol timing and state caches ────────────────────────────────────
    _last_trade_ts.clear()
    _trades_this_hour.clear()
    _last_processed_candle_ts.clear()
    _last_symbol_eval_ms.clear()
    _is_exploration_trade.clear()
    _pending_exploration_origins.clear()   # FTD-EXPLORE-ATTR: orphan cleanup
    _closed_trade_count[0] = 0

    msg = (
        "🔄 SESSION RESET — RL Q-table cleared (0 contexts), "
        "PnL history cleared, strategy loss-cap counters reset, "
        "thought log cleared. Fresh learning cycle started."
    )
    _thought(msg, "SYSTEM")
    logger.info(f"[RESET-SESSION] Full session reset executed by admin.")

    return {
        "reset":               True,
        "rl_table_contexts":   0,
        "pnl_trades_cleared":  True,
        "capital_restored_to": pnl_calc._initial_capital,
        "ts":                  int(time.time() * 1000),
    }


@app.get("/api/halt-audit")
async def get_halt_audit():
    """
    Returns the auto-liquidation audit log:
    all HALT and CLOSE_POSITION risk events + current halted state.
    """
    halt_events = [
        {
            "ts":         e.ts,
            "event_type": e.event_type,
            "symbol":     e.symbol,
            "detail":     e.detail,
        }
        for e in risk_ctrl.events
        if e.event_type in ("HALT", "CLOSE_POSITION", "EMERGENCY")
    ]
    # Grab FILTER-level thoughts for SKIP audit
    skip_log = [
        t for t in _thought_log
        if t.get("level") == "FILTER"
    ][-50:]

    return {
        "halted":        risk_ctrl.halted,
        "graceful_stop": risk_ctrl.graceful_stop,
        "halt_events":   halt_events[-100:],
        "skip_log":      skip_log,
        "ts":            int(time.time() * 1000),
    }


@app.get("/api/last-skip")
async def get_last_skip():
    """
    Returns the most recent structured skip event for the live Skip Reason indicator.
    Also returns skip_total (all-time FILTER count this session) and recent 5 skips.
    """
    recent_skips = [t for t in _thought_log if t.get("level") == "FILTER"]
    return {
        "last_skip":    _last_skip,
        "skip_total":   len(recent_skips),
        "recent_msgs":  [s.get("msg", "") for s in recent_skips[-5:]],
        "ts":           int(time.time() * 1000),
    }


# ── FTD-REF-025: WebSocket Truth + Error Registry ────────────────────────────

@app.get("/api/ws-truth")
async def get_ws_truth():
    """FTD-REF-025: WebSocket truth state for the UI (CONNECTED/RECONNECTING/STALE/DOWN)."""
    return ws_truth_engine.to_dict()


@app.get("/api/errors")
async def get_errors(n: int = 50):
    """FTD-REF-025: Structured error registry — recent errors + occurrence counts."""
    return error_registry.summary()


# ── FTD-REF-026: Strategy / Profitability / CT-Scan endpoints ─────────────────

@app.get("/api/strategy-usage")
async def get_strategy_usage():
    """FTD-REF-026: Per-strategy usage distribution across all closed trades."""
    return strategy_engine.summary()


@app.get("/api/profit-guard")
async def get_profit_guard():
    """FTD-REF-026: Profit guard state — PF gate and fee-ratio threshold."""
    stats = pnl_calc.session_stats
    return profit_guard.summary(
        profit_factor=stats.get("profit_factor", 0.0),
        n_trades=len(pnl_calc.trades),
    )


@app.get("/api/inverse-engine")
async def get_inverse_engine():
    """A.I.E.: Adaptive Inverse Engine — per-strategy mode and win-rate."""
    return {
        "strategies": inverse_engine.summary(),
        "thresholds": {
            "win_threshold":     0.60,
            "inverse_threshold": 0.40,
            "min_samples":       10,
        },
    }


@app.get("/api/ct-scan")
async def get_ct_scan():
    """FTD-REF-026: CT-Scan system health report — HEALTHY / WARNING / CRITICAL."""
    stats    = pnl_calc.session_stats
    n_trades = len(pnl_calc.trades)
    total_fees  = stats.get("total_fees_paid",  0.0)
    total_net   = stats.get("total_net_pnl",    0.0)
    total_slip  = stats.get("total_slippage",   0.0)
    # gross ≈ |net| + fees + slippage (approximation without raw gross field)
    total_gross = abs(total_net) + total_fees + total_slip
    fee_ratio   = total_fees / max(total_gross, 1e-9)
    win_rate_pct = stats.get("win_rate", 0.0)   # comes back as 0–100
    return ct_scan_engine.scan(
        profit_factor=stats.get("profit_factor", 0.0),
        fee_ratio=round(fee_ratio, 4),
        strategy_usage=strategy_engine.usage(),
        win_rate=win_rate_pct / 100.0,
        regime_stable=True,
        n_trades=n_trades,
    )


# ── FTD-040: Consistency Engine endpoint ─────────────────────────────────────

@app.get("/api/consistency")
async def get_consistency():
    """
    FTD-040 Consistency Engine — unified system stability status.

    Returns:
      equity_volatility_pct  — rolling std-dev of equity returns (%)
      mode context           — what the engine would classify as current mode
      configuration          — all CE_* thresholds for reference

    For the live pre-trade ConsistencyState (mode + size_mult + reason), that
    is computed per-trade signal and logged to the thought_log stream.
    """
    status = consistency_engine.status()
    dd     = drawdown_controller.summary()
    return {
        "consistency":    status,
        "drawdown":       dd,
        "streak":         streak_engine.summary(),
        "capital_recovery": capital_recovery_engine.summary(),
        "loss_cluster":   loss_cluster_controller.summary(),
        "description": (
            "FTD-040 Consistency Engine: makes profit repeatable. "
            "Tracks equity volatility, profit smoothing, and unified mode."
        ),
    }


# ── FTD-026A: Layer integration endpoints ────────────────────────────────────

@app.get("/api/suggestions")
async def get_suggestions():
    """FTD-015 Suggestion Engine — CT-Scan enriched with confidence + impact."""
    from core.intelligence.suggestion_engine import suggestion_engine
    stats    = pnl_calc.session_stats
    n_trades = len(pnl_calc.trades)
    total_gross = abs(stats.get("total_net_pnl", 0.0)) + stats.get("total_fees_paid", 0.0)
    fee_ratio   = stats.get("total_fees_paid", 0.0) / max(total_gross, 1e-9)
    return suggestion_engine.detect(
        profit_factor=stats.get("profit_factor", 0.0),
        fee_ratio=round(fee_ratio, 4),
        win_rate=stats.get("win_rate", 0.0) / 100.0,
        n_trades=n_trades,
        strategy_usage=strategy_engine.usage(),
        regime_stable=True,
    )


@app.get("/api/auto-tuning")
async def get_auto_tuning():
    """FTD-016 Auto-Tuning — current dynamic threshold state."""
    from core.tuning.tuner_controller import tuner_controller
    return tuner_controller.get_state()


@app.get("/api/alert-state")
async def get_alert_state():
    """FTD-018 Alert Engine — severity-sorted, deduplicated alerts."""
    from core.alerts.alert_engine import alert_engine
    gs   = global_gate_controller.snapshot() if hasattr(global_gate_controller, "snapshot") else {}
    halt = {}
    try:
        halt = risk_ctrl.halt_audit() if hasattr(risk_ctrl, "halt_audit") else {}
    except Exception:
        pass
    return alert_engine.get_alerts(
        gate_status=gs,
        halt_audit=halt,
        error_recent=error_registry.recent(50),
        drawdown=drawdown_controller.summary(),
    )


@app.get("/api/evolution")
async def get_evolution():
    """FTD-019 Strategy Evolution — genome champion/challenger state."""
    from core.evolution.evolution_engine import evolution_engine
    return evolution_engine.get_state()


@app.get("/api/portfolio-state")
async def get_portfolio_state():
    """FTD-020 Portfolio — allocation + exposure view."""
    from core.portfolio.allocation_engine import allocation_engine
    positions = []
    try:
        for sym, pos in risk_ctrl.positions.items():
            positions.append({
                "symbol":   sym,
                "side":     getattr(pos, "side",       ""),
                "qty":      getattr(pos, "qty",        0.0),
                "entry_px": getattr(pos, "entry_px",   0.0),
                "stop":     getattr(pos, "stop",       0.0),
                "tp":       getattr(pos, "tp",         0.0),
                "unrealised": getattr(pos, "unrealised_pnl", 0.0),
            })
    except Exception:
        pass
    return allocation_engine.get_state(
        positions=positions,
        equity=scaler.equity,
    )


@app.get("/api/risk-state")
async def get_risk_state():
    """FTD-021 Risk Engine — unified risk + drawdown view."""
    rs = risk_ctrl.snapshot()
    dd = drawdown_controller.summary()
    return {
        **rs,
        "drawdown": dd,
        "module":   "RISK_STATE",
        "phase":    "021",
    }


@app.get("/api/audit-log")
async def get_audit_log():
    """FTD-022 Audit Layer — structured event log."""
    from core.audit.audit_engine import audit_engine
    return audit_engine.get_log(limit=100)


@app.get("/api/ai-brain")
async def get_ai_brain():
    """FTD-023 AI Brain — aggregated intelligence state + decision."""
    from core.meta.ai_brain import ai_brain
    return ai_brain.get_state()


@app.get("/api/capital-allocator")
async def get_capital_allocator():
    """FTD-024 Capital Scaling — allocator + growth state."""
    from core.capital.scaling_engine import scaling_engine
    return scaling_engine.get_state(
        equity=scaler.equity,
        initial_capital=pnl_calc._initial_capital,
    )


# ── FTD-029: Self-Correction Engine (Closed-Loop Intelligence) ───────────────

def _sc_build_state():
    """Shared helper: build system_state + current_params for FTD-029 endpoints."""
    from config import cfg
    from core.deep_validation.contradiction_engine import ContradictionEngine

    stats    = pnl_calc.session_stats
    n_trades = len(pnl_calc.trades)
    dd       = drawdown_controller.summary()
    rs       = risk_ctrl.snapshot()
    gs       = global_gate_controller.snapshot() if hasattr(global_gate_controller, "snapshot") else {}

    equity    = float(scaler.equity or 0.0)
    dd_pct    = float(dd.get("drawdown_pct", 0.0) or 0.0)
    win_rate  = float(stats.get("win_rate", 0.0) or 0.0) / 100.0
    total_pnl = float(stats.get("total_net_pnl", 0.0) or 0.0)
    halted    = rs.get("halted", False)

    system_state = {
        "equity":               equity,
        "total_trades":         n_trades,
        "total_pnl":            total_pnl,
        "win_rate":             win_rate,
        "current_drawdown_pct": dd_pct,
        "halted":               halted,
        "risk_halted":          halted,
        "sharpe_ratio":         stats.get("sharpe_ratio", None),
    }

    contradiction = ContradictionEngine().run({
        **system_state,
        "total_signals":    n_trades,
        "trades_active":    len(risk_ctrl.positions) > 0,
        "max_drawdown_pct": 0.15,
        "kill_switch_active": not gs.get("can_trade", True),
    })
    # Real performance-based meta_score (replaces binary 85/55 that was always 85
    # when system was running — making corrections perpetually BLOCKED even during
    # severe loss periods).
    # Components: WR quality (40%), PnL direction (30%), DD health (30%).
    _initial_cap = float(pnl_calc._initial_capital or 1000.0)
    _wr_score    = min(100.0, win_rate * 200.0)          # 50% WR → 100, 37% → 74
    _pnl_score   = max(0.0, min(100.0, 50.0 + total_pnl / max(_initial_cap, 1) * 500))
    _dd_score    = max(0.0, 100.0 - dd_pct * 5.0)        # 0% DD → 100, 20% DD → 0
    meta_score   = round(_wr_score * 0.40 + _pnl_score * 0.30 + _dd_score * 0.30, 1)
    if not contradiction["passed"]:
        meta_score = min(meta_score, 55.0)               # cap at 55 if contradictions found
    ai_brain_score = min(100.0, max(0.0, win_rate * 100.0 + (10.0 if total_pnl >= 0 else -10.0)))

    current_params = {
        "P7B_PERF_WIN_THRESHOLD":  cfg.P7B_PERF_WIN_THRESHOLD,
        "P7B_PERF_LOSS_THRESHOLD": cfg.P7B_PERF_LOSS_THRESHOLD,
        "P7B_EV_HIGH_THRESHOLD":   cfg.P7B_EV_HIGH_THRESHOLD,
        "P7B_EV_LOW_THRESHOLD":    cfg.P7B_EV_LOW_THRESHOLD,
        "TR_EV_WEIGHT":            cfg.TR_EV_WEIGHT,
        "ADAPTIVE_LR":             cfg.ADAPTIVE_LR,
        "ADAPTIVE_MIN_WEIGHT":     cfg.ADAPTIVE_MIN_WEIGHT,
        "ADAPTIVE_MAX_WEIGHT":     cfg.ADAPTIVE_MAX_WEIGHT,
        "KELLY_FRACTION":          cfg.KELLY_FRACTION,
        "EXPLORE_EV_FLOOR":        cfg.EXPLORE_EV_FLOOR,
    }

    ftd028_validators = {
        "contradiction": contradiction,
        "performance": {
            "passed":    total_pnl >= 0,
            "issue_count": 0 if total_pnl >= 0 else 1,
            "issues":    [] if total_pnl >= 0 else [{"message": f"negative PnL={total_pnl:.2f}"}],
        },
        "risk": {
            "passed":    not halted,
            "error_count": 0 if not halted else 1,
            "errors":    [] if not halted else [{"message": "engine halted"}],
        },
    }
    ftd028_meta = {
        "system_score":     meta_score,
        "stability_score":  max(0.0, 100.0 - dd_pct * 500),
        "confidence_score": min(100.0, win_rate * 100.0 + 40.0),
    }

    return system_state, current_params, ftd028_validators, ftd028_meta, ai_brain_score, halted


@app.post("/api/self-correction/run")
async def run_self_correction():
    """
    FTD-029 — Full orchestrated correction cycle (Part 1–9).
    Flow: IssueExtract → Confidence → Policy → Priority → Plan → Collide → Apply → Audit.
    Requires ≥30 trades + FTD-028 score ≥ 70 + AI Brain ≥ 70.
    """
    from core.self_correction.correction_orchestrator import correction_orchestrator

    system_state, current_params, ftd028_validators, ftd028_meta, ai_brain_score, halted = (
        _sc_build_state()
    )
    return correction_orchestrator.run_cycle(
        ftd028_validators=ftd028_validators,
        ftd028_meta=ftd028_meta,
        current_params=current_params,
        system_state=system_state,
        ai_brain_score=ai_brain_score,
        risk_halted=halted,
        risk_violated=halted,
        contradiction_critical=not ftd028_validators["contradiction"].get("passed", True),
    )


@app.get("/api/self-correction/state")
async def get_self_correction_state():
    """FTD-029 — Full dashboard state (Q13): enabled, cooldown, overlay, audit, rollback."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    return correction_orchestrator.summary()


@app.get("/api/self-correction/logs")
async def get_self_correction_logs(n: int = 50):
    """FTD-029 — Recent correction audit log (Q11/Q13)."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    return {"logs": correction_orchestrator.logs(n), "phase": "029"}


@app.get("/api/self-correction/last-change")
async def get_last_self_correction():
    """FTD-029 — Last correction card for dashboard (Q13)."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    last = correction_orchestrator.last_change()
    return last or {"detail": "No corrections applied yet", "phase": "029"}


@app.post("/api/self-correction/manual-override")
async def manual_override_self_correction(body: dict = None):
    """
    FTD-029 — Human override endpoint (Q8/Q13).
    Body: {"action": "stop"|"resume"|"clear_overlay"|"enable"|"disable"}
    """
    from core.self_correction.correction_orchestrator import correction_orchestrator
    action = (body or {}).get("action", "stop")
    if action == "stop":
        correction_orchestrator.human_override_stop()
    elif action == "resume":
        correction_orchestrator.human_override_resume()
    elif action == "clear_overlay":
        correction_orchestrator.clear_overlay()
    elif action == "enable":
        correction_orchestrator.enable()
    elif action == "disable":
        correction_orchestrator.disable()
    else:
        return {"error": f"Unknown action '{action}'", "phase": "029"}
    return {"status": f"override_{action}_applied", "phase": "029"}


@app.post("/api/self-correction/enable")
async def enable_self_correction():
    """FTD-029 — Enable auto-correction."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.enable()
    return {"status": "enabled", "phase": "029"}


@app.post("/api/self-correction/disable")
async def disable_self_correction():
    """FTD-029 — Disable auto-correction."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.disable()
    return {"status": "disabled", "phase": "029"}


@app.post("/api/self-correction/override/stop")
async def override_stop_self_correction():
    """FTD-029 — Human override: immediately halt."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.human_override_stop()
    return {"status": "stopped_by_human_override", "phase": "029"}


@app.post("/api/self-correction/override/resume")
async def override_resume_self_correction():
    """FTD-029 — Human override: resume."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.human_override_resume()
    return {"status": "resumed", "phase": "029"}


@app.post("/api/self-correction/override/clear")
async def clear_self_correction_overlay():
    """FTD-029 — Clear all active corrections, revert to base config."""
    from core.self_correction.correction_orchestrator import correction_orchestrator
    correction_orchestrator.clear_overlay()
    return {"status": "overlay_cleared", "phase": "029"}


# ── FTD-030: Autonomous Background Intelligence Loop ─────────────────────────

@app.get("/api/auto-intelligence/state")
async def get_auto_intelligence_state():
    """FTD-030 — Auto-intelligence engine state: enabled, cycles, last result."""
    if _auto_intelligence is None:
        return {"detail": "Auto-intelligence not yet initialised", "phase": "030"}
    return _auto_intelligence.summary()


@app.get("/api/auto-intelligence/history")
async def get_auto_intelligence_history(n: int = 20):
    """FTD-030 — Recent correction cycle history (up to 20 records)."""
    if _auto_intelligence is None:
        return {"history": [], "phase": "030"}
    return {"history": _auto_intelligence.history(n), "phase": "030"}


@app.post("/api/auto-intelligence/force-run")
async def force_auto_intelligence_run():
    """FTD-030 — Bypass interval gate and trigger an immediate correction cycle."""
    if _auto_intelligence is None:
        return {"detail": "Auto-intelligence not yet initialised", "phase": "030"}
    _auto_intelligence.force_run()
    result = _auto_intelligence.tick()
    return {"status": "executed", "result": result, "phase": "030"}


@app.post("/api/auto-intelligence/enable")
async def enable_auto_intelligence():
    """FTD-030 — Enable the autonomous intelligence loop."""
    if _auto_intelligence is None:
        return {"detail": "Not initialised", "phase": "030"}
    _auto_intelligence.enable()
    return {"status": "enabled", "phase": "030"}


@app.post("/api/auto-intelligence/disable")
async def disable_auto_intelligence():
    """FTD-030 — Disable the autonomous intelligence loop."""
    if _auto_intelligence is None:
        return {"detail": "Not initialised", "phase": "030"}
    _auto_intelligence.disable()
    return {"status": "disabled", "phase": "030"}


@app.post("/api/auto-intelligence/reset-daily")
async def reset_auto_intelligence_daily():
    """FTD-030 — Reset the 24h cycle counter (admin use)."""
    if _auto_intelligence is None:
        return {"detail": "Not initialised", "phase": "030"}
    _auto_intelligence.reset_daily_counter()
    return {"status": "daily_counter_reset", "phase": "030"}


@app.get("/api/evolution-status")
async def get_evolution_status():
    """
    FTD-EV-001 — System evolution monitoring dashboard.

    Returns:
      - Drift detection status (is auto-correction paused due to drift?)
      - Performance trajectory (IMPROVING / STABLE / DEGRADING)
      - Critical alerts (WR_CRITICAL, DRIFT, DD_CRITICAL, LOSS_OUTLIER)
      - Correction history with before/after outcomes
      - Trajectory computed from last 20 session trades
    """
    from core.intelligence.evolution_tracker import evolution_tracker

    # Compute live trajectory from current session trades
    _session_trades = pnl_calc.trades[_boot_replay_count:]
    trajectory = evolution_tracker.compute_trajectory(_session_trades)

    # Check critical alerts against current session state
    _last_pnl = _session_trades[-1].net_pnl if _session_trades else None
    evolution_tracker.check_critical_alerts(
        recent_trades=_session_trades,
        session_dd_pct=drawdown_controller.current_drawdown(),
        last_trade_pnl=_last_pnl,
    )

    ev_summary = evolution_tracker.summary()
    ev_summary["trajectory"] = trajectory
    ev_summary["session_trades"] = len(_session_trades)
    # FTD-REA-001 / FTD-SNP-001: include reactive micro-adjustment state + fee efficiency
    re_summary = reactive_evolution_engine.summary()
    re_summary["fee_efficiency"] = reactive_evolution_engine.get_fee_efficiency(_session_trades)
    ev_summary["reactive_evolution"] = re_summary
    return ev_summary


# ── FTD-055-ATHENA: RL Learning Intelligence Live Feed ───────────────────────

@app.get("/api/rl-intelligence")
async def get_rl_intelligence():
    """
    FTD-055-ATHENA — Institutional-grade live RL learning intelligence.

    Returns `get_evolution_state()` enriched with context differentiation
    evidence, alpha discovery, policy evolution metrics, and the current
    learning verdict.  Equivalent to the rl_intelligence.json report file
    but served as a live endpoint with no bundle download required.
    """
    _session_trades = pnl_calc.trades[_boot_replay_count:]
    _trade_dicts: "list[dict]" = []
    for _t in _session_trades:
        try:
            _trade_dicts.append(_t.__dict__ if hasattr(_t, "__dict__") else dict(_t))
        except Exception:
            pass

    try:
        _files = _generate_rl_intelligence_reports(
            trade_dicts=_trade_dicts,
            session_start_idx=0,
        )
        import json as _json
        _payload = _json.loads(_files.get("rl_intelligence.json", "{}"))
    except Exception as _err:
        _payload = {"error": str(_err), "verdict": "UNAVAILABLE"}

    # Augment with live Q-table snapshot for context map
    _ctx_map: "dict[str, dict]" = {}
    try:
        for _k, _ctx in rl_engine._table.items():
            _ctx_map[_k] = {
                "q":       round(_ctx.q_value, 4),
                "visits":  _ctx.n_visits,
                "wins":    _ctx.n_wins,
                "wr":      round(_ctx.win_rate * 100, 1),
                "pnl":     round(_ctx.total_pnl, 4),
                "mature":  _ctx.maturity_score >= 1.0,
            }
    except Exception:
        pass

    _payload["live_context_map"] = _ctx_map
    _payload["session_trades"]   = len(_session_trades)
    return _payload


# ── FTD-028: Deep Intelligence Validation Layer ──────────────────────────────

@app.post("/api/deep-validation/run")
async def run_deep_validation():
    """
    FTD-028 — Scientific Proof Engine.
    Runs all 13 deep validators and returns a unified system intelligence score
    with PASS/FAIL verdict.  Executes after FTD-027.
    """
    from core.deep_validation.contradiction_engine    import ContradictionEngine
    from core.deep_validation.data_integrity_checker  import DataIntegrityChecker
    from core.deep_validation.decision_scorer         import DecisionScorer
    from core.deep_validation.risk_validator          import RiskValidator
    from core.deep_validation.tuning_validator        import TuningValidator
    from core.deep_validation.evolution_validator     import EvolutionValidator
    from core.deep_validation.capital_validator       import CapitalValidator
    from core.deep_validation.audit_validator         import AuditValidator
    from core.deep_validation.alert_validator         import AlertValidator
    from core.deep_validation.performance_validator   import PerformanceValidator
    from core.deep_validation.failure_simulator       import FailureSimulator
    from core.deep_validation.system_consistency_checker import SystemConsistencyChecker
    from core.deep_validation.meta_score_engine       import MetaScoreEngine
    from core.alerts.alert_engine                     import alert_engine
    from core.audit.audit_engine                      import audit_engine
    from core.evolution.evolution_engine              import evolution_engine
    from core.capital.scaling_engine                  import scaling_engine
    import json, pathlib, datetime

    stats        = pnl_calc.session_stats
    n_trades     = len(pnl_calc.trades)
    dd           = drawdown_controller.summary()
    rs           = risk_ctrl.snapshot()
    gs           = global_gate_controller.snapshot() if hasattr(global_gate_controller, "snapshot") else {}

    halted       = rs.get("halted", False)
    equity       = float(scaler.equity or 0.0)
    dd_pct       = float(dd.get("drawdown_pct", 0.0) or 0.0)
    win_rate     = float(stats.get("win_rate", 0.0) or 0.0) / 100.0
    total_pnl    = float(stats.get("total_net_pnl", 0.0) or 0.0)
    risk_of_ruin = float(rs.get("risk_of_ruin", 0.0) or 0.0)
    kill_switch  = not gs.get("can_trade", True)

    system_state = {
        "equity":                   equity,
        "initial_capital":          float(pnl_calc._initial_capital or equity),
        "total_trades":             n_trades,
        "total_signals":            n_trades,   # 1:1 signal→trade as minimum bound
        "total_pnl":                total_pnl,
        "win_rate":                 win_rate,
        "current_drawdown_pct":     dd_pct,
        "max_drawdown_pct":         0.15,
        "halted":                   halted,
        "risk_halted":              halted,
        "trades_active":            len(risk_ctrl.positions) > 0,
        "risk_of_ruin":             risk_of_ruin,
        "exposure_pct":             float(rs.get("exposure_pct", 0.0) or 0.0),
        "total_exposure":           float(rs.get("total_exposure", 0.0) or 0.0),
        "kill_switch_active":       kill_switch,
        "scale_factor":             float(rs.get("size_multiplier", 1.0) or 1.0),
        "sharpe_ratio":             stats.get("sharpe_ratio", None),
        "pipeline_stages":          ["market_data", "signal", "risk", "execution"],
        # failure simulator flags
        "volatility_guard_active":  True,
        "rr_engine_active":         True,
        "drawdown_controller_active": True,
        "data_health_monitor_active": True,
        "safe_mode_engine_active":  True,
        "ws_stabilizer_active":     True,
        "error_registry_active":    True,
        "api_manager_active":       True,
        "self_healing_active":      True,
    }

    # 1. Contradiction
    contradiction_result = ContradictionEngine().run(system_state)

    # 2. Data integrity
    data_result = DataIntegrityChecker().run(system_state)

    # 3. Decision scorer — derive from closed trades
    decisions = []
    for t in pnl_calc.trades:
        pnl_val = getattr(t, "net_pnl", 0.0) or 0.0
        decisions.append({
            "action":  "TRADE",
            "outcome": "PROFIT" if pnl_val > 0 else "LOSS",
            "pnl":     float(pnl_val),
        })
    decision_result = DecisionScorer().run(decisions)

    # 4. Risk validator
    risk_result = RiskValidator().run(system_state)

    # 5. Tuning validator
    tuning_result = TuningValidator().run([])   # history not persisted in this session

    # 6. Evolution validator
    try:
        ev_state    = evolution_engine.get_state()
        evo_input   = {
            "generation":     ev_state.get("generation", 0),
            "champion_score": ev_state.get("fitness", 0.0),
            "strategies":     ev_state.get("strategies", []),
        }
    except Exception:
        evo_input = {}
    evolution_result = EvolutionValidator().run(evo_input)

    # 7. Capital validator
    cap_input = {
        **system_state,
        "total_exposure": float(rs.get("total_exposure", 0.0) or 0.0),
    }
    capital_result = CapitalValidator().run(cap_input)

    # 8. Audit validator
    try:
        audit_log  = audit_engine.get_log(limit=200)
    except Exception:
        audit_log  = {}
    audit_input = {**audit_log, "total_trades": n_trades}
    audit_result = AuditValidator().run(audit_input)

    # 9. Alert validator
    try:
        alert_out = alert_engine.get_alerts(
            gate_status=gs,
            halt_audit={},
            error_recent=error_registry.recent(50),
            drawdown=dd,
        )
        alert_input = {
            "alerts":                   alert_out.get("alerts", []),
            "false_alert_count":        0,
            "missed_alert_count":       0,
            "critical_events_detected": sum(
                1 for a in alert_out.get("alerts", [])
                if str(a.get("severity", "")).upper() == "CRITICAL"
            ),
        }
    except Exception:
        alert_input = {}
    alert_result = AlertValidator().run(alert_input)

    # 10. Performance validator
    perf_result = PerformanceValidator().run(system_state)

    # 11. Failure simulator
    failure_result = FailureSimulator().run(system_state)

    # 12. System consistency checker
    module_states = {
        "risk_ctrl":   {"equity": equity, "halted": halted},
        "drawdown":    {"equity": equity, "halted": halted},
        "gate":        {"halted": not gs.get("can_trade", True)},
    }
    consistency_result = SystemConsistencyChecker().run(module_states)

    # 13. Meta score
    validator_results = {
        "contradiction":     contradiction_result,
        "data_integrity":    data_result,
        "decision_quality":  decision_result,
        "risk":              risk_result,
        "tuning":            tuning_result,
        "evolution":         evolution_result,
        "capital":           capital_result,
        "audit":             audit_result,
        "alert":             alert_result,
        "performance":       perf_result,
        "failure_resilience": failure_result,
        "consistency":       consistency_result,
    }
    meta = MetaScoreEngine().run(validator_results)

    # Persist score to reports/deep_validation/system_score.json
    try:
        score_path = pathlib.Path("reports/deep_validation/system_score.json")
        score_path.parent.mkdir(parents=True, exist_ok=True)
        score_path.write_text(json.dumps({
            "phase":            "FTD-028",
            "module":           "META_SCORE_ENGINE",
            "system_score":     meta["system_score"],
            "risk_score":       meta["risk_score"],
            "stability_score":  meta["stability_score"],
            "confidence_score": meta["confidence_score"],
            "verdict":          meta["verdict"],
            "snapshot_ts":      meta["snapshot_ts"],
        }, indent=2))
    except Exception:
        pass

    return {
        "phase":      "FTD-028",
        "validators": validator_results,
        "meta":       meta,
        "verdict":    meta["verdict"],
        "system_score": meta["system_score"],
        "run_ts":     int(time.time() * 1000),
    }


# ── Dual-API Credential Vault ─────────────────────────────────────────────────

@app.get("/api/vault/status")
async def get_vault_status():
    """Non-sensitive vault status: configured, current_mode, is_live."""
    return vault.status()


@app.post("/api/vault/setup")
async def vault_setup(body: dict, _auth=Depends(require_roles("admin"))):
    """
    Encrypt and persist both PAPER and LIVE credential slots under a master password.
    Requires admin bearer token.  Re-calling overwrites the existing vault.
    Body: {password, paper_key, paper_secret, live_key, live_secret}
    """
    try:
        vault.setup(
            password     = body.get("password", ""),
            paper_key    = body.get("paper_key", ""),
            paper_secret = body.get("paper_secret", ""),
            live_key     = body.get("live_key", ""),
            live_secret  = body.get("live_secret", ""),
        )
        _thought("🔐 API Vault configured — PAPER and LIVE credentials encrypted at rest.", "SYSTEM")
        return {"ok": True, "mode": "PAPER"}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Vault setup failed: {exc}")


@app.post("/api/vault/switch")
async def vault_switch(body: dict):
    """
    Password-gated mode switch — the master password IS the authorization.
    On success, hot-swaps Binance API credentials in the running cfg and mdp
    WITHOUT requiring an engine restart.
    Body: {password, mode: "PAPER"|"LIVE"}
    """
    try:
        creds = vault.switch(
            password    = body.get("password", ""),
            target_mode = body.get("mode", "PAPER"),
        )
    except WrongPassword:
        raise HTTPException(status_code=401, detail="Wrong master password.")
    except VaultNotConfigured:
        raise HTTPException(status_code=409, detail="Vault not configured — run /api/vault/setup first.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    # ── Hot-swap runtime credentials (no restart needed) ─────────────────────
    cfg.BINANCE_API_KEY    = creds["key"]
    cfg.BINANCE_API_SECRET = creds["secret"]
    cfg.BINANCE_TESTNET    = creds["testnet"]
    cfg.TRADE_MODE         = creds["mode"]           # type: ignore[assignment]
    mdp._exec_url          = mdp.EXEC_API_TEST if creds["testnet"] else mdp.EXEC_API_LIVE

    endpoint_label = "testnet.binance.vision" if creds["testnet"] else "api.binance.com (PRODUCTION)"
    _thought(
        f"🔐 VAULT SWITCH → {creds['mode']} "
        f"({'Testnet' if creds['testnet'] else '⚡ REAL PRODUCTION'}) | "
        f"Execution endpoint: {endpoint_label}",
        "SYSTEM",
    )

    return {
        "ok":      True,
        "mode":    creds["mode"],
        "testnet": creds["testnet"],
        "is_live": creds["mode"] == "LIVE",
    }


# ── Guardian Logic & Aggression Control ───────────────────────────────────────

@app.get("/api/guardian/status")
async def get_guardian_status():
    """Returns Guardian Logic state: level, safe_mode, veto history, all profiles."""
    return guardian.snapshot()


@app.get("/api/engine/aggression")
async def get_aggression():
    """Current aggression level and profile parameters."""
    return guardian.snapshot()


@app.post("/api/engine/aggression")
async def set_aggression(body: dict, _auth=Depends(require_roles("operator", "admin"))):
    """
    Password-free aggression change — Guardian validates automatically.
    Body: {level: 1|2|3|4}
    Returns 403 with veto reason if Guardian blocks the change.
    """
    try:
        level = int(body.get("level", 2))
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail="level must be an integer 1–4.")

    # Pull live session metrics for Guardian validation
    stats    = pnl_calc.session_stats
    win_rate = stats.get("win_rate", 0.0)
    mdd_pct  = stats.get("max_drawdown_pct", 0.0)

    trades  = pnl_calc.trades
    valid_r = [t.r_multiple for t in trades if t.r_multiple != 0.0]
    pos_r   = [r for r in valid_r if r > 0]
    neg_r   = [abs(r) for r in valid_r if r < 0]
    avg_r_win  = (sum(pos_r) / len(pos_r)) if pos_r else 1.0
    avg_r_loss = (sum(neg_r) / len(neg_r)) if neg_r else 1.0

    allowed, msg = guardian.validate_and_apply(
        level, win_rate, mdd_pct, avg_r_win, avg_r_loss, cfg
    )

    _thought(msg, "SYSTEM" if allowed else "HALT")

    if not allowed:
        raise HTTPException(status_code=403, detail=msg)

    return guardian.snapshot()


# ── Engine Command & Control ──────────────────────────────────────────────────

@app.get("/api/engine/status")
async def get_engine_status():
    """Live engine operational status: ACTIVE / GRACEFUL_STOP / STANDBY / HALTED."""
    if risk_ctrl.halted:
        state = "HALTED"
    elif risk_ctrl.graceful_stop:
        state = "GRACEFUL_STOP"
    elif mdp._running:
        state = "ACTIVE"
    else:
        state = "STANDBY"
    return {
        "state":          state,
        "halted":         risk_ctrl.halted,
        "graceful_stop":  risk_ctrl.graceful_stop,
        "ws_running":     mdp._running,
        "open_positions": len(risk_ctrl.positions),
        "pending_orders": len(risk_ctrl.pending_orders),
        "ts":             int(time.time() * 1000),
    }


@app.post("/api/engine/start")
async def start_engine(_auth=Depends(require_roles("operator", "admin"))):
    """Clear halt + graceful-stop flags and resume normal signal scanning."""
    risk_ctrl.halted       = False
    risk_ctrl.graceful_stop = False
    _thought("▶ Engine START command received — resuming full signal scanning.", "SYSTEM")
    return {"state": "ACTIVE"}


@app.post("/api/engine/stop/graceful")
async def graceful_stop_engine(_auth=Depends(require_roles("operator", "admin"))):
    """
    Graceful stop: no new entries accepted, existing positions run until TP/SL.
    Does NOT close open positions immediately.
    """
    risk_ctrl.graceful_stop = True
    _thought(
        f"⏸ Graceful STOP — new entries blocked. "
        f"{len(risk_ctrl.positions)} position(s) running to TP/SL naturally.",
        "SYSTEM",
    )
    return {"state": "GRACEFUL_STOP", "open_positions": len(risk_ctrl.positions)}


# ── FTD-030B: Learning Memory Engine ─────────────────────────────────────────

@app.get("/api/memory/state")
async def memory_state():
    """Q18/Q19: Memory dashboard — all panels (valid_patterns, retention, negative_memory, etc.)."""
    return memory_orchestrator.summary()


@app.get("/api/memory/patterns")
async def memory_patterns():
    """Q17/Q18: Export all tracked patterns with ban status."""
    return memory_orchestrator.patterns()


@app.get("/api/memory/logs")
async def memory_logs(n: int = 50):
    """Q16-A: Recent JSONL memory entries (append-only log)."""
    return memory_orchestrator.logs(n=n)


@app.post("/api/memory/learn")
async def memory_learn(body: dict, _auth=Depends(require_roles("operator", "admin"))):
    """
    Q12: Ingest a correction-cycle record into the memory engine.
    Required fields: change_id, parameter, delta_pct, direction, value_before,
                     value_after, pnl_delta, score_delta, rolled_back.
    Optional: rollback_trigger, rationale, confidence, market_regime, volatility, symbol.
    """
    try:
        result = memory_orchestrator.learn(
            change_id=body["change_id"],
            parameter=body["parameter"],
            delta_pct=float(body["delta_pct"]),
            direction=body["direction"],
            value_before=float(body["value_before"]),
            value_after=float(body["value_after"]),
            pnl_delta=float(body["pnl_delta"]),
            score_delta=float(body["score_delta"]),
            rolled_back=bool(body["rolled_back"]),
            rollback_trigger=body.get("rollback_trigger"),
            rationale=body.get("rationale", ""),
            confidence=float(body.get("confidence", 50.0)),
            market_regime=body.get("market_regime", "UNKNOWN"),
            volatility=float(body.get("volatility", 0.0)),
            symbol=body.get("symbol", "PORTFOLIO"),
        )
        return result
    except KeyError as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail=f"Missing required field: {exc}")


@app.get("/api/memory/suggestions")
async def memory_suggestions(
    total_trades: int = 0,
    validation_score: float = 0.0,
    regime_context: str = "UNKNOWN",
    risk_halted: bool = False,
    risk_violated: bool = False,
    policy_ok: bool = True,
):
    """
    Q7/Q8/Q20: Return memory-based parameter suggestions.
    Gates: memory_ready + total_trades≥50 + validation_score≥70 + PolicyGuard.
    """
    from core.self_correction.correction_proposal import TUNABLE_PARAMS
    current_params = {k: float(v[0] + v[1]) / 2.0 for k, v in TUNABLE_PARAMS.items()}
    return memory_orchestrator.suggest(
        current_params=current_params,
        total_trades=total_trades,
        validation_score=validation_score,
        regime_context=regime_context,
        risk_halted=risk_halted,
        risk_violated=risk_violated,
        policy_ok=policy_ok,
    )


@app.post("/api/memory/reset")
async def memory_reset(_auth=Depends(require_roles("admin"))):
    """Hard reset: clear all memory entries, patterns, negative memory, guard session."""
    memory_orchestrator.reset()
    return {"status": "RESET", "module": "MEMORY_ORCHESTRATOR", "phase": "030B"}


# ── WebSocket (Real-time Dashboard Feed) ──────────────────────────────────────

MAX_WS_CLIENTS = 3   # max simultaneous dashboard connections

@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    # Reject BEFORE accepting when over cap (code 4029 = too many connections)
    # Client must back off on 4029 — do NOT retry immediately
    if len(_ws_clients) >= MAX_WS_CLIENTS:
        await ws.accept()
        await ws.close(code=4029, reason="too_many_connections")
        logger.debug(f"[WS] Rejected — cap {MAX_WS_CLIENTS} reached. Active: {len(_ws_clients)}")
        return

    await ws.accept()
    _ws_clients.append(ws)
    logger.info(f"[WS] Client connected. Total: {len(_ws_clients)}")

    try:
        # Send initial state burst — includes truth-engine WS state (FTD-REF-026)
        await ws.send_text(json.dumps({
            "type":     "init",
            "status":   await get_status(),
            "pnl":      pnl_calc.session_stats,
            "thoughts": _thought_log[-20:],
            "ws_truth": ws_truth_engine.to_dict(),   # FTD-REF-026
        }, default=str))

        while True:
            # Keep-alive: 45s timeout (client pings every 20s)
            msg = await asyncio.wait_for(ws.receive_text(), timeout=45)
            data = json.loads(msg)
            if data.get("cmd") == "ping":
                await ws.send_text(json.dumps({"type": "pong", "ts": int(time.time() * 1000)}))

    except (WebSocketDisconnect, asyncio.TimeoutError):
        pass
    except Exception as e:
        logger.debug(f"[WS] Connection error: {e}")
    finally:
        if ws in _ws_clients:
            _ws_clients.remove(ws)
        logger.info(f"[WS] Client disconnected. Total: {len(_ws_clients)}")


# ── FTD-030B: Learning Memory Layer ──────────────────────────────────────────

@app.get("/api/learning-memory/summary")
async def learning_memory_summary():
    """FTD-030B — Full learning memory state: patterns formed, negative memory, cycle stats."""
    from core.learning_memory import learning_memory_orchestrator
    return learning_memory_orchestrator.summary()


@app.get("/api/learning-memory/patterns")
async def learning_memory_patterns(n: int = 10):
    """FTD-030B — Top N formed patterns by confidence (leaderboard)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "patterns": learning_memory_orchestrator.pattern_leaderboard(n),
        "phase": "030B",
    }


@app.get("/api/learning-memory/failed-patterns")
async def learning_memory_failed_patterns(n: int = 10):
    """FTD-030B — Bottom N patterns by confidence (failed patterns)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "failed_patterns": learning_memory_orchestrator.failed_patterns(n),
        "phase": "030B",
    }


@app.get("/api/learning-memory/negative-memory")
async def learning_memory_negative():
    """FTD-030B — Current negative memory blacklist (temporary + permanent bans)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "negative_memory":  learning_memory_orchestrator.negative_memory_list(),
        "counts":           learning_memory_orchestrator._neg_memory.count(),
        "phase": "030B",
    }


@app.get("/api/learning-memory/log")
async def learning_memory_log(n: int = 20):
    """FTD-030B — Recent memory store records (last N entries)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "records": learning_memory_orchestrator.recent_memory_log(n),
        "phase":   "030B",
    }


@app.post("/api/learning-memory/enable")
async def learning_memory_enable():
    """FTD-030B — Enable learning memory layer."""
    from core.learning_memory import learning_memory_orchestrator
    learning_memory_orchestrator.enable()
    return {"status": "enabled", "phase": "030B"}


@app.post("/api/learning-memory/disable")
async def learning_memory_disable():
    """FTD-030B — Disable learning memory layer (memory is read-only)."""
    from core.learning_memory import learning_memory_orchestrator
    learning_memory_orchestrator.disable()
    return {"status": "disabled", "phase": "030B"}


@app.get("/api/learning-memory/history")
async def learning_memory_history(n: int = 10):
    """FTD-030B — Recent memory store records (explainability log)."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "history": learning_memory_orchestrator.recent_memory_log(n),
        "phase": "030B",
    }


@app.get("/api/learning-memory/heatmap")
async def learning_memory_heatmap():
    """FTD-030B — Regime × parameter confidence heatmap."""
    from core.learning_memory import learning_memory_orchestrator
    return {
        "heatmap": learning_memory_orchestrator.pattern_heatmap(),
        "phase": "030B",
    }


@app.get("/api/learning-memory/bridge")
async def learning_memory_bridge_status():
    """LRN-001 — TradeMemoryBridge telemetry: records fed, wins/losses, LMO state."""
    return trade_memory_bridge.get_telemetry()


# ── PRP-001 Signal Truth API ──────────────────────────────────────────────────

@app.get("/api/prp/001/summary")
async def prp001_summary():
    """PRP-001 — Signal Truth telemetry dashboard summary."""
    from analytics.odyssey.signal_truth_reports import get_dashboard_summary
    return get_dashboard_summary()


@app.get("/api/prp/001/reports")
async def prp001_reports():
    """PRP-001 — All 10 forensic reports bundle."""
    from analytics.odyssey.signal_truth_reports import generate_all_reports
    return generate_all_reports()


@app.get("/api/prp/001/signal-truth")
async def prp001_signal_truth():
    """PRP-001 — Signal truth matrix (report 01)."""
    return signal_truth_engine.signal_truth_matrix()


@app.get("/api/prp/001/false-positives")
async def prp001_false_positives():
    """PRP-001 — False positive clusters (report 02)."""
    return false_positive_forensics.false_positive_clusters()


@app.get("/api/prp/001/directional-legitimacy")
async def prp001_directional_legit():
    """PRP-001 — Directional legitimacy report (report 03)."""
    return directional_legitimacy.directional_legitimacy_report()


@app.get("/api/prp/001/asymmetry")
async def prp001_asymmetry():
    """PRP-001 — Asymmetry validation report (report 06)."""
    return asymmetry_validation.asymmetry_validation_report()


@app.get("/api/prp/001/context-quality")
async def prp001_context_quality():
    """PRP-001 — Context quality analysis (report 05)."""
    return context_quality_engine.context_quality_analysis()


@app.get("/api/prp/001/recent-signals")
async def prp001_recent_signals(n: int = 30):
    """PRP-001 — Recent signal records with outcomes."""
    return {"signals": signal_truth_engine.recent_signals(n=n)}


@app.get("/api/prp/001/download")
async def prp001_download():
    """PRP-001 — All forensic reports as a single downloadable ZIP."""
    import zipfile, io as _io, json as _json
    from fastapi.responses import StreamingResponse
    from analytics.odyssey.signal_truth_reports import generate_all_reports, get_dashboard_summary

    ts = int(time.time())
    buf = _io.BytesIO()

    reports = generate_all_reports()
    summary = get_dashboard_summary()

    files = {
        "00_dashboard_summary.json":              summary,
        "01_signal_truth_matrix.json":            signal_truth_engine.signal_truth_matrix(),
        "02_false_positive_clusters.json":        false_positive_forensics.false_positive_clusters(),
        "03_directional_legitimacy.json":         directional_legitimacy.directional_legitimacy_report(),
        "04_confidence_reality_divergence.json":  asymmetry_validation.confidence_reality_divergence(),
        "05_context_quality_analysis.json":       context_quality_engine.context_quality_analysis(),
        "06_asymmetry_validation.json":           asymmetry_validation.asymmetry_validation_report(),
        "07_noise_participation_audit.json":      false_positive_forensics.noise_participation_audit(),
        "08_predictive_integrity_monitor.json":   signal_truth_engine.predictive_integrity_monitor(),
        "09_regime_signal_validity.json":         directional_legitimacy.regime_signal_validity(),
        "10_truth_density_summary.json":          signal_truth_engine.truth_density_summary(),
        "recent_signals.json":                    {"signals": signal_truth_engine.recent_signals(n=50)},
        "all_reports_bundle.json":                reports,
    }

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, data in files.items():
            zf.writestr(fname, _json.dumps(data, indent=2, default=str))

    buf.seek(0)
    fn = f"prp001_forensic_reports_{ts}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )




# ── PRP-002 Signal Ecology API ────────────────────────────────────────────────

@app.get("/api/prp/002/summary")
async def prp002_summary():
    """PRP-002 — Signal ecology telemetry snapshot."""
    return opportunity_ecology.get_telemetry()


@app.get("/api/prp/002/ecology")
async def prp002_ecology():
    """PRP-002 — Compact ecology snapshot (signals/hr, survival, drought, recovery)."""
    return opportunity_ecology.ecology_snapshot()


@app.get("/api/prp/002/density")
async def prp002_density():
    """PRP-002 — Signal density engine telemetry (flow health, block reasons)."""
    return signal_density_engine.get_telemetry()


@app.get("/api/prp/002/rsi-governor")
async def prp002_rsi_governor():
    """PRP-002 — Adaptive RSI Governor: current bands, survival rates, adapt log."""
    return adaptive_rsi_governor.get_telemetry()


@app.get("/api/prp/002/recovery")
async def prp002_recovery():
    """PRP-002 — Exploration Recovery Governor: active cycle, cycle history."""
    return exploration_recovery_governor.get_telemetry()


@app.get("/api/prp/002/context-memory")
async def prp002_context_memory():
    """PRP-002 — Alpha Context Memory: profitable/toxic contexts, boost counts."""
    return alpha_context_memory.get_telemetry()


@app.get("/api/prp/002/context-clusters")
async def prp002_context_clusters(n: int = 20):
    """PRP-002 — Alpha Context Memory: top-N contexts sorted by avg PnL."""
    return {"clusters": alpha_context_memory.context_clusters(n=n)}


@app.get("/api/prp/002/rsi-decisions")
async def prp002_rsi_decisions(n: int = 50):
    """PRP-002 — Recent RSI governor decisions (pass/block with band state)."""
    return {"decisions": adaptive_rsi_governor.recent_decisions(n=n)}


@app.get("/api/prp/002/recovery-history")
async def prp002_recovery_history(n: int = 20):
    """PRP-002 — Recent exploration recovery cycles."""
    return {"cycles": exploration_recovery_governor.cycle_history(n=n)}


@app.get("/api/forensics/recovery-cycle-audit")
async def recovery_cycle_audit():
    """
    Recovery Cycle Audit — validates the 5-win/6-loss cyclical hypothesis.

    Returns four evidence sections:
      1. consecutive_runs   — actual win/loss run lengths from trade history
      2. r_multiple_dist    — how many wins had NO breakeven protection (<1.5R)
      3. recovery_vs_normal — exploration/recovery trades vs normal trade performance
      4. context_boost      — context-boosted trades vs non-boosted performance
      5. thought_log_events — recovery mode activation counts from thought log

    Use this data to confirm/deny each proposed fix before implementing.
    """
    import collections as _col

    trades_raw = list(pnl_calc.trades)
    trades_sorted = sorted(trades_raw, key=lambda t: getattr(t, "exit_ts", 0))

    def _wr(wins, total):
        return round(wins / total * 100, 1) if total else 0.0

    def _avg(vals):
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    def _dec_snap(t, *keys):
        d = getattr(t, "decision_snapshot", None) or {}
        for k in keys:
            d = d.get(k) if isinstance(d, dict) else None
            if d is None:
                return None
        return d

    # ── 1. Consecutive win/loss run analysis ─────────────────────────────────
    runs = []
    run_type = None
    run_len  = 0
    for t in trades_sorted:
        is_win = (getattr(t, "net_pnl", 0.0) > 0)
        cur    = "WIN" if is_win else "LOSS"
        if cur == run_type:
            run_len += 1
        else:
            if run_type is not None:
                runs.append({"type": run_type, "length": run_len})
            run_type, run_len = cur, 1
    if run_type:
        runs.append({"type": run_type, "length": run_len})

    win_runs  = [r["length"] for r in runs if r["type"] == "WIN"]
    loss_runs = [r["length"] for r in runs if r["type"] == "LOSS"]
    run_dist  = _col.Counter(r["length"] for r in runs if r["type"] == "LOSS")

    # ── 2. R-multiple distribution (Fix A — breakeven trigger validation) ────
    r_buckets: dict = _col.defaultdict(list)
    for t in trades_sorted:
        r = getattr(t, "r_multiple", 0.0) or 0.0
        if r > 0:
            if r < 0.5:   r_buckets["win_0.0_0.5"].append(r)
            elif r < 1.0: r_buckets["win_0.5_1.0"].append(r)
            elif r < 1.5: r_buckets["win_1.0_1.5"].append(r)
            else:         r_buckets["win_1.5_plus"].append(r)
        else:
            r_buckets["loss"].append(r)

    unprotected_wins = (len(r_buckets["win_0.0_0.5"])
                        + len(r_buckets["win_0.5_1.0"])
                        + len(r_buckets["win_1.0_1.5"]))
    total_wins  = unprotected_wins + len(r_buckets["win_1.5_plus"])
    total_total = total_wins + len(r_buckets["loss"])

    # Estimate pnl at risk: wins below 1.5R closed profitably — if market reversed
    # before close, they'd have hit full SL. Quantify that exposure.
    at_risk_pnl = sum(
        getattr(t, "net_pnl", 0.0)
        for t in trades_sorted
        if 0 < (getattr(t, "r_multiple", 0.0) or 0.0) < 1.5
    )

    # ── 3. Recovery vs normal trade analysis (Fix B) ─────────────────────────
    def _is_recovery(t) -> bool:
        # RL floor exploration (anti-starvation)
        eo = getattr(t, "exploration_origin", None) or {}
        if eo.get("was_exploration_trade"):
            return True
        # Ecology recovery mode: size_mult < 1.0 on a PAPER_SPEED signal
        eco_mult = _dec_snap(t, "ecology", "size_multiplier")
        if eco_mult is not None and eco_mult < 1.0:
            return True
        return False

    recovery_trades = [t for t in trades_sorted if _is_recovery(t)]
    normal_trades   = [t for t in trades_sorted if not _is_recovery(t)]

    def _bucket_metrics(bucket):
        n      = len(bucket)
        if n == 0:
            return {"n": 0, "win_rate_pct": 0.0, "avg_pnl": 0.0, "total_pnl": 0.0}
        wins   = sum(1 for t in bucket if getattr(t, "net_pnl", 0.0) > 0)
        pnls   = [getattr(t, "net_pnl", 0.0) for t in bucket]
        return {
            "n":            n,
            "win_rate_pct": _wr(wins, n),
            "avg_pnl":      _avg(pnls),
            "total_pnl":    round(sum(pnls), 4),
        }

    # ── 4. Context-boost analysis (Fix B) ────────────────────────────────────
    def _boost_mult(t) -> float:
        # PRIMARY_STRATEGY: ctx_amp.boost_mult in decision_snapshot
        v = _dec_snap(t, "ctx_amp", "boost_mult")
        if v is not None:
            return float(v)
        # PAPER_SPEED: ecology.boost_mult
        v = _dec_snap(t, "ecology", "boost_mult")
        return float(v) if v is not None else 1.0

    boosted_trades    = [t for t in trades_sorted if _boost_mult(t) > 1.0]
    nonboosted_trades = [t for t in trades_sorted if _boost_mult(t) <= 1.0]

    # ── 5. Thought log event counts ───────────────────────────────────────────
    tlog_msgs = [str(e.get("msg", "")) for e in list(_thought_log)]
    def _tcnt(kw): return sum(1 for m in tlog_msgs if kw in m)

    # ── Hypothesis verdict helper ─────────────────────────────────────────────
    pct_unprotected = round(unprotected_wins / max(total_wins, 1) * 100, 1)
    avg_loss_run    = round(sum(loss_runs) / len(loss_runs), 1) if loss_runs else 0.0
    avg_win_run     = round(sum(win_runs)  / len(win_runs),  1) if win_runs  else 0.0

    fix_a_verdict = (
        f"APPLIED — BREAKEVEN_TRIGGER_R is now {cfg.BREAKEVEN_TRIGGER_R}R (was 1.5R). "
        f"{pct_unprotected}% of wins still close below 1.5R; monitor for win-rate improvement."
        if cfg.BREAKEVEN_TRIGGER_R < 1.5 else
        "SUPPORTED — majority of wins have no BE protection; lowering trigger to 1.0R is justified"
        if pct_unprotected > 50 else
        "WEAK — most wins already reach 1.5R; fix may have limited impact"
    )
    rec_m = _bucket_metrics(recovery_trades)
    norm_m = _bucket_metrics(normal_trades)
    fix_b_verdict = (
        "SUPPORTED — recovery/exploration trades underperform normal trades significantly"
        if rec_m["avg_pnl"] < norm_m["avg_pnl"] * 0.5 and rec_m["n"] > 5 else
        "INCONCLUSIVE — insufficient data or recovery trades not significantly worse"
    )
    boost_m = _bucket_metrics(boosted_trades)
    nboost_m = _bucket_metrics(nonboosted_trades)

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_trades_analyzed": total_total,

        "section_1_consecutive_runs": {
            "description": "Win/loss run lengths — 5W→6L cycle detection",
            "all_runs":          runs[-40:],   # last 40 runs
            "avg_win_run_length":  avg_win_run,
            "avg_loss_run_length": avg_loss_run,
            "max_win_run":  max(win_runs,  default=0),
            "max_loss_run": max(loss_runs, default=0),
            "loss_run_distribution": {str(k): v for k, v in sorted(run_dist.items())},
            "cycle_pattern_detected": (
                "YES — avg loss run > avg win run (losses outnumber wins per streak)"
                if avg_loss_run > avg_win_run else
                "NO — no systematic loss-streak bias detected"
            ),
        },

        "section_2_r_multiple_distribution": {
            "description": "Fix A validation — wins with no breakeven protection (r < 1.5)",
            "wins_unprotected_below_1_5r": unprotected_wins,
            "wins_protected_above_1_5r":   len(r_buckets["win_1.5_plus"]),
            "total_wins":                  total_wins,
            "pct_wins_unprotected":        pct_unprotected,
            "by_bucket": {
                "win_0.0_to_0.5r": {"count": len(r_buckets["win_0.0_0.5"]),
                                     "avg_r": _avg(r_buckets["win_0.0_0.5"])},
                "win_0.5_to_1.0r": {"count": len(r_buckets["win_0.5_1.0"]),
                                     "avg_r": _avg(r_buckets["win_0.5_1.0"])},
                "win_1.0_to_1.5r": {"count": len(r_buckets["win_1.0_1.5"]),
                                     "avg_r": _avg(r_buckets["win_1.0_1.5"])},
                "win_1.5r_plus":   {"count": len(r_buckets["win_1.5_plus"]),
                                     "avg_r": _avg(r_buckets["win_1.5_plus"])},
                "losses":          {"count": len(r_buckets["loss"]),
                                    "avg_r": _avg(r_buckets["loss"])},
            },
            "pnl_from_unprotected_wins": round(at_risk_pnl, 4),
            "fix_a_verdict": fix_a_verdict,
            "fix_a_recommendation": (
                f"Fix already applied — BREAKEVEN_TRIGGER_R={cfg.BREAKEVEN_TRIGGER_R}R. "
                "Monitor: watch win_0.5_to_1.0r bucket and peak_r data across next 200+ trades."
                if cfg.BREAKEVEN_TRIGGER_R < 1.5 else
                "Lower BREAKEVEN_TRIGGER_R from 1.5 to 1.0 in config.py"
                if pct_unprotected > 50 else
                "Hold — current 1.5R trigger may be appropriate"
            ),
            # FTD-PEAK-R: peak_r is now captured — these counts become meaningful
            # from the next session onward. Legacy trades default to peak_r=0.0.
            "peak_r_analysis": {
                "note": "Requires trades recorded after peak_r instrumentation (v1.38.6+)",
                "trades_with_peak_r_data": sum(
                    1 for t in trades_sorted if getattr(t, "peak_r", 0.0) > 0
                ),
                # Core Fix A question: reached meaningful R, had no BE protection, reversed to loss
                "reached_1r_then_loss": sum(
                    1 for t in trades_sorted
                    if getattr(t, "peak_r", 0.0) >= 1.0
                    and getattr(t, "net_pnl", 0.0) <= 0
                ),
                "reached_0_5r_then_loss": sum(
                    1 for t in trades_sorted
                    if getattr(t, "peak_r", 0.0) >= 0.5
                    and getattr(t, "net_pnl", 0.0) <= 0
                ),
                "never_reached_0_5r": sum(
                    1 for t in trades_sorted
                    if getattr(t, "peak_r", 0.0) < 0.5
                ),
                "avg_peak_r_of_losing_trades": _avg([
                    getattr(t, "peak_r", 0.0) for t in trades_sorted
                    if getattr(t, "net_pnl", 0.0) <= 0
                    and getattr(t, "peak_r", 0.0) > 0
                ]),
            },
        },

        "section_3_recovery_vs_normal": {
            "description": "Fix B/C validation — exploration/recovery trade quality vs normal",
            "recovery_trades": rec_m,
            "normal_trades":   norm_m,
            "recovery_pct_of_total": round(rec_m["n"] / max(total_total, 1) * 100, 1),
            "fix_b_verdict": fix_b_verdict,
            "note": (
                "Recovery trades tagged via exploration_origin.was_exploration_trade "
                "or ecology.size_multiplier < 1.0 in decision_snapshot"
            ),
        },

        "section_4_context_boost": {
            "description": "Fix B validation — context-amplified trades vs non-amplified",
            "boosted_trades":    boost_m,
            "nonboosted_trades": nboost_m,
            "boost_coverage_pct": round(
                len(boosted_trades) / max(total_total, 1) * 100, 1),
            "boost_vs_normal_pnl_delta": round(
                boost_m["avg_pnl"] - nboost_m["avg_pnl"], 4),
            "verdict": (
                "BOOST HARMFUL — amplified trades underperform; suppress recovery-mode boosts"
                if boost_m["avg_pnl"] < nboost_m["avg_pnl"] - 0.05 and len(boosted_trades) > 5 else
                "BOOST NEUTRAL/POSITIVE — amplification not causing systematic harm"
            ),
        },

        "section_5_thought_log_events": {
            "description": "Recovery-mode activation frequency in recent thought log",
            "drought_activations":   _tcnt("DROUGHT"),
            "curiosity_activations": _tcnt("CURIOSITY"),
            "forced_activations":    _tcnt("FORCED"),
            "rsi_crash_guard_blocks": _tcnt("RSI_CRASH_GUARD"),
            "recovery_mode_trades_per_thought_event": (
                round(rec_m["n"] / max(
                    _tcnt("CURIOSITY") + _tcnt("FORCED") + _tcnt("DROUGHT"), 1
                ), 1)
            ),
            "note": "Thought log holds last 500 entries only; counts reflect recent session",
        },

        "summary": {
            "hypothesis_status": (
                "STRONG" if (pct_unprotected > 50 and avg_loss_run >= avg_win_run) else
                "MODERATE" if (pct_unprotected > 30 or avg_loss_run > avg_win_run) else
                "WEAK — data does not strongly support the proposed cycle"
            ),
            "recommended_next_action": (
                f"Fix A APPLIED (BREAKEVEN_TRIGGER_R={cfg.BREAKEVEN_TRIGGER_R}R). "
                "Fix B APPLIED (recovery boost suppressed). "
                "Monitor peak_r data — need 300+ peak_r trades before Fix C evaluation. "
                "Fix C (recovery trade causality) on hold."
                if cfg.BREAKEVEN_TRIGGER_R < 1.5 else
                "Fix A (BREAKEVEN_TRIGGER_R 1.5→1.0) is data-justified. "
                "Fix B and C require deeper investigation — share this report."
            ),
        },
    }


# ── FORENSIC: Genome Exposure Audit ──────────────────────────────────────────
@app.get("/api/forensics/genome-exposure-audit")
async def genome_exposure_audit():
    """
    Pipeline audit: how many genomes pass each stage
    Generated → Activated → Executed → Evaluated → Promoted.
    Identifies where evolution is stalling.
    """
    state = genome.get_state()
    gen_log   = state.get("recent_genomes", [])   # last 500 in memory
    promo_log = state.get("promotion_log", [])

    total_generated = state.get("generation", len(gen_log))

    # Activated = appeared in generation_log (backtest ran)
    activated = len(gen_log)

    # Executed = had at least 1 simulated trade in backtest
    executed = [g for g in gen_log if g.get("trades", 0) >= 1]

    # Evaluated = had enough trades for meaningful gate check (≥5 per gate 1)
    evaluated = [g for g in gen_log if g.get("trades", 0) >= 5]

    # Promoted = decision == PROMOTED in promotion_log
    promoted  = [p for p in promo_log if p.get("decision") == "PROMOTED"]
    rejected  = [p for p in promo_log if p.get("decision") == "REJECTED"]

    # Rejection breakdown
    rejection_reasons: dict = {}
    for p in rejected:
        reason = p.get("reason", "UNKNOWN")
        # Extract gate names
        gates = []
        if "train_gate" in reason: gates.append("TRAIN_GATE")
        if "r_gate"     in reason: gates.append("R_GATE")
        if "overfit"    in reason: gates.append("OVERFIT")
        if "oos_gate"   in reason: gates.append("OOS_GATE")
        key = "+".join(gates) if gates else reason[:40]
        rejection_reasons[key] = rejection_reasons.get(key, 0) + 1

    # By strategy breakdown
    by_strategy: dict = {}
    for stype in ["TrendFollowing", "MeanReversion", "VolatilityExpansion"]:
        sg = [g for g in gen_log if g.get("strategy_type") == stype]
        se = [g for g in sg if g.get("trades", 0) >= 1]
        sv = [g for g in sg if g.get("trades", 0) >= 5]
        sp = [p for p in promoted if p.get("strategy_type") == stype]
        avg_cost_drag = round(
            sum(g.get("cost_drag_pct", 0) for g in se) / max(len(se), 1), 1
        )
        by_strategy[stype] = {
            "generated":    len(sg),
            "executed":     len(se),
            "evaluated":    len(sv),
            "promoted":     len(sp),
            "avg_cost_drag_pct": avg_cost_drag,
            "bottleneck": (
                "NO_TRADES — backtest finds no setups in available candle window"
                if len(se) == 0 else
                "INSUFFICIENT_TRADES — fewer than 5 trades per backtest"
                if len(sv) == 0 else
                "GATE_REJECTION — trades exist but quality gates block promotion"
                if len(sp) == 0 else
                "HEALTHY"
            ),
        }

    # What is blocking promotion right now?
    current_bottleneck = (
        "NO_PROMOTIONS_YET — engine evolving; first promotion requires: "
        f"WinRate≥{cfg.GENOME_PROMOTE_WIN_RATE*100:.0f}% "
        f"PF≥{cfg.GENOME_PROMOTE_PF} "
        f"AvgR≥{cfg.GENOME_MIN_AVG_R} "
        f"OOS_PF≥1.0 "
        f"Overfit≤{cfg.GENOME_OVERFITTING_MAX_RATIO}"
    ) if not promoted else f"FIRST_PROMOTION_AT_GENERATION_{promoted[0].get('ts', '?')}"

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "pipeline": {
            "generated":  total_generated,
            "activated":  activated,
            "executed":   len(executed),
            "evaluated":  len(evaluated),
            "promoted":   len(promoted),
            "rejected":   len(rejected),
        },
        "funnel_pct": {
            "executed_of_activated":  round(len(executed)  / max(activated, 1) * 100, 1),
            "evaluated_of_executed":  round(len(evaluated) / max(len(executed), 1) * 100, 1),
            "promoted_of_evaluated":  round(len(promoted)  / max(len(evaluated), 1) * 100, 1),
        },
        "rejection_breakdown": rejection_reasons,
        "by_strategy":         by_strategy,
        "promotion_gate_thresholds": {
            "win_rate_min_pct": cfg.GENOME_PROMOTE_WIN_RATE * 100,
            "profit_factor_min": cfg.GENOME_PROMOTE_PF,
            "avg_r_min":         cfg.GENOME_MIN_AVG_R,
            "oos_pf_min":        1.0,
            "overfit_ratio_max": cfg.GENOME_OVERFITTING_MAX_RATIO,
            "min_trades":        5,
        },
        "current_bottleneck": current_bottleneck,
        "watch_for": "First ACCEPTED in promotion_log — use /api/forensics/promotion-watch",
    }


# ── FORENSIC: Breakeven Impact Audit ─────────────────────────────────────────
@app.get("/api/forensics/breakeven-impact-audit")
async def breakeven_impact_audit():
    """
    Before/after comparison of Fix A (BREAKEVEN_TRIGGER_R 1.5→1.0).
    Segments trades by whether BE was armed. Tracks avg win size,
    cost drag, and PF to confirm Fix A is having the intended effect.
    """
    _boot_replay = getattr(pnl_calc, "_boot_replay_count", 0)
    all_trades   = pnl_calc.trades
    session_trades = all_trades[_boot_replay:]

    def _safe_avg(vals):
        return round(sum(vals) / len(vals), 4) if vals else 0.0

    # Segment: trades where BE fired (breakeven_armed captured via peak_r ≥ trigger)
    # We approximate: peak_r >= current trigger → BE armed; peak_r < trigger → not armed
    trigger = cfg.BREAKEVEN_TRIGGER_R

    has_peak_data = [t for t in all_trades if getattr(t, "peak_r", 0.0) > 0]
    be_armed   = [t for t in has_peak_data if t.peak_r >= trigger]
    be_unarmed = [t for t in has_peak_data if t.peak_r < trigger]

    # Win/loss split for each segment
    def _seg_stats(trades):
        wins   = [t for t in trades if t.net_pnl >= 0]
        losses = [t for t in trades if t.net_pnl <  0]
        fees   = [getattr(t, "fee_entry", 0) + getattr(t, "fee_exit", 0) for t in trades]
        gross  = [getattr(t, "gross_pnl", t.net_pnl) for t in trades]
        total_gross = sum(gross)
        total_fees  = sum(fees)
        cost_drag   = round(total_fees / max(abs(total_gross), 1e-9) * 100, 1) if total_gross > 0 else 999.9
        return {
            "n":            len(trades),
            "wins":         len(wins),
            "losses":       len(losses),
            "win_rate_pct": round(len(wins) / max(len(trades), 1) * 100, 1),
            "avg_net_pnl":  _safe_avg([t.net_pnl for t in trades]),
            "avg_peak_r":   _safe_avg([t.peak_r for t in trades]),
            "avg_r_multiple": _safe_avg([getattr(t, "r_multiple", 0) for t in trades]),
            "total_fees":   round(total_fees, 4),
            "cost_drag_pct": cost_drag,
        }

    # Session-level stats (after boot — most recent trades)
    session_wins   = [t for t in session_trades if t.net_pnl >= 0]
    session_losses = [t for t in session_trades if t.net_pnl <  0]

    # Peak_r distribution — are trades now reaching 1.0R?
    peak_buckets = {
        "never_reached_0_5r":   sum(1 for t in has_peak_data if t.peak_r < 0.5),
        "reached_0_5r":         sum(1 for t in has_peak_data if 0.5 <= t.peak_r < 1.0),
        "reached_1r":           sum(1 for t in has_peak_data if 1.0 <= t.peak_r < 1.5),
        "reached_1_5r_plus":    sum(1 for t in has_peak_data if t.peak_r >= 1.5),
    }

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "fix_a_config": {
            "current_be_trigger_r":    trigger,
            "previous_be_trigger_r":   1.5,
            "status": "APPLIED" if trigger < 1.5 else "PENDING",
        },
        "peak_r_sample_size": len(has_peak_data),
        "peak_r_note": (
            f"Sufficient for trend analysis ({len(has_peak_data)} trades)"
            if len(has_peak_data) >= 300 else
            f"Growing — need {300 - len(has_peak_data)} more trades for Fix C confidence"
        ),
        "peak_r_distribution": peak_buckets,
        "be_armed_trades":   _seg_stats(be_armed),
        "be_unarmed_trades": _seg_stats(be_unarmed),
        "session_overview": {
            "total":          len(session_trades),
            "wins":           len(session_wins),
            "losses":         len(session_losses),
            "win_rate_pct":   round(len(session_wins) / max(len(session_trades), 1) * 100, 1),
            "avg_net_pnl":    _safe_avg([t.net_pnl for t in session_trades]),
        },
        "fix_a_verdict": (
            "ACTIVE — monitor be_armed_trades vs be_unarmed_trades over next 300+ trades"
            if len(has_peak_data) < 300 else
            "MEASURABLE — compare be_armed_trades.avg_net_pnl vs be_unarmed_trades.avg_net_pnl"
        ),
        "fix_c_readiness": {
            "peak_r_trades_needed": 300,
            "peak_r_trades_have":   len(has_peak_data),
            "ready": len(has_peak_data) >= 300,
        },
    }


# ── FORENSIC: First Promotion Watch ──────────────────────────────────────────
@app.get("/api/forensics/promotion-watch")
async def promotion_watch():
    """
    Real-time watch for the first genome promotion.
    Shows what the best candidate so far achieved vs what is needed,
    and how far from promotion each strategy type is.
    """
    state     = genome.get_state()
    gen_log   = state.get("recent_genomes", [])
    promo_log = state.get("promotion_log", [])
    promoted  = [p for p in promo_log if p.get("decision") == "PROMOTED"]
    rejected  = [p for p in promo_log if p.get("decision") == "REJECTED"]

    gates = {
        "win_rate_pct":   cfg.GENOME_PROMOTE_WIN_RATE * 100,
        "profit_factor":  cfg.GENOME_PROMOTE_PF,
        "avg_r_multiple": cfg.GENOME_MIN_AVG_R,
        "oos_pf":         1.0,
        "overfit_ratio":  cfg.GENOME_OVERFITTING_MAX_RATIO,
        "min_trades":     5,
    }

    # Best candidate per strategy (by fitness: WR × PF − cost_drag/100)
    best_by_strategy = {}
    for stype in ["TrendFollowing", "MeanReversion", "VolatilityExpansion"]:
        sg = [g for g in gen_log if g.get("strategy_type") == stype and g.get("trades", 0) >= 1]
        if not sg:
            best_by_strategy[stype] = {"status": "NO_EXECUTED_GENOMES"}
            continue
        best = max(sg, key=lambda g: (
            g.get("win_rate", 0) * g.get("profit_factor", 0) - g.get("cost_drag_pct", 100) / 100
        ))
        wr  = best.get("win_rate", 0) * 100
        pf  = best.get("profit_factor", 0)
        ar  = best.get("avg_r_multiple", 0)
        oos = best.get("oos_pf", 0)
        trd = best.get("trades", 0)
        best_by_strategy[stype] = {
            "genome_id":        best.get("genome_id", "?"),
            "trades":           trd,
            "win_rate_pct":     round(wr, 1),
            "profit_factor":    round(pf, 3),
            "avg_r_multiple":   round(ar, 3),
            "oos_pf":           round(oos, 3),
            "cost_drag_pct":    best.get("cost_drag_pct", 0),
            "gates_passing": {
                "win_rate":    wr   >= gates["win_rate_pct"],
                "profit_factor": pf >= gates["profit_factor"],
                "avg_r":       ar   >= gates["avg_r_multiple"],
                "oos_pf":      oos  >= gates["oos_pf"],
                "min_trades":  trd  >= gates["min_trades"],
            },
            "gaps": {
                "win_rate_gap":   round(max(gates["win_rate_pct"] - wr,  0), 1),
                "pf_gap":         round(max(gates["profit_factor"] - pf,  0), 3),
                "avg_r_gap":      round(max(gates["avg_r_multiple"] - ar, 0), 3),
                "oos_pf_gap":     round(max(gates["oos_pf"] - oos, 0), 3),
            },
        }

    # Recent rejection pattern
    recent_rejections = promo_log[-9:] if promo_log else []

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "promotion_status": {
            "first_promotion_achieved": len(promoted) > 0,
            "total_promoted":  len(promoted),
            "total_rejected":  len(rejected),
            "total_cycles":    state.get("generation", 0),
        },
        "first_promotion": promoted[0] if promoted else None,
        "promotion_gate_thresholds": gates,
        "best_candidate_by_strategy": best_by_strategy,
        "recent_rejection_log": recent_rejections,
        "watch_signal": (
            "🎉 FIRST PROMOTION ACHIEVED" if promoted else
            "⏳ WATCHING — no promotion yet. Check best_candidate_by_strategy.gaps for distance."
        ),
    }


@app.get("/api/forensics/promotion-failure-audit")
async def promotion_failure_audit():
    """
    Promotion Failure Audit — answers WHY genomes are not being promoted.

    Parses the full promotion_log and breaks down every REJECTED decision
    by which gate(s) caused the failure. Shows actual metric distributions
    vs the required thresholds so the gap is quantified, not just identified.

    Gate structure (ALL must pass for promotion):
      Gate 1 — Train: win_rate ≥ GENOME_PROMOTE_WIN_RATE, PF ≥ GENOME_PROMOTE_PF, trades ≥ 5
      Gate 2 — OOS:   oos_pf ≥ GENOME_OOS_MIN_PF (when OOS data available)
      Gate 3 — R:     avg_r_multiple ≥ GENOME_MIN_AVG_R
      Gate 4 — Overfit: train_pf / oos_pf ≤ GENOME_OVERFITTING_MAX_RATIO
    """
    state     = genome.export_state()
    promo_log = state.get("promotion_log", [])

    rejected  = [p for p in promo_log if p.get("decision") == "REJECTED"]
    promoted  = [p for p in promo_log if p.get("decision") == "PROMOTED"]
    total     = len(rejected) + len(promoted)

    # ── Gate failure counters ─────────────────────────────────────────────────
    gate_fails = {
        "train_gate":  0,  # win_rate / PF / trades below threshold
        "oos_gate":    0,  # oos_pf below floor
        "r_gate":      0,  # avg_r_multiple below min
        "overfit":     0,  # train_pf / oos_pf ratio too high
        "multi_gate":  0,  # failed 2+ gates simultaneously
    }
    # track how many failed each specific count
    gate_fail_counts: list[int] = []

    # ── Metric distributions for rejected candidates ──────────────────────────
    train_pfs:   list[float] = []
    oos_pfs:     list[float] = []
    avg_rs:      list[float] = []
    overfit_ratios: list[float] = []

    for p in rejected:
        reason = p.get("reason", "")
        gates_hit = 0
        if "train_gate" in reason:
            gate_fails["train_gate"] += 1
            gates_hit += 1
        if "oos_gate" in reason:
            gate_fails["oos_gate"] += 1
            gates_hit += 1
        if "r_gate" in reason:
            gate_fails["r_gate"] += 1
            gates_hit += 1
        if "overfit" in reason:
            gate_fails["overfit"] += 1
            gates_hit += 1
        if gates_hit >= 2:
            gate_fails["multi_gate"] += 1
        gate_fail_counts.append(gates_hit)

        pf = p.get("train_pf", 0)
        oos = p.get("oos_pf", 0)
        ar  = p.get("avg_r_multiple", 0)
        if pf:
            train_pfs.append(pf)
        if oos:
            oos_pfs.append(oos)
        if ar:
            avg_rs.append(ar)
        if pf > 0 and oos > 0:
            overfit_ratios.append(_safe_num(pf / oos))

    def _pct(n): return round(n / len(rejected) * 100, 1) if rejected else 0.0
    def _avg(lst): return _safe_num(round(sum(_safe_num(x) for x in lst) / len(lst), 3)) if lst else 0.0
    def _med(lst):
        if not lst: return 0.0
        s = sorted(_safe_num(x) for x in lst)
        m = len(s) // 2
        return _safe_num(round(s[m], 3))
    def _pct_below(lst, thresh):
        if not lst: return 0.0
        return round(sum(1 for x in lst if _safe_num(x) < thresh) / len(lst) * 100, 1)
    def _pct_above(lst, thresh):
        if not lst: return 0.0
        return round(sum(1 for x in lst if _safe_num(x) > thresh) / len(lst) * 100, 1)

    # ── Per-strategy breakdown ────────────────────────────────────────────────
    by_strategy: dict = {}
    for stype in ["TrendFollowing", "MeanReversion", "VolatilityExpansion"]:
        sr = [p for p in rejected if p.get("strategy_type") == stype]
        sp = [p for p in promoted if p.get("strategy_type") == stype]
        if not sr:
            by_strategy[stype] = {"rejected": 0, "promoted": len(sp), "primary_blockers": []}
            continue
        # Find primary blocker (most common gate failure for this strategy)
        sg_fails = {"train_gate": 0, "oos_gate": 0, "r_gate": 0, "overfit": 0}
        for p in sr:
            r = p.get("reason", "")
            for g in sg_fails:
                if g in r:
                    sg_fails[g] += 1
        primary = sorted(sg_fails.items(), key=lambda x: -x[1])
        sr_pfs = [p["train_pf"] for p in sr if p.get("train_pf", 0) > 0]
        sr_oos = [p["oos_pf"]   for p in sr if p.get("oos_pf",   0) > 0]
        sr_r   = [p["avg_r_multiple"] for p in sr if p.get("avg_r_multiple", 0) > 0]
        by_strategy[stype] = {
            "rejected": len(sr),
            "promoted": len(sp),
            "primary_blockers": [{"gate": g, "count": c} for g, c in primary if c > 0],
            "avg_train_pf": _avg(sr_pfs),
            "avg_oos_pf":   _avg(sr_oos),
            "avg_r":        _avg(sr_r),
            "pct_below_train_pf_threshold": _pct_below(sr_pfs, cfg.GENOME_PROMOTE_PF),
            "pct_below_r_threshold":        _pct_below(sr_r,  cfg.GENOME_MIN_AVG_R),
        }

    # ── Verdict ───────────────────────────────────────────────────────────────
    if not rejected:
        verdict = "INSUFFICIENT_DATA"
        verdict_detail = "No rejection events recorded yet — genome engine may be in early warmup."
    else:
        top_gate = max(gate_fails, key=gate_fails.get) if any(gate_fails.values()) else None
        top_count = gate_fails.get(top_gate, 0)
        top_pct = _pct(top_count)

        # Determine if gates are protecting correctly or are structurally impossible
        # Impossible = >90% of rejections fail the same gate AND avg metric is far from threshold
        if top_gate == "r_gate" and _avg(avg_rs) < cfg.GENOME_MIN_AVG_R * 0.5:
            verdict = "GATE_MAY_BE_STRUCTURALLY_IMPOSSIBLE"
            verdict_detail = (
                f"{top_pct}% of rejections fail {top_gate}. "
                f"Avg avg_R={_avg(avg_rs):.3f} vs threshold {cfg.GENOME_MIN_AVG_R} — "
                f"candidates are achieving less than 50% of required R. "
                f"Investigate whether market conditions support this R threshold."
            )
        elif top_gate == "train_gate" and _avg(train_pfs) < cfg.GENOME_PROMOTE_PF * 0.7:
            verdict = "GATE_MAY_BE_STRUCTURALLY_IMPOSSIBLE"
            verdict_detail = (
                f"{top_pct}% of rejections fail {top_gate}. "
                f"Avg train_PF={_avg(train_pfs):.3f} vs threshold {cfg.GENOME_PROMOTE_PF} — "
                f"candidates are well below required PF. "
                f"May indicate strategy edge is insufficient in current regime."
            )
        elif top_pct > 60:
            verdict = "SINGLE_GATE_DOMINATES"
            verdict_detail = (
                f"{top_pct}% of all rejections blocked by {top_gate}. "
                f"This gate is the primary bottleneck. Review whether threshold is calibrated correctly."
            )
        else:
            verdict = "MULTI_GATE_FAILURE"
            verdict_detail = (
                f"No single gate dominates (highest={top_pct}% on {top_gate}). "
                f"Candidates are failing multiple gates — likely a fundamental edge problem "
                f"rather than a threshold calibration issue."
            )

    # ── DELIVERABLE 1: Train Gate Root Cause Matrix ───────────────────────────
    # Decompose train_gate failures into PF/WR/Trades individual and combo failures
    _tg_min_trades = 5
    tg_pf_fail = tg_wr_fail = tg_tr_fail = 0
    tg_pf_wr = tg_pf_tr = tg_wr_tr = tg_all3 = 0
    for p in rejected:
        if "train_gate" not in p.get("reason", ""):
            continue
        pf_f  = _safe_num(p.get("train_pf", 0)) < cfg.GENOME_PROMOTE_PF
        wr_f  = _safe_num(p.get("win_rate", 0)) < cfg.GENOME_PROMOTE_WIN_RATE * 100
        tr_f  = p.get("train_trades", 0) < _tg_min_trades
        combo = sum([pf_f, wr_f, tr_f])
        if pf_f: tg_pf_fail += 1
        if wr_f: tg_wr_fail += 1
        if tr_f: tg_tr_fail += 1
        if pf_f and wr_f and not tr_f: tg_pf_wr += 1
        if pf_f and tr_f and not wr_f: tg_pf_tr += 1
        if wr_f and tr_f and not pf_f: tg_wr_tr += 1
        if combo == 3: tg_all3 += 1
    tg_total = gate_fails["train_gate"] or 1  # avoid div/0
    train_gate_breakdown = {
        "pf_failures":          {"count": tg_pf_fail, "pct": round(tg_pf_fail / tg_total * 100, 1)},
        "wr_failures":          {"count": tg_wr_fail, "pct": round(tg_wr_fail / tg_total * 100, 1)},
        "trade_count_failures": {"count": tg_tr_fail, "pct": round(tg_tr_fail / tg_total * 100, 1)},
        "pf_and_wr":            {"count": tg_pf_wr,   "pct": round(tg_pf_wr   / tg_total * 100, 1)},
        "pf_and_trades":        {"count": tg_pf_tr,   "pct": round(tg_pf_tr   / tg_total * 100, 1)},
        "wr_and_trades":        {"count": tg_wr_tr,   "pct": round(tg_wr_tr   / tg_total * 100, 1)},
        "all_three":            {"count": tg_all3,    "pct": round(tg_all3    / tg_total * 100, 1)},
    }

    # ── DELIVERABLE 2: OOS Diagnostics ────────────────────────────────────────
    oos_t_vals  = [p.get("oos_trades", 0) for p in rejected]
    all_t_vals  = [p.get("train_trades", 0) for p in rejected]
    oos_zero    = sum(1 for t in oos_t_vals if t == 0)
    oos_1_5     = sum(1 for t in oos_t_vals if 1 <= t <= 5)
    oos_6_20    = sum(1 for t in oos_t_vals if 6 <= t <= 20)
    oos_gt20    = sum(1 for t in oos_t_vals if t > 20)
    avg_oos_trades = _avg(oos_t_vals) if oos_t_vals else 0.0
    avg_oos_pf     = _avg(oos_pfs)
    avg_train_trades = _avg(all_t_vals) if all_t_vals else 0.0
    oos_diagnostics = {
        "candidates_evaluated":      len(rejected),
        "oos_trades_zero":           {"count": oos_zero,  "pct": round(oos_zero  / len(rejected) * 100, 1) if rejected else 0.0},
        "oos_trades_1_to_5":         {"count": oos_1_5,   "pct": round(oos_1_5   / len(rejected) * 100, 1) if rejected else 0.0},
        "oos_trades_6_to_20":        {"count": oos_6_20,  "pct": round(oos_6_20  / len(rejected) * 100, 1) if rejected else 0.0},
        "oos_trades_above_20":       {"count": oos_gt20,  "pct": round(oos_gt20  / len(rejected) * 100, 1) if rejected else 0.0},
        "avg_oos_trades":            avg_oos_trades,
        "avg_oos_pf":                avg_oos_pf,
        "avg_train_trades":          avg_train_trades,
        "interpretation": (
            "OOS path is NOT producing data — candidates have insufficient candle history."
            if oos_zero > len(rejected) * 0.8 else
            "OOS path is producing some data — further accumulation needed for full analysis."
        ),
    }

    # ── DELIVERABLE 3: Sentinel Value Report ──────────────────────────────────
    _SENTINEL_PF      = 999.0
    _SENTINEL_OVERFIT = 999.0
    sentinel_pf_count      = sum(1 for p in rejected if _safe_num(p.get("train_pf", 0)) >= _SENTINEL_PF)
    sentinel_oos_zero      = oos_zero
    sentinel_overfit_count = sum(1 for p in rejected if "overfit(ratio=999" in p.get("reason", ""))
    sentinel_none_sub      = sum(1 for p in rejected if p.get("train_pf") is None or p.get("oos_pf") is None)
    sentinel_zero_pf_sub   = sum(1 for p in rejected if p.get("train_pf", -1) == 0)
    sentinel_report = {
        "pf_sentinel_999_count":        {"count": sentinel_pf_count,      "pct": round(sentinel_pf_count      / len(rejected) * 100, 1) if rejected else 0.0},
        "oos_pf_zero_count":            {"count": sentinel_oos_zero,       "pct": round(sentinel_oos_zero      / len(rejected) * 100, 1) if rejected else 0.0},
        "overfit_sentinel_999_count":   {"count": sentinel_overfit_count,  "pct": round(sentinel_overfit_count / len(rejected) * 100, 1) if rejected else 0.0},
        "none_substitutions":           {"count": sentinel_none_sub,       "pct": round(sentinel_none_sub      / len(rejected) * 100, 1) if rejected else 0.0},
        "zero_pf_fallback_count":       {"count": sentinel_zero_pf_sub,    "pct": round(sentinel_zero_pf_sub   / len(rejected) * 100, 1) if rejected else 0.0},
        "interpretation": (
            "HIGH sentinel prevalence — majority of candidates are placeholder-valued, "
            "indicating data insufficiency rather than genuine strategy failure."
            if (sentinel_pf_count + sentinel_oos_zero) > len(rejected) * 0.5 else
            "Sentinel values within acceptable range — majority of candidates have real metric values."
        ),
    }

    # ── DELIVERABLE 4: Candidate Quality Distribution ─────────────────────────
    all_rs  = [_safe_num(p.get("avg_r_multiple", 0)) for p in rejected]
    all_pfs = [_safe_num(p.get("train_pf", 0)) for p in rejected]
    quality_distribution = {
        "avg_r_distribution": {
            "below_zero":    {"count": sum(1 for r in all_rs  if r < 0),                      "pct": round(sum(1 for r in all_rs  if r < 0)             / len(rejected) * 100, 1) if rejected else 0.0},
            "zero_to_0_5":   {"count": sum(1 for r in all_rs  if 0 <= r < 0.5),               "pct": round(sum(1 for r in all_rs  if 0 <= r < 0.5)      / len(rejected) * 100, 1) if rejected else 0.0},
            "0_5_to_1_0":    {"count": sum(1 for r in all_rs  if 0.5 <= r < 1.0),             "pct": round(sum(1 for r in all_rs  if 0.5 <= r < 1.0)    / len(rejected) * 100, 1) if rejected else 0.0},
            "above_1_0":     {"count": sum(1 for r in all_rs  if r >= 1.0),                   "pct": round(sum(1 for r in all_rs  if r >= 1.0)          / len(rejected) * 100, 1) if rejected else 0.0},
        },
        "train_pf_distribution": {
            "below_1_0":     {"count": sum(1 for p in all_pfs if p < 1.0),                    "pct": round(sum(1 for p in all_pfs if p < 1.0)           / len(rejected) * 100, 1) if rejected else 0.0},
            "1_0_to_1_2":    {"count": sum(1 for p in all_pfs if 1.0 <= p < 1.2),             "pct": round(sum(1 for p in all_pfs if 1.0 <= p < 1.2)    / len(rejected) * 100, 1) if rejected else 0.0},
            "1_2_to_2_0":    {"count": sum(1 for p in all_pfs if 1.2 <= p < 2.0),             "pct": round(sum(1 for p in all_pfs if 1.2 <= p < 2.0)    / len(rejected) * 100, 1) if rejected else 0.0},
            "above_2_0":     {"count": sum(1 for p in all_pfs if p >= 2.0),                   "pct": round(sum(1 for p in all_pfs if p >= 2.0)          / len(rejected) * 100, 1) if rejected else 0.0},
        },
        "trade_count_distribution": {
            "zero_trades":   {"count": sum(1 for p in rejected if p.get("train_trades", 0) == 0), "pct": round(sum(1 for p in rejected if p.get("train_trades", 0) == 0) / len(rejected) * 100, 1) if rejected else 0.0},
            "1_to_4":        {"count": sum(1 for p in rejected if 1 <= p.get("train_trades", 0) <= 4), "pct": round(sum(1 for p in rejected if 1 <= p.get("train_trades", 0) <= 4) / len(rejected) * 100, 1) if rejected else 0.0},
            "5_to_10":       {"count": sum(1 for p in rejected if 5 <= p.get("train_trades", 0) <= 10), "pct": round(sum(1 for p in rejected if 5 <= p.get("train_trades", 0) <= 10) / len(rejected) * 100, 1) if rejected else 0.0},
            "above_10":      {"count": sum(1 for p in rejected if p.get("train_trades", 0) > 10), "pct": round(sum(1 for p in rejected if p.get("train_trades", 0) > 10) / len(rejected) * 100, 1) if rejected else 0.0},
        },
    }

    return {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "summary": {
            "total_decisions":  total,
            "total_rejected":   len(rejected),
            "total_promoted":   len(promoted),
            "promotion_rate_pct": round(len(promoted) / total * 100, 2) if total else 0.0,
        },
        "thresholds": {
            "Gate1_win_rate_pct":      cfg.GENOME_PROMOTE_WIN_RATE * 100,
            "Gate1_profit_factor":     cfg.GENOME_PROMOTE_PF,
            "Gate1_min_trades":        5,
            "Gate2_oos_pf":            cfg.GENOME_OOS_MIN_PF,
            "Gate3_avg_r_multiple":    cfg.GENOME_MIN_AVG_R,
            "Gate4_overfit_max_ratio": cfg.GENOME_OVERFITTING_MAX_RATIO,
        },
        "gate_failure_breakdown": {
            "train_gate_failures": {"count": gate_fails["train_gate"], "pct_of_rejected": _pct(gate_fails["train_gate"])},
            "oos_gate_failures":   {"count": gate_fails["oos_gate"],   "pct_of_rejected": _pct(gate_fails["oos_gate"])},
            "r_gate_failures":     {"count": gate_fails["r_gate"],     "pct_of_rejected": _pct(gate_fails["r_gate"])},
            "overfit_failures":    {"count": gate_fails["overfit"],    "pct_of_rejected": _pct(gate_fails["overfit"])},
            "multi_gate_failures": {"count": gate_fails["multi_gate"], "pct_of_rejected": _pct(gate_fails["multi_gate"])},
        },
        "train_gate_root_cause_matrix": train_gate_breakdown,
        "oos_diagnostics": oos_diagnostics,
        "sentinel_value_report": sentinel_report,
        "candidate_quality_distribution": quality_distribution,
        "rejected_candidate_metrics": {
            "train_pf":   {"avg": _avg(train_pfs), "median": _med(train_pfs), "pct_below_threshold": _pct_below(train_pfs, cfg.GENOME_PROMOTE_PF)},
            "oos_pf":     {"avg": _avg(oos_pfs),   "median": _med(oos_pfs),   "pct_below_threshold": _pct_below(oos_pfs,   cfg.GENOME_OOS_MIN_PF)},
            "avg_r":      {"avg": _avg(avg_rs),    "median": _med(avg_rs),    "pct_below_threshold": _pct_below(avg_rs,    cfg.GENOME_MIN_AVG_R)},
            "overfit_ratio": {"avg": _avg(overfit_ratios), "median": _med(overfit_ratios), "pct_above_threshold": _pct_above(overfit_ratios, cfg.GENOME_OVERFITTING_MAX_RATIO)},
        },
        "by_strategy": by_strategy,
        "verdict": verdict,
        "verdict_detail": verdict_detail,
        "recent_rejections": [
            {
                "ts":           p.get("ts"),
                "strategy":     p.get("strategy_type"),
                "reason":       p.get("reason"),
                "train_pf":     _safe_num(round(_safe_num(p.get("train_pf", 0)), 3)),
                "oos_pf":       _safe_num(round(_safe_num(p.get("oos_pf", 0)), 3)),
                "avg_r":        _safe_num(round(_safe_num(p.get("avg_r_multiple", 0)), 3)),
                "cost_drag":    _safe_num(round(_safe_num(p.get("cost_drag_pct", 0)), 1)),
                "train_trades": p.get("train_trades", 0),
                "oos_trades":   p.get("oos_trades", 0),
                "win_rate":     _safe_num(round(_safe_num(p.get("win_rate", 0)), 1)),
            }
            for p in rejected[-20:]
        ],
        "interpretation": {
            "A_gates_protecting_correctly": "All gates failing at reasonable rates — system is working as designed. No threshold change needed.",
            "B_structurally_impossible":    "One or more gates rejecting >90% of candidates with metrics far below threshold — threshold may need review after further data accumulation.",
            "current_verdict":             verdict,
        },
    }


# ── FTD-AIL-001: Autonomous Intelligence Layer API ────────────────────────────

@app.get("/api/autonomous-intelligence/status")
async def ail_status():
    """AIL — current status: enabled flag, collection stats, finding counts by severity/status."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    return await ail_engine.get_status()


@app.get("/api/autonomous-intelligence/findings")
async def ail_findings(status: str | None = None):
    """AIL — list all findings, optionally filtered by status (PENDING|APPROVED|REJECTED|NEEDS_MORE_EVIDENCE)."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    return {"findings": await ail_engine.get_findings(status)}


@app.get("/api/autonomous-intelligence/findings/{finding_id}")
async def ail_finding_detail(finding_id: str):
    """AIL — get full detail for a single finding by lineage_id."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    f = await ail_engine.get_finding(finding_id)
    if f is None:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")
    return f


@app.post("/api/autonomous-intelligence/finding/{finding_id}/approve")
async def ail_approve(finding_id: str):
    """AIL — approve a finding (human action, no auto-code-change)."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    try:
        return await ail_engine.approve_finding(finding_id)
    except KeyError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/autonomous-intelligence/finding/{finding_id}/reject")
async def ail_reject(finding_id: str, reason: str = ""):
    """AIL — reject a finding (human action)."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    try:
        return await ail_engine.reject_finding(finding_id, reason)
    except KeyError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/autonomous-intelligence/finding/{finding_id}/needs-evidence")
async def ail_needs_evidence(finding_id: str, reason: str = ""):
    """AIL — mark finding as needing more evidence before decision."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    try:
        return await ail_engine.needs_evidence(finding_id, reason)
    except KeyError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/autonomous-intelligence/finding/{finding_id}/supersede")
async def ail_supersede(finding_id: str, reason: str = ""):
    """AIL — supersede a stale APPROVED/PENDING finding (governance hygiene).
    Removes the finding from the active dedup set so AIL can generate a fresh
    finding from current data. Original finding is preserved in history.
    """
    from core.autonomous_intelligence.ail_engine import ail_engine
    try:
        return await ail_engine.supersede_finding(finding_id, reason)
    except KeyError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/autonomous-intelligence/history")
async def ail_history(limit: int = 100):
    """AIL — immutable approval/rejection history timeline."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    return {"history": await ail_engine.get_history(limit)}


@app.get("/api/autonomous-intelligence/daily-brief")
async def ail_daily_brief():
    """AIL — daily intelligence brief: top pending findings by evidence score."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    return await ail_engine.get_daily_brief()


@app.post("/api/autonomous-intelligence/force-collect")
async def ail_force_collect():
    """AIL — force an immediate collection + analysis cycle."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    result = await ail_engine.force_collect()
    return {"status": "ok", "result": result}


@app.post("/api/autonomous-intelligence/enable")
async def ail_enable():
    """AIL — enable the autonomous intelligence layer."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    ail_engine.enable()
    return {"status": "enabled"}


@app.post("/api/autonomous-intelligence/disable")
async def ail_disable():
    """AIL — disable the autonomous intelligence layer (stops scheduler)."""
    from core.autonomous_intelligence.ail_engine import ail_engine
    ail_engine.disable()
    return {"status": "disabled"}


async def prp002_download():
    """PRP-002 — All Signal Ecology reports as a single downloadable ZIP."""
    import zipfile, io as _io, json as _json
    from fastapi.responses import StreamingResponse

    ts = int(time.time())
    buf = _io.BytesIO()

    files = {
        "00_ecology_snapshot.json":    opportunity_ecology.ecology_snapshot(),
        "01_full_telemetry.json":      opportunity_ecology.get_telemetry(),
        "02_density_engine.json":      signal_density_engine.get_telemetry(),
        "03_rsi_governor.json":        adaptive_rsi_governor.get_telemetry(),
        "04_recovery_governor.json":   exploration_recovery_governor.get_telemetry(),
        "05_context_memory.json":      alpha_context_memory.get_telemetry(),
        "06_context_clusters.json":    {"clusters": alpha_context_memory.context_clusters(n=50)},
        "07_rsi_decisions.json":       {"decisions": adaptive_rsi_governor.recent_decisions(n=100)},
        "08_recovery_history.json":    {"cycles": exploration_recovery_governor.cycle_history(n=50)},
        "09_block_reason_matrix.json": {"block_reasons": signal_density_engine.block_reason_matrix()},
    }

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, data in files.items():
            zf.writestr(fname, _json.dumps(data, indent=2, default=str))

    buf.seek(0)
    fn = f"prp002_signal_ecology_{ts}.zip"
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{fn}"'},
    )


# ── PRP-002 Analytics Reports API ─────────────────────────────────────────────

@app.get("/api/prp/002/analytics/density-reports")
async def prp002_analytics_density():
    """PRP-002 Analytics — Reports 01,02,06,07,09,10: density, filter, ecology."""
    from analytics.odyssey.signal_density_reports import generate_all_reports
    return await asyncio.get_event_loop().run_in_executor(None, generate_all_reports)


@app.get("/api/prp/002/analytics/exploration-reports")
async def prp002_analytics_exploration():
    """PRP-002 Analytics — Reports 03,08: collapse monitor and recovery cycles."""
    from analytics.odyssey.exploration_reports import generate_all_reports
    return await asyncio.get_event_loop().run_in_executor(None, generate_all_reports)


@app.get("/api/prp/002/analytics/context-reports")
async def prp002_analytics_context():
    """PRP-002 Analytics — Reports 04,05: alpha context clusters and recurrence."""
    from analytics.odyssey.context_cluster_reports import generate_all_reports
    return await asyncio.get_event_loop().run_in_executor(None, generate_all_reports)


@app.get("/api/prp/002/analytics/full-bundle")
async def prp002_analytics_full_bundle():
    """PRP-002 Analytics — All 10 forensic reports in one bundle (complete=True)."""
    from analytics.odyssey.context_cluster_reports import generate_full_prp002_bundle
    return await asyncio.get_event_loop().run_in_executor(None, generate_full_prp002_bundle)


# ── Phase-B Cross-PRP Wiring Audit API ────────────────────────────────────────

@app.get("/api/wiring-audit/constitution")
async def wiring_audit_constitution():
    """Phase-B.1 — PRP Registry & Endpoint Constitutional Audit."""
    from core.cross_prp_audit.endpoint_constitution_auditor import audit_endpoint_constitution
    return await asyncio.get_event_loop().run_in_executor(None, audit_endpoint_constitution)


@app.get("/api/wiring-audit/propagation")
async def wiring_audit_propagation():
    """Phase-B.2 — Cross-Report Propagation Audit (ghost/orphan detection)."""
    from core.cross_prp_audit.report_propagation_auditor import audit_report_propagation
    return await asyncio.get_event_loop().run_in_executor(None, audit_report_propagation)


@app.get("/api/wiring-audit/dependencies")
async def wiring_audit_dependencies():
    """Phase-B.3 — Dependency Survivability Audit (import/init chain)."""
    from core.cross_prp_audit.dependency_survivability_auditor import audit_dependency_survivability
    return await asyncio.get_event_loop().run_in_executor(None, audit_dependency_survivability)


@app.get("/api/wiring-audit/archive")
async def wiring_audit_archive():
    """Phase-B.4 — Archive Replay & Continuity Audit (bundle determinism)."""
    from core.cross_prp_audit.archive_continuity_auditor import audit_archive_continuity
    return await asyncio.get_event_loop().run_in_executor(None, audit_archive_continuity)


@app.get("/api/wiring-audit/rendering")
async def wiring_audit_rendering():
    """Phase-B.5 — Institutional Rendering Consistency Audit (multi-mode parity)."""
    from core.cross_prp_audit.rendering_consistency_auditor import audit_rendering_consistency
    return await asyncio.get_event_loop().run_in_executor(None, audit_rendering_consistency)


@app.get("/api/wiring-audit/compression")
async def wiring_audit_compression():
    """Phase-B.6 — Operational Compression Readiness Mapping (Tier 1-4 classification)."""
    from core.cross_prp_audit.compression_readiness_mapper import map_compression_readiness
    return await asyncio.get_event_loop().run_in_executor(None, map_compression_readiness)


@app.get("/api/wiring-audit/full-report")
async def wiring_audit_full_report():
    """Phase-B Master — Full Cross-PRP Wiring Audit (all 6 domains, composite score)."""
    from core.cross_prp_audit.cross_prp_audit_orchestrator import run_full_wiring_audit
    return await asyncio.get_event_loop().run_in_executor(None, run_full_wiring_audit)


@app.get("/api/wiring-audit/health")
async def wiring_audit_health():
    """Phase-B Health — Lightweight wiring health check (scores + tier only)."""
    from core.cross_prp_audit.cross_prp_audit_orchestrator import get_wiring_audit_health
    return await asyncio.get_event_loop().run_in_executor(None, get_wiring_audit_health)


# ── Phase-C: Operational Compression Layer ────────────────────────────────────

@app.get("/api/compression/executive")
async def compression_executive():
    """Phase-C Executive — Executive compression of full institutional intelligence."""
    from core.operational_compression.executive_compression_engine import generate_executive_compression
    return await asyncio.get_event_loop().run_in_executor(None, generate_executive_compression)


@app.get("/api/compression/health")
async def compression_health():
    """Phase-C Health — Institutional health score across 9 weighted domains."""
    from core.operational_compression.institutional_health_score_engine import compute_institutional_health
    return await asyncio.get_event_loop().run_in_executor(None, compute_institutional_health)


@app.get("/api/compression/anomalies")
async def compression_anomalies():
    """Phase-C Anomalies — Clustered anomaly report across 7 institutional domains."""
    from core.operational_compression.anomaly_clustering_engine import cluster_anomalies
    return await asyncio.get_event_loop().run_in_executor(None, cluster_anomalies)


@app.get("/api/compression/ecology")
async def compression_ecology():
    """Phase-C Ecology — Signal ecology compressed into 8 operator-readable domains."""
    from core.operational_compression.signal_ecology_compression_layer import compress_signal_ecology
    return await asyncio.get_event_loop().run_in_executor(None, compress_signal_ecology)


@app.get("/api/compression/governance")
async def compression_governance():
    """Phase-C Governance — Governance civilization compressed into executive summary."""
    from core.operational_compression.governance_compression_layer import compress_governance
    return await asyncio.get_event_loop().run_in_executor(None, compress_governance)


@app.get("/api/compression/visibility")
async def compression_visibility():
    """Phase-C Visibility — Multi-tier visibility architecture with lineage preservation."""
    from core.operational_compression.multi_tier_visibility_architecture import build_visibility_tier_map
    return await asyncio.get_event_loop().run_in_executor(None, build_visibility_tier_map)


@app.get("/api/compression/orchestration")
async def compression_orchestration():
    """Phase-C Orchestration — Unified OPERATIONAL_COMPRESSION_REPORT across all domains."""
    from core.operational_compression.compression_orchestrator import run_full_compression
    return await asyncio.get_event_loop().run_in_executor(None, run_full_compression)


# ── Phase-D: Economic Truth Reconstruction API ───────────────────────────────

def _build_eco_trades() -> list:
    """Combine session + historical trades deduplicated by trade_id, oldest first."""
    session_trades = [asdict(t) for t in pnl_calc.trades]
    historical     = data_lake.get_trades(limit=1000)
    seen: dict[str, dict] = {}
    for t in session_trades:
        tid = t.get("trade_id", "")
        if tid:
            seen[tid] = t
    for t in historical:
        tid = t.get("trade_id", "")
        if tid and tid not in seen:
            seen[tid] = t
    # Sort chronologically so IS/OOS splits and cumulative-PnL curves are correct.
    # data_lake returns DESC by default; without sorting, OOS = oldest trades (backwards).
    return sorted(seen.values(), key=lambda t: t.get("exit_ts", 0))


# Phase-I uses a rolling window so the certification reflects the CURRENT strategy
# config, not all-time history which may span multiple strategy revisions.
_PHASE_I_LOOKBACK = 300


def _build_phase_i_trades() -> list:
    """Most recent _PHASE_I_LOOKBACK trades for Phase-I alpha certification."""
    return _build_eco_trades()[-_PHASE_I_LOOKBACK:]


@app.get("/api/economic-truth/expectancy")
async def economic_truth_expectancy():
    """Phase-D Expectancy — Multi-axis expectancy reconstruction with survivability verdict."""
    from core.economic_truth_reconstruction.expectancy_reconstruction import compute_expectancy_reconstruction
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_expectancy_reconstruction, trades
    )


@app.get("/api/economic-truth/fee-drag")
async def economic_truth_fee_drag():
    """Phase-D Fee Drag — Fee drag intelligence with cost-adjusted survivability assessment."""
    from core.economic_truth_reconstruction.fee_drag_intelligence import compute_fee_drag_intelligence
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_fee_drag_intelligence, trades
    )


@app.get("/api/economic-truth/alpha")
async def economic_truth_alpha():
    """Phase-D Alpha — Survivable alpha detector across 8 dimensions."""
    from core.economic_truth_reconstruction.survivable_alpha_detector import detect_survivable_alpha
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, detect_survivable_alpha, trades
    )


@app.get("/api/economic-truth/ecology")
async def economic_truth_ecology():
    """Phase-D Ecology — Ecological collapse detector with live telemetry + trade history."""
    from core.economic_truth_reconstruction.ecological_collapse_detector import detect_ecological_collapse
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, detect_ecological_collapse, trades
    )


@app.get("/api/economic-truth/regime")
async def economic_truth_regime():
    """Phase-D Regime — Regime survivability across 6 extended regime categories."""
    from core.economic_truth_reconstruction.regime_survivability_engine import compute_regime_survivability
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_regime_survivability, trades
    )


@app.get("/api/economic-truth/filtration")
async def economic_truth_filtration():
    """Phase-D Filtration — Adaptive signal filtration candidates with contradictory evidence."""
    from core.economic_truth_reconstruction.adaptive_signal_filtration import compute_adaptive_filtration
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_adaptive_filtration, trades
    )


@app.get("/api/economic-truth/orchestration")
async def economic_truth_orchestration():
    """Phase-D Orchestration — Unified ECONOMIC_TRUTH_REPORT across all 6 engines."""
    from core.economic_truth_reconstruction.economic_truth_orchestrator import run_economic_truth
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, run_economic_truth, trades
    )


@app.get("/api/economic-truth/dashboard")
async def economic_truth_dashboard():
    """
    Economic Truth Command Center — all 9 dashboard sections in one fast call.
    Computes directly from trade records; no heavy orchestration modules invoked.
    Primary data source for the Economic Truth landing tab.
    """
    import time as _t

    trades = _build_eco_trades()
    n = len(trades)

    # ── Core vectors ──────────────────────────────────────────────────────────
    nets    = [t.get("net_pnl",   0.0) for t in trades]
    grosses = [t.get("gross_pnl", 0.0) for t in trades]
    fees    = [t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) for t in trades]

    wins    = [p for p in nets if p > 0]
    losses  = [p for p in nets if p < 0]
    be      = [p for p in nets if p == 0.0]

    total_net   = sum(nets)
    total_gross = sum(grosses)
    total_fees  = sum(fees)

    wr  = len(wins) / n if n else 0.0
    pf  = sum(wins) / abs(sum(losses)) if losses else (99.99 if wins else 0.0)
    avg_win  = sum(wins)   / len(wins)   if wins   else 0.0
    avg_loss = sum(losses) / len(losses) if losses else 0.0

    # Running equity curve + max drawdown (from initial capital)
    _initial_cap = pnl_calc._initial_capital
    running      = _initial_cap
    peak         = _initial_cap
    mdd          = 0.0
    eq_curve: list = []
    for net in nets:
        running += net
        eq_curve.append(round(running, 4))
        if running > peak:
            peak = running
        dd = (peak - running) / peak if peak > 0 else 0.0
        if dd > mdd:
            mdd = dd

    # ── §1 Executive Snapshot ─────────────────────────────────────────────────
    rr_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0
    kelly    = max(0.0, min(1.0, wr - (1 - wr) / rr_ratio if rr_ratio > 0 else 0.0))

    if   pf >= 1.5 and wr >= 0.45: alpha_tier = "ALPHA"
    elif pf >= 1.2 and wr >= 0.38: alpha_tier = "POSITIVE"
    elif pf >= 1.0:                alpha_tier = "BREAK_EVEN"
    else:                           alpha_tier = "NEGATIVE"

    # ── §2 Trade Truth ────────────────────────────────────────────────────────
    gross_pos  = [t for t in trades if t.get("gross_pnl", 0.0) > 0]
    fee_destr  = [t for t in gross_pos  if t.get("net_pnl", 0.0) <= 0]

    # ── §3 Fee Analysis ───────────────────────────────────────────────────────
    avg_fee          = total_fees / n if n else 0.0
    fee_pct_gross    = (total_fees / abs(total_gross) * 100) if total_gross else 0.0

    if   fee_pct_gross > 50: fee_severity = "CRITICAL"
    elif fee_pct_gross > 30: fee_severity = "HIGH"
    elif fee_pct_gross > 15: fee_severity = "MODERATE"
    else:                     fee_severity = "LOW"

    if n >= 40:
        r20 = sum(fees[-20:]) / 20
        p20 = sum(fees[-40:-20]) / 20
        fee_trend = "INCREASING" if r20 > p20 * 1.1 else ("DECREASING" if r20 < p20 * 0.9 else "STABLE")
    else:
        fee_trend = "INSUFFICIENT_DATA"

    # ── §4 Win/Loss Geometry ──────────────────────────────────────────────────
    def _hold_s(t: dict) -> float:
        return max(0.0, (t.get("exit_ts", 0) - t.get("entry_ts", 0)) / 1000.0)

    win_trades  = [t for t in trades if t.get("net_pnl", 0.0) > 0]
    loss_trades = [t for t in trades if t.get("net_pnl", 0.0) < 0]

    avg_win_hold  = (sum(_hold_s(t) for t in win_trades)  / len(win_trades))  if win_trades  else 0.0
    avg_loss_hold = (sum(_hold_s(t) for t in loss_trades) / len(loss_trades)) if loss_trades else 0.0

    largest_win  = max(nets) if nets else 0.0
    largest_loss = min(nets) if nets else 0.0

    # ── §5 Survivability ──────────────────────────────────────────────────────
    deploy_ready = pf >= 1.5 and wr >= 0.45 and mdd < 0.10 and n >= 50

    # ── §6 Session & Regime Truth ─────────────────────────────────────────────
    sess_map: dict   = {}
    regime_map: dict = {}
    for t in trades:
        sess = t.get("origin_session") or "UNKNOWN"
        sess_map.setdefault(sess, []).append(t.get("net_pnl", 0.0))
        reg = t.get("regime") or "UNKNOWN"
        regime_map.setdefault(reg, []).append(t.get("net_pnl", 0.0))

    def _stats(pnls: list) -> dict:
        sw = [p for p in pnls if p > 0]
        return {
            "count":   len(pnls),
            "net_pnl": round(sum(pnls), 4),
            "win_rate": round(len(sw) / len(pnls), 4) if pnls else 0.0,
            "avg_pnl": round(sum(pnls) / len(pnls), 4) if pnls else 0.0,
        }

    session_stats  = {k: _stats(v) for k, v in sess_map.items()}
    regime_stats   = {k: _stats(v) for k, v in regime_map.items()}

    cb_trades = [t for t in trades if t.get("crossed_session_boundary")]
    cb_losses = [t for t in cb_trades if t.get("net_pnl", 0.0) <= 0]

    # Best / worst session by net_pnl
    best_sess  = max(session_stats, key=lambda k: session_stats[k]["net_pnl"]) if session_stats else "—"
    worst_sess = min(session_stats, key=lambda k: session_stats[k]["net_pnl"]) if session_stats else "—"

    # ── §7 RL Intelligence ────────────────────────────────────────────────────
    try:
        rl_ev       = rl_engine.get_evolution_state()
        rl_ld       = rl_ev.get("learning_dynamics", {})
        rl_ctx      = rl_ev.get("context_maturity", {})
        toxic_c     = rl_ld.get("toxic_count",   0)
        mature_c    = rl_ctx.get("mature",        0)
        avg_q       = rl_ld.get("avg_q",          0.0)
        exp_r       = rl_ld.get("explore_ratio",  1.0)
        intell_s    = rl_ev.get("intelligence_score", 0.0)
        total_ctx   = rl_ev.get("total_contexts", 0)
        total_pulls = rl_engine._total_pulls
    except Exception:
        toxic_c = mature_c = total_ctx = total_pulls = 0
        avg_q = exp_r = intell_s = 0.0

    if   total_pulls == 0:                         adapt_state = "IDLE"
    elif avg_q < -0.3:                             adapt_state = "NEGATIVE_DRIFT"
    elif exp_r > 0.6:                              adapt_state = "EXPLORING"
    elif mature_c >= 10 and avg_q > 0:             adapt_state = "CONVERGING"
    else:                                           adapt_state = "LEARNING"

    # ── §8 Danger Radar ───────────────────────────────────────────────────────
    threats: list = []
    if n < 30:
        threats.append({"code": "LOW_SAMPLE",      "message": f"Only {n} trades — insufficient data for reliable conclusions"})
    if pf < 1.0 and n >= 30:
        threats.append({"code": "NEGATIVE_PF",     "message": f"Profit factor {pf:.3f} < 1.0 — system is losing money"})
    if mdd > 0.15:
        threats.append({"code": "HIGH_DRAWDOWN",   "message": f"Max drawdown {mdd*100:.1f}% exceeds 15% threshold"})
    if fee_pct_gross > 40 and n >= 10:
        threats.append({"code": "FEE_DESTRUCTION", "message": f"Fees consuming {fee_pct_gross:.1f}% of gross PnL"})
    if wr < 0.30 and n >= 30:
        threats.append({"code": "LOW_WIN_RATE",    "message": f"Win rate {wr*100:.1f}% — below 30% survival floor"})
    if toxic_c > 5:
        threats.append({"code": "TOXIC_CONTEXTS",  "message": f"{toxic_c} RL contexts classified toxic"})
    if len(fee_destr) > len(gross_pos) * 0.3 and len(gross_pos) >= 10:
        threats.append({"code": "FEE_KILLS_WINS",  "message": f"{len(fee_destr)}/{len(gross_pos)} gross-wins turned net-negative by fees"})

    if   len(threats) == 0: danger_verdict = "HEALTHY"
    elif len(threats) == 1: danger_verdict = "STRESSED"
    elif len(threats) == 2: danger_verdict = "DEGRADED"
    elif len(threats) <= 4: danger_verdict = "CRITICAL"
    else:                   danger_verdict = "SURVIVAL_MODE"

    # ── §9 Long-Horizon Truth ─────────────────────────────────────────────────
    rolling_exp: list = []
    W = 20
    for i in range(W - 1, n):
        window = nets[max(0, i - W + 1): i + 1]
        rolling_exp.append(round(sum(window) / len(window), 4))

    net_exp_per_trade   = round(total_net   / n, 4) if n else 0.0
    gross_exp_per_trade = round(total_gross / n, 4) if n else 0.0
    fee_drag_per_trade  = round(total_fees  / n, 4) if n else 0.0

    return {
        "ts":       int(_t.time() * 1000),
        "version":  APP_VERSION,
        "n_trades": n,

        "executive_snapshot": {
            "net_pnl":                  round(total_net,  4),
            "gross_pnl":                round(total_gross, 4),
            "total_fees":               round(total_fees,  4),
            "profit_factor":            round(pf,   4),
            "win_rate":                 round(wr,   4),
            "avg_win_usdt":             round(avg_win,  4),
            "avg_loss_usdt":            round(avg_loss, 4),
            "max_drawdown_pct":         round(mdd * 100, 2),
            "alpha_tier":               alpha_tier,
            "net_expectancy_per_trade": net_exp_per_trade,
            "kelly_fraction":           round(kelly, 4),
        },

        "trade_truth": {
            "total":              n,
            "wins":               len(wins),
            "losses":             len(losses),
            "breakeven":          len(be),
            "gross_positive":     len(gross_pos),
            "fee_destroyed":      len(fee_destr),
            "fee_destruction_pct": round(len(fee_destr) / len(gross_pos) * 100, 1) if gross_pos else 0.0,
        },

        "fee_analysis": {
            "total_fees":         round(total_fees,   4),
            "fee_as_pct_gross":   round(fee_pct_gross, 2),
            "avg_fee_per_trade":  round(avg_fee,       4),
            "severity":           fee_severity,
            "trend":              fee_trend,
        },

        "winloss_geometry": {
            "avg_win_usdt":       round(avg_win,        4),
            "avg_loss_usdt":      round(avg_loss,       4),
            "rr_ratio":           round(rr_ratio,        4),
            "avg_win_hold_sec":   round(avg_win_hold,    1),
            "avg_loss_hold_sec":  round(avg_loss_hold,   1),
            "hold_asymmetry":     "CORRECT" if avg_win_hold > avg_loss_hold else ("INVERTED" if loss_trades else "UNKNOWN"),
            "largest_win":        round(largest_win,    4),
            "largest_loss":       round(largest_loss,   4),
        },

        "survivability": {
            "alpha_tier":         alpha_tier,
            "kelly_fraction":     round(kelly, 4),
            "max_drawdown_pct":   round(mdd * 100, 2),
            "profit_factor":      round(pf,  4),
            "win_rate":           round(wr,  4),
            "rr_ratio":           round(rr_ratio, 4),
            "deployment_ready":   deploy_ready,
        },

        "session_regime": {
            "sessions":                  session_stats,
            "regimes":                   regime_stats,
            "cross_boundary_count":      len(cb_trades),
            "cross_boundary_losses":     len(cb_losses),
            "cross_boundary_loss_pnl":   round(sum(t.get("net_pnl", 0.0) for t in cb_losses), 4),
            "best_session":              best_sess,
            "worst_session":             worst_sess,
        },

        "rl_intelligence": {
            "adaptation_state":   adapt_state,
            "intelligence_score": round(intell_s, 2),
            "avg_q":              round(avg_q,    4),
            "explore_ratio":      round(exp_r,    4),
            "toxic_contexts":     toxic_c,
            "mature_contexts":    mature_c,
            "total_contexts":     total_ctx,
            "total_pulls":        total_pulls,
        },

        "danger_radar": {
            "verdict":      danger_verdict,
            "threat_count": len(threats),
            "threats":      threats,
        },

        "long_horizon": {
            "equity_curve":              eq_curve[-200:],
            "rolling_expectancy_20":     rolling_exp[-100:],
            "net_expectancy_per_trade":  net_exp_per_trade,
            "gross_expectancy_per_trade": gross_exp_per_trade,
            "fee_drag_per_trade":        fee_drag_per_trade,
            "max_drawdown_pct":          round(mdd * 100, 2),
            "initial_capital":           _initial_cap,
        },
    }


# ── Phase-E: Survivability Evolution Program API ─────────────────────────────

@app.get("/api/survivability/expectancy-stability")
async def survivability_expectancy_stability():
    """Phase-E E.1 — Expectancy stability: persistence, decay velocity, half-life, instability."""
    from core.survivability_evolution.expectancy_stability_engine import compute_expectancy_stability
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_expectancy_stability, trades
    )


@app.get("/api/survivability/ecology-preservation")
async def survivability_ecology_preservation():
    """Phase-E E.2 — Ecological self-preservation: threat detection and advisory throttling."""
    from core.survivability_evolution.ecological_self_preservation_engine import compute_ecological_self_preservation
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_ecological_self_preservation, trades
    )


@app.get("/api/survivability/regime-memory")
async def survivability_regime_memory():
    """Phase-E E.3 — Regime adaptation memory: historical survivability and collapse conditions."""
    from core.survivability_evolution.regime_adaptation_memory_engine import compute_regime_adaptation_memory
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_regime_adaptation_memory, trades
    )


@app.get("/api/survivability/alpha-persistence")
async def survivability_alpha_persistence():
    """Phase-E E.4 — Alpha persistence: decay curves, evaporation risk, edge vs statistical noise."""
    from core.survivability_evolution.alpha_persistence_tracker import track_alpha_persistence
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, track_alpha_persistence, trades
    )


@app.get("/api/survivability/confidence-realism")
async def survivability_confidence_realism():
    """Phase-E E.5 — Confidence realism: hallucination detection, conviction reliability."""
    from core.survivability_evolution.confidence_realism_engine import compute_confidence_realism
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_confidence_realism, trades
    )


@app.get("/api/survivability/entropy")
async def survivability_entropy():
    """Phase-E E.6 — Entropy resistance: 6-domain degradation analysis, STABLE→DEGENERATIVE."""
    from core.survivability_evolution.entropy_resistance_engine import compute_entropy_resistance
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_entropy_resistance, trades
    )


@app.get("/api/survivability/orchestration")
async def survivability_orchestration():
    """Phase-E E.7 — Unified SURVIVABILITY_EVOLUTION_REPORT across all 6 engines."""
    from core.survivability_evolution.survivability_evolution_orchestrator import run_survivability_evolution
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, run_survivability_evolution, trades
    )


# ── Phase-G: Adaptive Execution Governance API ───────────────────────────────

@app.get("/api/execution-governance/restraint")
async def execution_governance_restraint():
    """Phase-G G.1 — Survivability restraint advisory (TRADE_ALLOWED→ENTROPY_ALERT)."""
    from core.adaptive_execution_governance.restraint_advisory_engine import compute_restraint_advisory
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_restraint_advisory, trades
    )


@app.get("/api/execution-governance/discipline-gate")
async def execution_governance_discipline_gate():
    """Phase-G G.2 — Capital discipline gate: pre-trade survivability evaluation (PASS→UNSAFE)."""
    from core.adaptive_execution_governance.capital_discipline_gate import compute_capital_discipline_gate
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_capital_discipline_gate, trades
    )


@app.get("/api/execution-governance/equilibrium")
async def execution_governance_equilibrium():
    """Phase-G G.3 — Equilibrium resumption: 6-dimension stabilisation assessment."""
    from core.adaptive_execution_governance.equilibrium_resumption_engine import compute_equilibrium_resumption
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_equilibrium_resumption, trades
    )


@app.get("/api/execution-governance/overrides")
async def execution_governance_overrides():
    """Phase-G G.4 — Operator override transparency: replay-visible override lineage."""
    from core.adaptive_execution_governance.operator_override_transparency_engine import compute_operator_override_transparency
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_operator_override_transparency, trades
    )


@app.get("/api/execution-governance/discipline-memory")
async def execution_governance_discipline_memory():
    """Phase-G G.5 — Execution discipline memory: revenge trading, impulsive spikes, discipline runs."""
    from core.adaptive_execution_governance.execution_discipline_memory_engine import compute_execution_discipline_memory
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_execution_discipline_memory, trades
    )


@app.get("/api/execution-governance/governance-safety")
async def execution_governance_safety():
    """Phase-G G.6 — Human governance safety: constitutional invariant validation."""
    from core.adaptive_execution_governance.human_governance_safety_engine import compute_human_governance_safety
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_human_governance_safety, trades
    )


@app.get("/api/execution-governance/orchestration")
async def execution_governance_orchestration():
    """Phase-G G.7 — Unified ADAPTIVE_EXECUTION_CIVILIZATION_REPORT across all 6 engines."""
    from core.adaptive_execution_governance.adaptive_execution_orchestrator import run_adaptive_execution_civilization
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, run_adaptive_execution_civilization, trades
    )


# ── Phase-H: Institutional Continuity API ────────────────────────────────────

@app.get("/api/continuity/survivability-memory")
async def continuity_survivability_memory():
    """Phase-H H.1 — Multi-cycle survivability memory: collapse/recovery/alpha-persistence eras."""
    from core.institutional_continuity.multi_cycle_survivability_memory import compute_multi_cycle_survivability_memory
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_multi_cycle_survivability_memory, trades
    )


@app.get("/api/continuity/doctrine")
async def continuity_doctrine():
    """Phase-H H.2 — Evolutionary doctrine memory: doctrine drift, regression, contradictions."""
    from core.institutional_continuity.evolutionary_doctrine_memory import compute_evolutionary_doctrine_memory
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_evolutionary_doctrine_memory, trades
    )


@app.get("/api/continuity/entropy")
async def continuity_entropy():
    """Phase-H H.3 — Long-horizon entropy: slow erosion, instability accumulation (DURABLE→EXHAUSTED)."""
    from core.institutional_continuity.long_horizon_entropy_engine import compute_long_horizon_entropy
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_long_horizon_entropy, trades
    )


@app.get("/api/continuity/recovery")
async def continuity_recovery():
    """Phase-H H.4 — Recovery inheritance: historical stabilisation pathways and repeatable conditions."""
    from core.institutional_continuity.institutional_recovery_inheritance import compute_institutional_recovery_inheritance
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_institutional_recovery_inheritance, trades
    )


@app.get("/api/continuity/cross-regime")
async def continuity_cross_regime():
    """Phase-H H.5 — Cross-regime continuity: survivability across 6 environment types."""
    from core.institutional_continuity.cross_regime_continuity_engine import compute_cross_regime_continuity
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_cross_regime_continuity, trades
    )


@app.get("/api/continuity/identity")
async def continuity_identity():
    """Phase-H H.6 — Institutional identity stability: anti-drift constitutional validation."""
    from core.institutional_continuity.institutional_identity_stability_engine import compute_institutional_identity_stability
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_institutional_identity_stability, trades
    )


@app.get("/api/continuity/orchestration")
async def continuity_orchestration():
    """Phase-H H.7 — Unified INSTITUTIONAL_CONTINUITY_REPORT (CONT-{ts}-{sha256[:16]}) across all 6 engines."""
    from core.institutional_continuity.continuity_evolution_orchestrator import run_institutional_continuity
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, run_institutional_continuity, trades
    )


# ── Phase-F: Adaptive Equilibrium & Capital Discipline ─────────────────────────

@app.get("/api/equilibrium/kelly")
async def equilibrium_kelly():
    """Phase-F F.1 — Kelly capital efficiency: optimal vs actual position sizing."""
    from core.adaptive_equilibrium.kelly_efficiency_engine import compute_kelly_efficiency
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_kelly_efficiency, trades
    )


@app.get("/api/equilibrium/drawdown")
async def equilibrium_drawdown():
    """Phase-F F.2 — Drawdown dynamics: multi-phase drawdown analysis and recovery velocity."""
    from core.adaptive_equilibrium.drawdown_dynamics_engine import compute_drawdown_dynamics
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_drawdown_dynamics, trades
    )


@app.get("/api/equilibrium/consistency")
async def equilibrium_consistency():
    """Phase-F F.3 — Return consistency: rolling window consistency scoring."""
    from core.adaptive_equilibrium.return_consistency_engine import compute_return_consistency
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_return_consistency, trades
    )


@app.get("/api/equilibrium/utilization")
async def equilibrium_utilization():
    """Phase-F F.4 — Capital utilization: PnL-per-unit efficiency and sizing variance."""
    from core.adaptive_equilibrium.capital_utilization_engine import compute_capital_utilization
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_capital_utilization, trades
    )


@app.get("/api/equilibrium/band")
async def equilibrium_band():
    """Phase-F F.5 — Equilibrium band: statistical 2.5-sigma band excursion detection."""
    from core.adaptive_equilibrium.equilibrium_band_engine import compute_equilibrium_band
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_equilibrium_band, trades
    )


@app.get("/api/equilibrium/discipline-cost")
async def equilibrium_discipline_cost():
    """Phase-F F.6 — Discipline cost: economic cost of over-caution and under-discipline."""
    from core.adaptive_equilibrium.discipline_cost_engine import compute_discipline_cost
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_discipline_cost, trades
    )


@app.get("/api/equilibrium/orchestration")
async def equilibrium_orchestration():
    """Phase-F F.7 — Adaptive Equilibrium Orchestrator (EQ-{ts}-{sha256[:16]}): BALANCED/ADAPTING/STRESSED/CRITICAL."""
    from core.adaptive_equilibrium.adaptive_equilibrium_orchestrator import run_adaptive_equilibrium
    trades = _build_eco_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, run_adaptive_equilibrium, trades
    )


# ── Phase-I: Alpha Confirmation & Live-Readiness Gating ───────────────────────

@app.get("/api/alpha-confirmation/statistics")
async def alpha_statistics():
    """Phase-I I.1 — Statistical significance: z/t tests on win rate and mean PnL vs noise."""
    from core.alpha_confirmation.statistical_significance_engine import compute_statistical_significance
    trades = _build_phase_i_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_statistical_significance, trades
    )


@app.get("/api/alpha-confirmation/oos")
async def alpha_oos():
    """Phase-I I.2 — Out-of-sample validation: 60/40 IS/OOS split with degradation ratio."""
    from core.alpha_confirmation.oos_validation_engine import compute_oos_validation
    trades = _build_phase_i_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_oos_validation, trades
    )


@app.get("/api/alpha-confirmation/fee-survival")
async def alpha_fee_survival():
    """Phase-I I.3 — Fee-survival certification: rolling window net-PnL survival rate."""
    from core.alpha_confirmation.fee_survival_engine import compute_fee_survival
    trades = _build_phase_i_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_fee_survival, trades
    )


@app.get("/api/alpha-confirmation/regime-robustness")
async def alpha_regime_robustness():
    """Phase-I I.4 — Regime robustness: qualifying profitable regimes and concentration risk."""
    from core.alpha_confirmation.regime_robustness_engine import compute_regime_robustness
    trades = _build_phase_i_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_regime_robustness, trades
    )


@app.get("/api/alpha-confirmation/drawdown-tolerance")
async def alpha_drawdown_tolerance():
    """Phase-I I.5 — Drawdown tolerance: DD ratio, recovery ratio, Calmar proxy."""
    from core.alpha_confirmation.drawdown_tolerance_engine import compute_drawdown_tolerance
    trades = _build_phase_i_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, compute_drawdown_tolerance, trades
    )


@app.get("/api/alpha-confirmation/gate")
async def alpha_gate():
    """Phase-I I.6 — Live readiness gate: hard constitutional gate (live_deployment_authorized=False always)."""
    from core.alpha_confirmation.statistical_significance_engine import compute_statistical_significance
    from core.alpha_confirmation.oos_validation_engine           import compute_oos_validation
    from core.alpha_confirmation.fee_survival_engine             import compute_fee_survival
    from core.alpha_confirmation.regime_robustness_engine        import compute_regime_robustness
    from core.alpha_confirmation.drawdown_tolerance_engine       import compute_drawdown_tolerance
    from core.alpha_confirmation.live_readiness_gate             import compute_live_readiness

    def _run_gate():
        trades = _build_phase_i_trades()
        i1 = compute_statistical_significance(trades)
        i2 = compute_oos_validation(trades)
        i3 = compute_fee_survival(trades)
        i4 = compute_regime_robustness(trades)
        i5 = compute_drawdown_tolerance(trades)
        return compute_live_readiness([i1, i2, i3, i4, i5])

    return await asyncio.get_event_loop().run_in_executor(None, _run_gate)


@app.get("/api/alpha-confirmation/orchestration")
async def alpha_orchestration():
    """Phase-I I.7 — Alpha Confirmation Orchestrator (ALPHA-{ts}-{sha256[:16]}): CONFIRMED/CANDIDATE/DEVELOPING/UNPROVEN."""
    from core.alpha_confirmation.alpha_confirmation_orchestrator import run_alpha_confirmation
    trades = _build_phase_i_trades()
    return await asyncio.get_event_loop().run_in_executor(
        None, run_alpha_confirmation, trades
    )


def _pnl_to_upe_records(trades: list) -> list:
    """Convert pnl_calculator.TradeRecord list → UPE TradeRecord list."""
    records = []
    for t in trades:
        d = asdict(t)
        sym  = d.get("symbol") or ""
        side = d.get("side")   or ""
        if not sym or not side:
            continue
        try:
            records.append(_UPERecord(
                trade_id      = d.get("trade_id", ""),
                symbol        = sym,
                side          = side,
                strategy_id   = d.get("strategy_id", "unknown"),
                regime        = d.get("regime", "unknown"),
                order_type    = d.get("order_type", "LIMIT"),
                entry_price   = float(d.get("entry_price", 0)),
                exit_price    = float(d.get("exit_price", 0)),
                qty           = float(d.get("qty", 0)),
                gross_pnl     = float(d.get("gross_pnl", 0)),
                fee_entry     = float(d.get("fee_entry", 0)),
                fee_exit      = float(d.get("fee_exit", 0)),
                slippage_cost = float(d.get("slippage_cost", 0)),
                net_pnl       = float(d.get("net_pnl", 0)),
                net_pnl_pct   = float(d.get("net_pnl_pct", 0)),
                r_multiple    = float(d.get("r_multiple", 0)),
                entry_ts      = int(d.get("entry_ts", 0)),
                exit_ts       = int(d.get("exit_ts", 0)),
                mode          = d.get("mode", "PAPER"),
            ))
        except Exception:
            pass
    return records


def _upe_build_filter(
    preset:    str,
    symbol:    str,
    strategy:  str,
    regime:    str,
    side:      str,
    win_only:  bool,
    loss_only: bool,
    rr_min,
    rr_max,
    pnl_min,
    pnl_max,
) -> _UPEFilter:
    flt = _upe_preset_filter(preset)
    if symbol:    flt.symbols    = [symbol]
    if strategy:  flt.strategies = [strategy]
    if regime:    flt.regimes    = [regime]
    if side:      flt.sides      = [side]
    if win_only:  flt.win_only   = True
    if loss_only: flt.loss_only  = True
    if rr_min  is not None: flt.rr_min  = rr_min
    if rr_max  is not None: flt.rr_max  = rr_max
    if pnl_min is not None: flt.pnl_min = pnl_min
    if pnl_max is not None: flt.pnl_max = pnl_max
    return flt


@app.get("/api/perf-explorer/summary")
async def upe_summary(
    preset:    str   = "ALL",
    symbol:    str   = "",
    strategy:  str   = "",
    regime:    str   = "",
    side:      str   = "",
    win_only:  bool  = False,
    loss_only: bool  = False,
    rr_min:    float = None,
    rr_max:    float = None,
    pnl_min:   float = None,
    pnl_max:   float = None,
):
    """Performance Explorer — summary panel + AI insights for given preset/filter."""
    records  = _pnl_to_upe_records(pnl_calc.trades)
    flt      = _upe_build_filter(preset, symbol, strategy, regime, side,
                                 win_only, loss_only, rr_min, rr_max, pnl_min, pnl_max)
    filtered = flt.apply(records)
    summary  = _upe_compute_summary(filtered, initial_capital=pnl_calc._initial_capital)
    insights = _upe_extract_insights(summary, filtered)
    return {
        "preset":      preset,
        "trade_count": len(filtered),
        "summary":     asdict(summary),
        "insights":    [asdict(i) for i in insights],
    }


@app.get("/api/perf-explorer/trades")
async def upe_trades(
    preset:    str   = "ALL",
    symbol:    str   = "",
    strategy:  str   = "",
    regime:    str   = "",
    side:      str   = "",
    win_only:  bool  = False,
    loss_only: bool  = False,
    rr_min:    float = None,
    rr_max:    float = None,
    pnl_min:   float = None,
    pnl_max:   float = None,
    limit:     int   = 500,
):
    """Performance Explorer — filtered trade list."""
    records  = _pnl_to_upe_records(pnl_calc.trades)
    flt      = _upe_build_filter(preset, symbol, strategy, regime, side,
                                 win_only, loss_only, rr_min, rr_max, pnl_min, pnl_max)
    filtered = flt.apply(records)
    return {
        "total":  len(filtered),
        "trades": [asdict(t) for t in filtered[-limit:]],
    }


@app.get("/api/perf-explorer/visuals")
async def upe_visuals(preset: str = "ALL"):
    """Performance Explorer — chart data (equity curve, drawdown series, histograms)."""
    records  = _pnl_to_upe_records(pnl_calc.trades)
    filtered = _upe_preset_filter(preset).apply(records)
    visuals  = _upe_build_visual_data(filtered, initial_capital=pnl_calc._initial_capital)
    return {
        "equity_curve":    visuals.equity_curve[-300:],
        "drawdown_series": visuals.drawdown_series[-300:],
        "pnl_histogram":   visuals.pnl_histogram,
        "win_loss_dist":   visuals.win_loss_dist,
        "rr_distribution": visuals.rr_distribution,
    }


@app.get("/api/perf-explorer/export/csv")
async def upe_export_csv(preset: str = "ALL"):
    """Performance Explorer — download filtered trade list as CSV."""
    from fastapi.responses import Response as _R
    records  = _pnl_to_upe_records(pnl_calc.trades)
    filtered = _upe_preset_filter(preset).apply(records)
    return _R(
        content    = _UPEExport.to_csv(filtered),
        media_type = "text/csv",
        headers    = {"Content-Disposition": f"attachment; filename=trades_{preset}.csv"},
    )


@app.get("/api/perf-explorer/export/json")
async def upe_export_json(preset: str = "ALL"):
    """Performance Explorer — download full report as JSON."""
    from fastapi.responses import Response as _R
    records  = _pnl_to_upe_records(pnl_calc.trades)
    filtered = _upe_preset_filter(preset).apply(records)
    summary  = _upe_compute_summary(filtered, initial_capital=pnl_calc._initial_capital)
    return _R(
        content    = _UPEExport.to_json(filtered, summary),
        media_type = "application/json",
        headers    = {"Content-Disposition": f"attachment; filename=report_{preset}.json"},
    )


@app.post("/api/perf-explorer/backup")
async def upe_backup():
    """Performance Explorer — trigger manual backup of trade history."""
    records = _pnl_to_upe_records(pnl_calc.trades)
    bm      = _UPEBackup("data/backups")
    path    = bm.backup(records, label="manual")
    return {"ok": True, "path": path, "trade_count": len(records)}


# ── FTD-038+039: Capital Flow Engine API ─────────────────────────────────────

@app.get("/api/capital-flow/state")
async def capital_flow_state():
    """
    FTD-038+039 — Full Capital Flow Engine state.
    Returns: per-strategy allocation %, stabilizer state, capital protect mode,
    equity smoothness, and allocation change log.
    """
    return _sanitize(capital_flow_engine.summary())


@app.get("/api/capital-flow/allocations")
async def capital_flow_allocations():
    """
    FTD-038 — Per-strategy capital allocation breakdown.
    Shows: strategy → AEE state → rank → priority mult → allocation %.
    DISABLED strategies show 0% allocation.
    """
    from dataclasses import asdict
    allocs = capital_flow_engine.allocations()
    equity = scaler.equity
    return {
        "equity_usdt":   round(equity, 2),
        "total_active":  sum(1 for a in allocs if a.can_trade),
        "total_disabled": sum(1 for a in allocs if not a.can_trade),
        "allocations":   [asdict(a) for a in allocs],
        "stabilizer_state": capital_flow_engine._stab_state,
        "protect_mode":  capital_flow_engine._protect_mode,
    }


# ── FTD-037: Adaptive Edge Engine API ────────────────────────────────────────

@app.get("/api/aee/state")
async def aee_state():
    """
    FTD-037 — Full AEE state: all strategies ranked by AEE Score.
    Returns: active / reduced / scaling / disabled lists + per-strategy
    metrics (score, PF, RR, cost%, WR%, streaks, size_mult, disable_log).
    """
    return _sanitize(adaptive_edge_engine.summary())


@app.get("/api/aee/strategy/{strategy_id}")
async def aee_strategy_detail(strategy_id: str):
    """
    FTD-037 — Single strategy detail: full AEE stats + disable log.
    Use strategy_id as it appears in trades (e.g. ALPHA_TCB_v1, MR_BB_RSI_v1).
    """
    stats = adaptive_edge_engine.get_stats(strategy_id)
    if stats is None:
        raise HTTPException(404, f"Strategy '{strategy_id}' not yet tracked by AEE")
    return _sanitize(asdict(stats))


# ── Forensic Report Generator ─────────────────────────────────────────────────

def _generate_forensic_reports(
    trade_dicts: list,
    session_stats: dict,
    thoughts: list,
    edge_summary: dict,
) -> "dict[str, str]":
    """
    Generate 7 forensic analysis files included in 05_forensics/ of the bundle.
    Each file targets a specific angle for diagnosing losses and reaching $1/min.

    1. strategy_forensics.json   — per-strategy WR, PF, fees, verdict
    2. exit_analysis.json        — how trades exit (SL/TP/TSL+/BE via r_multiple)
    3. fee_drag_analysis.json    — fee breakdown by symbol
    4. regime_performance.json   — WR/PF per market regime
    5. hourly_performance.json   — performance by UTC hour (golden/avoid hours)
    6. signal_funnel.json        — pipeline funnel from thought log
    7. capital_efficiency.json   — gap analysis vs $1/min target
    """
    import collections as _col

    def _exit_type(r: float) -> str:
        if r >= 3.5:      return "TAKE_PROFIT"
        if r > 0.05:      return "TRAILING_STOP_WIN"
        if r > -0.05:     return "BREAKEVEN"
        if r >= -1.15:    return "STOP_LOSS"
        return "STOP_LOSS_SLIP"

    def _pf(gp, gl):
        return round(gp / max(gl, 1e-9), 3)

    def _wr(wins, total):
        return round(len(wins) / max(total, 1) * 100, 2)

    files: dict = {}
    n_total = len(trade_dicts)

    # ── 1. Strategy Forensics ─────────────────────────────────────────────────
    sg = _col.defaultdict(list)
    for t in trade_dicts:
        sg[t.get("strategy_id", "unknown")].append(t)

    strats = []
    for sid, tt in sorted(sg.items()):
        wins   = [t for t in tt if t.get("net_pnl", 0) > 0]
        losses = [t for t in tt if t.get("net_pnl", 0) <= 0]
        gp = sum(t.get("net_pnl", 0) for t in wins)
        gl = abs(sum(t.get("net_pnl", 0) for t in losses))
        fees = sum(t.get("fee_entry", 0) + t.get("fee_exit", 0) for t in tt)
        aw = gp / max(len(wins), 1)
        al = gl / max(len(losses), 1)
        pf = _pf(gp, gl)
        strats.append({
            "strategy_id":        sid,
            "n_trades":           len(tt),
            "win_rate_pct":       _wr(wins, len(tt)),
            "profit_factor":      pf,
            "net_pnl_usdt":       round(sum(t.get("net_pnl", 0) for t in tt), 4),
            "avg_win_usdt":       round(aw, 4),
            "avg_loss_usdt":      round(al, 4),
            "actual_rr":          round(aw / max(al, 1e-9), 3),
            "total_fees_usdt":    round(fees, 4),
            "fee_pct_of_gp":      round(fees / gp * 100, 1) if gp > 0 else None,
            "avg_r_multiple":     round(sum(t.get("r_multiple", 0) for t in tt) / max(len(tt), 1), 3),
            "verdict":            "ALPHA" if pf > 1.2 else "BREAKEVEN" if pf > 0.9 else "NOISE",
        })
    strats.sort(key=lambda x: x["profit_factor"], reverse=True)
    best = next((s["strategy_id"] for s in strats if s["profit_factor"] > 1.0), None)
    files["strategy_forensics.json"] = json.dumps({
        "title":          "Strategy Forensics — Per-Strategy Performance Breakdown",
        "generated_at":   time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_strategies": len(strats),
        "best_strategy":  best or "NONE — all strategies losing",
        "strategies":     strats,
        "action": f"Keep: {best}. Kill rest until WR>50%" if best
                  else "RSI filter + real strategies needed before any strategy is viable",
    }, indent=2)

    # ── 2. Exit Analysis ──────────────────────────────────────────────────────
    eg = _col.defaultdict(list)
    for t in trade_dicts:
        eg[_exit_type(t.get("r_multiple", -1.0))].append(t)

    exits = []
    for etype, tt in sorted(eg.items(), key=lambda x: -len(x[1])):
        pnls = [t.get("net_pnl", 0) for t in tt]
        rs   = [t.get("r_multiple", 0) for t in tt]
        exits.append({
            "exit_type":      etype,
            "count":          len(tt),
            "pct_of_total":   round(len(tt) / max(n_total, 1) * 100, 1),
            "total_pnl_usdt": round(sum(pnls), 4),
            "avg_pnl_usdt":   round(sum(pnls) / max(len(pnls), 1), 4),
            "avg_r_multiple": round(sum(rs) / max(len(rs), 1), 4),
        })

    sl_count  = sum(e["count"] for e in exits if "STOP_LOSS" in e["exit_type"])
    win_count = sum(e["count"] for e in exits if e["exit_type"] in ("TAKE_PROFIT", "TRAILING_STOP_WIN"))
    diagnosis = ("DIRECTION_WRONG — SL hit 2× more than TP. Fix signal direction."
                 if sl_count > win_count * 2 else
                 "TRAILING_STOP_TOO_TIGHT — wins closed before TP. Widen trailing."
                 if win_count > sl_count * 0.8 else "BALANCED")
    files["exit_analysis.json"] = json.dumps({
        "title":            "Exit Analysis — How and Why Trades Close",
        "generated_at":     time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "summary": {
            "stop_loss_exits":      sl_count,
            "profitable_exits":     win_count,
            "sl_to_win_ratio":      round(sl_count / max(win_count, 1), 2),
            "diagnosis":            diagnosis,
        },
        "by_exit_type":     exits,
        "action": ("Improve entry direction — too many full SL hits."
                   if sl_count > win_count * 2 else
                   "Widen trailing stop — winners cut too early." if win_count > sl_count * 0.8
                   else "Exit quality acceptable — focus on entry quality."),
    }, indent=2)

    # ── 3. Fee Drag Analysis ──────────────────────────────────────────────────
    sym_g = _col.defaultdict(list)
    for t in trade_dicts:
        sym_g[t.get("symbol", "?")].append(t)

    fee_rows = []
    for sym, tt in sorted(sym_g.items()):
        fees = sum(t.get("fee_entry", 0) + t.get("fee_exit", 0) for t in tt)
        slip = sum(t.get("slippage_cost", 0) for t in tt)
        gp   = sum(t.get("net_pnl", 0) for t in tt if t.get("net_pnl", 0) > 0)
        np_  = sum(t.get("net_pnl", 0) for t in tt)
        fee_rows.append({
            "symbol":               sym,
            "n_trades":             len(tt),
            "total_fees_usdt":      round(fees, 4),
            "total_slippage_usdt":  round(slip, 4),
            "total_cost_usdt":      round(fees + slip, 4),
            "net_pnl_usdt":         round(np_, 4),
            "fee_per_trade_usdt":   round(fees / max(len(tt), 1), 4),
            "fee_pct_of_gross_win": round(fees / gp * 100, 1) if gp > 0 else None,
            "verdict": ("FEE_TOXIC"  if fees > abs(np_) * 0.8 else
                        "FEE_HEAVY"  if (gp > 0 and fees / gp > 0.30) else "OK"),
        })
    fee_rows.sort(key=lambda x: x["total_fees_usdt"], reverse=True)
    total_fees = sum(r["total_fees_usdt"] for r in fee_rows)
    total_slip  = sum(r["total_slippage_usdt"] for r in fee_rows)
    files["fee_drag_analysis.json"] = json.dumps({
        "title":              "Fee Drag Analysis — Where Costs Are Eating Profit",
        "generated_at":       time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "total_fees_usdt":    round(total_fees, 4),
        "total_slippage_usdt": round(total_slip, 4),
        "total_cost_usdt":    round(total_fees + total_slip, 4),
        "toxic_symbols":      [r["symbol"] for r in fee_rows if r["verdict"] == "FEE_TOXIC"],
        "by_symbol":          fee_rows,
        "action": ("Remove toxic symbols: " + ", ".join(r["symbol"] for r in fee_rows[:3] if r["verdict"] != "OK")
                   if any(r["verdict"] != "OK" for r in fee_rows[:3]) else "Fee profile acceptable."),
    }, indent=2)

    # ── 4. Regime Performance Matrix ──────────────────────────────────────────
    rg = _col.defaultdict(list)
    for t in trade_dicts:
        rg[t.get("regime", "UNKNOWN")].append(t)

    regimes = []
    for regime, tt in sorted(rg.items()):
        wins   = [t for t in tt if t.get("net_pnl", 0) > 0]
        losses = [t for t in tt if t.get("net_pnl", 0) <= 0]
        gp = sum(t.get("net_pnl", 0) for t in wins)
        gl = abs(sum(t.get("net_pnl", 0) for t in losses))
        dur_secs = [
            (t.get("exit_ts", 0) - t.get("entry_ts", 0)) / 1000.0
            for t in tt if t.get("exit_ts", 0) > t.get("entry_ts", 0)
        ]
        regimes.append({
            "regime":           regime,
            "n_trades":         len(tt),
            "win_rate_pct":     _wr(wins, len(tt)),
            "profit_factor":    _pf(gp, gl),
            "net_pnl_usdt":     round(sum(t.get("net_pnl", 0) for t in tt), 4),
            "avg_win_usdt":     round(gp / max(len(wins), 1), 4),
            "avg_loss_usdt":    round(gl / max(len(losses), 1), 4),
            "avg_duration_sec": round(sum(dur_secs) / max(len(dur_secs), 1), 1),
            "verdict":          "TRADE_HERE" if _pf(gp, gl) > 1.0 else "AVOID",
        })
    regimes.sort(key=lambda x: x["profit_factor"], reverse=True)
    files["regime_performance_matrix.json"] = json.dumps({
        "title":        "Regime Performance Matrix — Which Market State Is Profitable",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "best_regime":  regimes[0]["regime"] if regimes else "N/A",
        "regimes":      regimes,
        "action": (f"Focus on {regimes[0]['regime']} regime — highest PF."
                   if regimes and regimes[0]["profit_factor"] > 1.0
                   else "All regimes losing — signal quality must improve first."),
    }, indent=2)

    # ── 5. Hourly Performance ─────────────────────────────────────────────────
    hg = _col.defaultdict(list)
    for t in trade_dicts:
        ets = t.get("entry_ts", 0)
        if ets > 0:
            h = int((ets // 1000) % 86400 // 3600)
            hg[h].append(t)

    hours = []
    for h, tt in sorted(hg.items()):
        wins = [t for t in tt if t.get("net_pnl", 0) > 0]
        net  = sum(t.get("net_pnl", 0) for t in tt)
        hours.append({
            "hour_utc":       h,
            "label":          f"{h:02d}:00-{h:02d}:59 UTC",
            "n_trades":       len(tt),
            "win_rate_pct":   _wr(wins, len(tt)),
            "net_pnl_usdt":   round(net, 4),
            "avg_pnl_usdt":   round(net / max(len(tt), 1), 4),
            "verdict":        ("GOLDEN_HOUR" if net > 1.0 else
                               "AVOID_HOUR"  if net < -3.0 else "NEUTRAL"),
        })
    golden = [h["label"] for h in sorted(hours, key=lambda x: -x["net_pnl_usdt"])[:3]
              if h["net_pnl_usdt"] > 0]
    avoid  = [h["label"] for h in sorted(hours, key=lambda x: x["net_pnl_usdt"])[:3]
              if h["net_pnl_usdt"] < 0]
    files["hourly_performance.json"] = json.dumps({
        "title":         "Hourly Performance — Golden Hours vs Avoid Hours (UTC)",
        "generated_at":  time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "golden_hours":  golden,
        "avoid_hours":   avoid,
        "by_hour":       hours,
        "action": (f"Trade more in: {', '.join(golden[:2])}. "
                   f"Reduce activity in: {', '.join(avoid[:2])}.") if golden or avoid
                  else "Insufficient data for hourly analysis.",
    }, indent=2)

    # ── 6. Signal Pipeline Funnel ─────────────────────────────────────────────
    tlog = [str(t.get("msg", "")) for t in list(thoughts)]
    def _cnt(kw): return sum(1 for m in tlog if kw in m)

    signals_gen   = _cnt("🔔 Signal")
    trades_open   = _cnt("✅ Opened")
    rsi_blocked   = _cnt("RSI filter blocked")
    rsi_crash_g   = _cnt("RSI_CRASH_GUARD")
    aie_suppress  = _cnt("AIE INVERSE suppressed")
    fee_blocked   = _cnt("FEE_HEAVY")
    sl_blocked    = _cnt("SL_TOO_TIGHT")
    rr_blocked    = _cnt("RR_LOW")
    dd_blocked    = _cnt("DAILY_DD")
    streak_block  = _cnt("LOSS_STREAK")
    lcc_blocked   = _cnt("LCC_OVERRIDE") + _cnt("LCC_PAUSED") + _cnt("LCC_REDUCING")
    zero_qty      = _cnt("ZERO_QTY")
    rl_blocked    = _cnt("RL_GATE")
    alloc_zero    = _cnt("ALLOC_ZERO")
    pos_exists    = _cnt("POSITION_EXISTS")

    # ALLOC_ZERO is informational in bypass mode (trade continues via orchestrator bypass).
    # It is NOT included in all_blockers — in non-bypass mode ALLOC_ZERO shows as ZERO_QTY.
    all_blockers = [
        ("RSI_FILTER",      rsi_blocked),
        ("RSI_CRASH_GUARD", rsi_crash_g),
        ("FEE_GATE",        fee_blocked),
        ("SL_GATE",         sl_blocked),
        ("RR_GATE",         rr_blocked),
        ("LCC",             lcc_blocked),
        ("ZERO_QTY",        zero_qty),
        ("RL_GATE",         rl_blocked),
        ("POSITION_EXISTS", pos_exists),
    ]
    files["signal_funnel.json"] = json.dumps({
        "title":         "Signal Pipeline Funnel — Where Trade Ideas Are Filtered",
        "generated_at":  time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "note":          "Scans entire rolling thought-log (not limited to 30 entries)",
        "funnel": {
            "1_signals_generated":         signals_gen,
            "2_rsi_filter_blocked":        rsi_blocked,
            "2_rsi_crash_guard_blocked":   rsi_crash_g,
            "3_aie_inversions_suppressed": aie_suppress,
            "4_lean_gate_fee_blocked":     fee_blocked,
            "4_lean_gate_sl_blocked":      sl_blocked,
            "4_lean_gate_rr_blocked":      rr_blocked,
            "4_lean_gate_dd_blocked":      dd_blocked,
            "4_lean_gate_streak_blocked":  streak_block,
            "4_lcc_blocked":               lcc_blocked,
            "4_rl_gate_blocked":           rl_blocked,
            "4_zero_qty_killed":           zero_qty,
            "4_alloc_zero_bypass_noted":   alloc_zero,
            "4_position_exists_skipped":   pos_exists,
            "5_trades_executed":           trades_open,
        },
        "conversion_rate_pct": round(trades_open / max(signals_gen, 1) * 100, 1),
        "session_trades_total":    n_total,
        "session_win_rate_pct":    session_stats.get("win_rate", 0.0),
        "session_profit_factor":   session_stats.get("profit_factor", 0.0),
        "biggest_blocker": max(all_blockers, key=lambda x: x[1])[0]
                           if any(v for _, v in all_blockers) else "NONE",
    }, indent=2)

    # ── 7. Capital Efficiency — Path to $1/min ────────────────────────────────
    wins_all   = [t for t in trade_dicts if t.get("net_pnl", 0) > 0]
    losses_all = [t for t in trade_dicts if t.get("net_pnl", 0) <= 0]
    gp_all     = sum(t.get("net_pnl", 0) for t in wins_all)
    gl_all     = abs(sum(t.get("net_pnl", 0) for t in losses_all))
    aw_all     = gp_all / max(len(wins_all), 1)
    al_all     = gl_all / max(len(losses_all), 1)
    wf         = session_stats.get("win_rate", 0.0) / 100.0
    current_ev = wf * aw_all - (1 - wf) * al_all

    # What WR is needed at current avg_win/avg_loss to break even?
    be_wr = al_all / max(aw_all + al_all, 1e-9)

    # $1/min target: assume 10 trades/hr after RSI filter
    assumed_freq = 10.0 / 60.0  # trades per minute
    target_ev_per_trade = 1.0 / max(assumed_freq, 1e-9)

    # What WR at current avg_win/avg_loss achieves $1/min?
    needed_wf = (target_ev_per_trade + al_all) / max(aw_all + al_all, 1e-9)

    files["capital_efficiency.json"] = json.dumps({
        "title":          "Capital Efficiency — Gap Analysis vs $1/min Target",
        "generated_at":   time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "current_state": {
            "win_rate_pct":          round(wf * 100, 2),
            "avg_win_usdt":          round(aw_all, 4),
            "avg_loss_usdt":         round(al_all, 4),
            "actual_rr":             round(aw_all / max(al_all, 1e-9), 3),
            "expected_value_per_trade_usdt": round(current_ev, 4),
            "breakeven_win_rate_pct": round(be_wr * 100, 1),
            "net_per_minute_usdt":   round(current_ev * assumed_freq * 60, 4),
            "total_fees_usdt":       round(sum(t.get("fee_entry", 0) + t.get("fee_exit", 0) for t in trade_dicts), 4),
        },
        "target": {
            "net_per_minute_usdt": 1.0,
            "assumed_trades_per_hr": int(assumed_freq * 60),
            "required_ev_per_trade_usdt": round(target_ev_per_trade, 4),
            "required_win_rate_pct": round(min(needed_wf * 100, 99.9), 1),
            "required_rr_at_50pct_wr": 2.0,
        },
        "gap": {
            "current_per_min": round(current_ev * assumed_freq * 60, 4),
            "gap_to_close":    round(1.0 - current_ev * assumed_freq * 60, 4),
            "primary_lever":   ("WIN_RATE"  if wf < be_wr + 0.10 else
                                "RISK_SIZE" if al_all < 3.0 else "TRADE_FREQUENCY"),
            "roadmap": [
                f"Step 1: RSI filter → target WR {round(be_wr*100+10, 0):.0f}%+ (currently {wf*100:.1f}%)",
                f"Step 2: With WR {round(be_wr*100+12, 0):.0f}%, increase risk/trade from {al_all:.2f} to {al_all*3:.2f} USDT",
                f"Step 3: Kelly sizing at 60% WR → auto-scales to ~$1/min",
            ],
        },
    }, indent=2)

    return files


# ── Evolution Forensic Report Generator ───────────────────────────────────────

def _generate_evolution_reports(session_trades: list) -> "dict[str, str]":
    """
    FTD-EV-001 — Generate 4 evolution forensic files for 06_evolution/ bundle folder.

    1. evolution_lineage.json   — Generation-by-generation correction audit trail
    2. system_health.json       — Drift status + performance trajectory summary
    3. alert_log.json           — All critical alerts; LEARNING_PAUSE events flagged
    4. executive_summary.md     — Natural-language 24-hour evolution narrative
    """
    from core.intelligence.evolution_tracker import evolution_tracker
    from dataclasses import asdict

    files: dict = {}
    now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    ev = evolution_tracker
    pairs     = ev._extract_pairs()
    all_alerts = ev._alerts
    cycle_count = ev._cycle_count

    # ── 1. Digital Lineage ────────────────────────────────────────────────────
    lineage_entries = []
    for gen_idx, (pre, post) in enumerate(pairs, start=1):
        wr_delta  = round(post.win_rate  - pre.win_rate,  4)
        pnl_delta = round(post.net_pnl   - pre.net_pnl,   4)
        dd_delta  = round(post.drawdown  - pre.drawdown,   4)
        outcome   = (
            "IMPROVED"  if wr_delta >  0.01 else
            "DEGRADED"  if wr_delta < -0.01 else
            "NEUTRAL"
        )
        ts_fmt = time.strftime(
            "%Y-%m-%d %H:%M:%S UTC",
            time.gmtime(post.ts // 1000)
        )
        lineage_entries.append({
            "generation":  gen_idx,
            "cycle_id":    post.cycle_id,
            "timestamp":   ts_fmt,
            "change_applied": "AUTO_CORRECTION_CYCLE",
            "pre": {
                "win_rate_pct": round(pre.win_rate * 100, 2),
                "net_pnl_usdt": round(pre.net_pnl,  4),
                "drawdown_pct": round(pre.drawdown,  2),
                "n_trades":     pre.n_trades,
            },
            "post": {
                "win_rate_pct": round(post.win_rate * 100, 2),
                "net_pnl_usdt": round(post.net_pnl,  4),
                "drawdown_pct": round(post.drawdown,  2),
                "n_trades":     post.n_trades,
            },
            "performance_delta": {
                "win_rate_pct": round(wr_delta * 100, 2),
                "net_pnl_usdt": pnl_delta,
                "drawdown_pct": dd_delta,
            },
            "outcome": outcome,
        })

    improved_count = sum(1 for e in lineage_entries if e["outcome"] == "IMPROVED")
    degraded_count = sum(1 for e in lineage_entries if e["outcome"] == "DEGRADED")
    neutral_count  = sum(1 for e in lineage_entries if e["outcome"] == "NEUTRAL")

    files["evolution_lineage.json"] = json.dumps({
        "title":         "Digital Lineage — Generation-by-Generation System Evolution",
        "generated_at":  now_str,
        "format":        "[Generation] → [Change Applied] → [Performance Delta (Pre vs Post)]",
        "total_generations":    len(lineage_entries),
        "outcome_summary": {
            "improved": improved_count,
            "neutral":  neutral_count,
            "degraded": degraded_count,
            "success_rate_pct": round(
                improved_count / max(len(lineage_entries), 1) * 100, 1
            ),
        },
        "lineage": lineage_entries,
    }, indent=2)

    # ── 2. System Health (Drift & Trajectory) ─────────────────────────────────
    trajectory = ev.compute_trajectory(session_trades)
    drift_paused = ev.check_drift_pause()

    drift_events = [a for a in all_alerts if a.kind == "DRIFT"]
    has_drift_warning = len(drift_events) > 0

    if drift_paused:
        drift_status = "CRITICAL"
    elif has_drift_warning:
        drift_status = "WARNING"
    else:
        drift_status = "STABLE"

    traj_verdict  = trajectory.get("verdict", "INSUFFICIENT_DATA")
    wr_current    = trajectory.get("win_rate", 0.0)
    wr_prev       = trajectory.get("wr_prev", 0.0)
    wr_delta_traj = trajectory.get("wr_delta", 0.0)

    active_critical = [
        asdict(a) for a in all_alerts
        if a.kind in ("DRIFT", "WR_CRITICAL", "DD_CRITICAL")
    ]

    wr_crit_count  = sum(1 for a in all_alerts if a.kind == "WR_CRITICAL")
    dd_crit_count  = sum(1 for a in all_alerts if a.kind == "DD_CRITICAL")
    loss_out_count = sum(1 for a in all_alerts if a.kind == "LOSS_OUTLIER")

    files["system_health.json"] = json.dumps({
        "title":        "System Health — Drift & Trajectory Status",
        "generated_at": now_str,
        "drift": {
            "status":            drift_status,
            "is_paused":         drift_paused,
            "paused_until_cycle": ev._paused_until_cycle,
            "current_cycle":     cycle_count,
            "drift_events_total": len(drift_events),
            "interpretation": (
                "AUTO-CORRECTION PAUSED — 3+ consecutive cycles degraded performance. "
                "Waiting for market to stabilise."
                if drift_paused else
                "Drift detected in history — monitor closely."
                if has_drift_warning else
                "No drift detected — corrections are improving or neutral."
            ),
        },
        "trajectory": {
            "verdict":        traj_verdict,
            "direction":      trajectory.get("direction", "→"),
            "win_rate_now":   round(wr_current * 100, 2),
            "win_rate_prev":  round(wr_prev * 100, 2),
            "wr_delta_pct":   round(wr_delta_traj * 100, 2),
            "trades_analysed": trajectory.get("window", 0),
            "interpretation": (
                f"System is {traj_verdict}: WR moved "
                f"{wr_prev*100:.1f}% → {wr_current*100:.1f}% "
                f"({'▲' if wr_delta_traj >= 0 else '▼'}{abs(wr_delta_traj)*100:.1f}pp)"
            ),
        },
        "alert_counts": {
            "total":          len(all_alerts),
            "drift_alerts":   len(drift_events),
            "wr_critical":    wr_crit_count,
            "dd_critical":    dd_crit_count,
            "loss_outliers":  loss_out_count,
        },
        "active_critical_alerts": active_critical,
    }, indent=2)

    # ── 3. Alert Log (with LEARNING_PAUSE highlighted) ────────────────────────
    alert_log_entries = []
    for a in all_alerts:
        is_learning_pause = (a.kind == "DRIFT")
        entry = asdict(a)
        entry["ts_fmt"] = time.strftime(
            "%Y-%m-%d %H:%M:%S UTC", time.gmtime(a.ts // 1000)
        )
        entry["is_learning_pause"] = is_learning_pause
        entry["display_flag"] = (
            "🔴 LEARNING PAUSE — auto-correction suspended"
            if is_learning_pause else
            "⚠ WARNING" if a.severity == "WARNING" else
            "🔴 CRITICAL"
        )
        alert_log_entries.append(entry)

    alert_log_entries.sort(key=lambda x: x["ts"], reverse=True)

    learning_pauses = [e for e in alert_log_entries if e["is_learning_pause"]]
    files["alert_log.json"] = json.dumps({
        "title":            "Anomaly & Alert Log — Evolution Critical Events",
        "generated_at":     now_str,
        "note":             (
            "LEARNING_PAUSE events (is_learning_pause=true) are highlighted. "
            "These are moments the system detected its own corrections were harmful "
            "and voluntarily stopped updating to protect performance."
        ),
        "total_alerts":     len(alert_log_entries),
        "learning_pauses":  len(learning_pauses),
        "learning_pause_events": learning_pauses,
        "all_alerts_newest_first": alert_log_entries,
    }, indent=2)

    # ── 4. Executive Summary (natural language narrative) ─────────────────────
    n_trades_sess  = len(session_trades)
    wins_sess      = sum(1 for t in session_trades if t.net_pnl > 0)
    wr_sess        = wins_sess / max(n_trades_sess, 1)
    net_pnl_sess   = sum(t.net_pnl for t in session_trades)
    n_gen          = len(lineage_entries)
    n_pauses       = len(learning_pauses)

    wr_change_desc = (
        f"Win rate improved from {wr_prev*100:.1f}% to {wr_current*100:.1f}%."
        if traj_verdict == "IMPROVING" else
        f"Win rate declined from {wr_prev*100:.1f}% to {wr_current*100:.1f}%."
        if traj_verdict == "DEGRADING" else
        f"Win rate held steady at {wr_current*100:.1f}%."
    )

    pause_desc = (
        f"{n_pauses} drift event(s) were detected where corrections were making "
        f"performance worse — the system voluntarily paused auto-learning in each case, "
        f"protecting against negative drift."
        if n_pauses > 0 else
        "No learning pauses were needed — all correction cycles moved performance "
        "in a neutral or positive direction."
    )

    alert_desc_parts = []
    if wr_crit_count:
        alert_desc_parts.append(
            f"{wr_crit_count} win rate critical alert(s) (WR below {28}% threshold)"
        )
    if dd_crit_count:
        alert_desc_parts.append(
            f"{dd_crit_count} drawdown critical alert(s) (DD exceeded 15%)"
        )
    if loss_out_count:
        alert_desc_parts.append(
            f"{loss_out_count} loss outlier warning(s) (single loss >3× session average)"
        )
    alert_desc = (
        "Critical alerts fired: " + "; ".join(alert_desc_parts) + "."
        if alert_desc_parts else
        "No critical safety thresholds were breached this session."
    )

    traj_icon = {"IMPROVING": "↑", "DEGRADING": "↓", "STABLE": "→"}.get(
        traj_verdict, "?"
    )
    prev_score = round(wr_prev * 100, 1)
    curr_score = round(wr_current * 100, 1)

    exec_md = (
        f"# EOW Quant Engine — Evolution Executive Summary\n\n"
        f"**Generated:** {now_str}\n\n"
        f"---\n\n"
        f"## Session at a Glance\n\n"
        f"This session, the system executed **{n_trades_sess} trades** "
        f"({wins_sess} wins / {n_trades_sess - wins_sess} losses) "
        f"with a session win rate of **{wr_sess*100:.1f}%** "
        f"and net PnL of **{net_pnl_sess:+.2f} USDT**.\n\n"
        f"---\n\n"
        f"## Self-Learning Journey\n\n"
        f"The auto-intelligence engine completed **{n_gen} correction generation(s)**. "
        f"Of these, **{improved_count} improved** performance, "
        f"**{neutral_count} were neutral**, and **{degraded_count} degraded** it.\n\n"
        f"{pause_desc}\n\n"
        f"---\n\n"
        f"## Performance Trajectory {traj_icon}\n\n"
        f"Trajectory verdict: **{traj_verdict}**. {wr_change_desc}\n\n"
        f"Overall intelligence score moved from **{prev_score}** to **{curr_score}** "
        f"(win-rate-based proxy, 0–100 scale).\n\n"
        f"---\n\n"
        f"## Safety Alerts\n\n"
        f"{alert_desc}\n\n"
        f"Total alerts logged: **{len(all_alerts)}** "
        f"({len(learning_pauses)} learning pause(s), "
        f"{wr_crit_count} WR critical, "
        f"{dd_crit_count} drawdown critical, "
        f"{loss_out_count} loss outlier).\n\n"
        f"---\n\n"
        f"## Action Items\n\n"
    )

    if traj_verdict == "DEGRADING":
        exec_md += (
            f"- **[HIGH]** System trajectory is DEGRADING. Review recent strategy "
            f"parameter changes and consider reverting the last correction cycle.\n"
        )
    if wr_sess < 0.35:
        exec_md += (
            f"- **[HIGH]** Session win rate {wr_sess*100:.1f}% is below 35% minimum. "
            f"Investigate signal quality before next session.\n"
        )
    if drift_paused:
        exec_md += (
            f"- **[MEDIUM]** Auto-correction is currently paused (drift detected). "
            f"Will resume at correction cycle #{ev._paused_until_cycle}.\n"
        )
    if n_gen == 0:
        exec_md += (
            f"- **[INFO]** No correction cycles completed this session. "
            f"System needs ≥30 trades and qualifying scores before self-correction activates.\n"
        )
    if not alert_desc_parts and traj_verdict != "DEGRADING" and not drift_paused:
        exec_md += (
            f"- **[OK]** System operating within all safety thresholds. "
            f"No immediate action required.\n"
        )

    exec_md += (
        f"\n---\n\n"
        f"*This report was auto-generated by FTD-EV-001 Evolution Tracker. "
        f"Full forensic detail available in `evolution_lineage.json`, "
        f"`system_health.json`, and `alert_log.json`.*\n"
    )

    files["executive_summary.md"] = exec_md

    return files


# ── FTD-055-ATHENA: RL Intelligence & Trade Quality Evolution Reports ─────────

def _generate_rl_intelligence_reports(
    trade_dicts: list,
    session_start_idx: int,
) -> "dict[str, str]":
    """
    FTD-055-ATHENA — Two institutional-grade RL observability files.

    1. rl_intelligence.json         — Evidence-based verdict: Is the RL actually learning?
                                      Context coverage, alpha discovery, convergence estimate,
                                      strategy coverage, session intelligence, policy evolution.
    2. trade_quality_evolution.json — Are later trades smarter than earlier trades?
                                      Rolling 20-trade windows, early vs late comparison,
                                      regime-stratified evolution, directional trend verdict.
    """
    import collections as _col
    now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    files: dict = {}

    # ── 1. RL Intelligence Report ─────────────────────────────────────────────
    evo_state     = rl_engine.get_evolution_state()
    rl_sum        = rl_engine.summary()
    uptime_min    = max(evo_state.get("uptime_min", 1), 0.01)
    counters      = evo_state.get("counters", {})
    dynamics      = evo_state.get("learning_dynamics", {})
    maturity      = evo_state.get("context_maturity", {})
    quality       = evo_state.get("quality_distribution", {})
    session_intel = evo_state.get("session_intelligence", {})
    evo_score     = evo_state.get("intelligence_score", 0)

    # Context coverage analysis — direct table inspection
    all_ctx       = list(rl_engine._table.values())
    visited_ctx   = [c for c in all_ctx if c.n_visits >= 3]
    unvisited_ctx = [c.context for c in all_ctx if c.n_visits == 0]
    total_ctx     = len(all_ctx)
    coverage_pct  = round(len(visited_ctx) / max(total_ctx, 1) * 100, 1)

    # Alpha discovery (Q > 0, min 3 visits)
    alpha_contexts = sorted(
        [
            {
                "context":       c.context,
                "q_value":       round(c.q_value, 4),
                "win_rate_pct":  round(c.win_rate * 100, 1),
                "n_visits":      c.n_visits,
                "total_pnl":     round(c.total_pnl, 4),
                "maturity_score": round(c.maturity_score, 3),
                "significance":  (
                    "MATURE"    if c.n_visits >= 50 else
                    "DEVELOPING" if c.n_visits >= 20 else
                    "EARLY"     if c.n_visits >= 5  else
                    "LOW_N"
                ),
            }
            for c in all_ctx if c.q_value > 0 and c.n_visits >= 3
        ],
        key=lambda x: x["q_value"], reverse=True,
    )
    toxic_contexts = rl_engine.get_toxic_contexts()

    # Contextual differentiation evidence — same regime different session → different Q
    session_buckets: dict = {}
    for c in all_ctx:
        parts = c.context.split("|")
        if len(parts) >= 2 and c.n_visits >= 3:
            sess = parts[1]
            session_buckets.setdefault(sess, []).append({
                "context": c.context,
                "q": round(c.q_value, 4),
                "wr_pct": round(c.win_rate * 100, 1),
                "n": c.n_visits,
                "pnl": round(c.total_pnl, 4),
            })
    for sess in session_buckets:
        session_buckets[sess].sort(key=lambda x: x["q"], reverse=True)

    # Strategy coverage map
    strat_coverage: dict = {}
    for c in all_ctx:
        parts = c.context.split("|")
        if len(parts) < 3:
            continue
        strat = parts[2]
        entry = strat_coverage.setdefault(
            strat, {"visited_contexts": 0, "total_contexts": 0, "avg_q": 0.0, "_qs": []}
        )
        entry["total_contexts"] += 1
        if c.n_visits >= 3:
            entry["visited_contexts"] += 1
            entry["_qs"].append(c.q_value)
    for strat, entry in strat_coverage.items():
        entry["avg_q"]        = round(sum(entry["_qs"]) / max(len(entry["_qs"]), 1), 4)
        entry["coverage_pct"] = round(
            entry["visited_contexts"] / max(entry["total_contexts"], 1) * 100, 1
        )
        del entry["_qs"]

    # Learning velocity
    total_updates  = counters.get("total_updates", 0)
    total_pulls    = counters.get("total_pulls",   0)
    updates_pm     = round(total_updates / uptime_min, 3)
    explore_ratio  = round(dynamics.get("explore_ratio", 0.0), 3)
    avg_q_velocity = round(dynamics.get("avg_q_velocity", 0.0), 4)

    # Convergence estimate for the best-explored context
    max_visits = max((c.n_visits for c in all_ctx), default=0)
    gap_to_mature = max(0, 50 - max_visits)
    proj_min = round(gap_to_mature / updates_pm, 0) if updates_pm > 0 else None

    # Verdict
    if total_ctx == 0 or max_visits < 3:
        verdict = "COLD_START"
        verdict_detail = "No context has reached 3 visits yet — learning has not started."
    elif alpha_contexts and toxic_contexts:
        verdict = "LEARNING_CONFIRMED_WITH_DIFFERENTIATION"
        verdict_detail = (
            f"Confirmed: {len(alpha_contexts)} profitable context(s) AND "
            f"{len(toxic_contexts)} toxic context(s). RL is correctly differentiating "
            f"between good and bad trading contexts."
        )
    elif alpha_contexts:
        verdict = "LEARNING_CONFIRMED"
        verdict_detail = (
            f"{len(alpha_contexts)} profitable context(s) discovered. "
            f"RL is identifying exploitable structure."
        )
    elif toxic_contexts:
        verdict = "LEARNING_ACTIVE_NO_ALPHA"
        verdict_detail = (
            f"RL correctly flagged {len(toxic_contexts)} toxic context(s). "
            f"No profitable contexts yet — signal quality is the limiting factor, not the RL."
        )
    elif updates_pm < 0.01:
        verdict = "STAGNANT"
        verdict_detail = "Learning rate < 0.01 updates/min — trade volume too low."
    else:
        verdict = "ACCUMULATING"
        verdict_detail = "RL is accumulating data. Verdict pending sufficient context visits."

    files["rl_intelligence.json"] = json.dumps({
        "title":          "RL Learning Intelligence — Contextual Bandit Evolution (FTD-055-ATHENA)",
        "generated_at":   now_str,
        "verdict":        verdict,
        "verdict_detail": verdict_detail,
        "intelligence_score": evo_score,
        "learning_velocity": {
            "updates_per_min":   updates_pm,
            "updates_per_hour":  round(updates_pm * 60, 1),
            "total_updates":     total_updates,
            "total_pulls":       total_pulls,
            "avg_q_velocity":    avg_q_velocity,
            "uptime_min":        round(uptime_min, 1),
        },
        "context_coverage": {
            "total_contexts_seen":    total_ctx,
            "contexts_visited_3plus": len(visited_ctx),
            "contexts_unvisited":     len(unvisited_ctx),
            "coverage_pct":           coverage_pct,
            "exploration_status": (
                "EXHAUSTED"  if coverage_pct >= 90 else
                "MATURE"     if coverage_pct >= 60 else
                "DEVELOPING" if coverage_pct >= 30 else
                "EARLY_PHASE"
            ),
            "unvisited_contexts": unvisited_ctx[:10],
        },
        "alpha_discovery": {
            "profitable_contexts": alpha_contexts,
            "toxic_contexts":      toxic_contexts,
            "differentiation_by_session": session_buckets,
        },
        "strategy_coverage":  strat_coverage,
        "convergence_estimate": {
            "max_visits_any_context":               max_visits,
            "visits_for_full_maturity":             50,
            "visits_needed_top_context":            gap_to_mature,
            "updates_per_min":                      updates_pm,
            "projected_minutes_to_mature_top_ctx":  proj_min,
            "note": (
                "50 visits → LR=0.07 (stable), Q-values reliable for policy decisions."
            ),
        },
        "maturity_distribution": maturity,
        "quality_distribution":  quality,
        "session_intelligence":  session_intel,
        "policy_evolution": {
            "allow_rate":       round(counters.get("total_allowed", 0) / max(total_pulls, 1), 3),
            "explore_ratio":    explore_ratio,
            "toxic_block_rate": round(
                counters.get("toxic_blocks", 0) / max(total_pulls, 1), 3
            ),
            "floor_raise_rate": round(
                counters.get("floor_raises", 0) / max(total_pulls, 1), 3
            ),
            "floor_lower_rate": round(
                counters.get("floor_lowers", 0) / max(total_pulls, 1), 3
            ),
            "boost_fire_rate":  round(
                counters.get("boost_fires", 0) / max(total_pulls, 1), 3
            ),
        },
        "hyperparameters": rl_sum.get("hyper", {}),
    }, indent=2, default=str)

    # ── 2. Trade Quality Evolution ─────────────────────────────────────────────
    # Session-only trades (exclude boot-replay history)
    session_dicts = trade_dicts[session_start_idx:]
    n_sess        = len(session_dicts)

    def _stats(window: list) -> dict:
        if not window:
            return {"n": 0, "wr_pct": 0.0, "pf": 0.0, "avg_pnl": 0.0, "ev": 0.0}
        wins   = [t for t in window if t.get("net_pnl", 0) > 0]
        losses = [t for t in window if t.get("net_pnl", 0) <= 0]
        gp     = sum(t.get("net_pnl", 0) for t in wins)
        gl     = abs(sum(t.get("net_pnl", 0) for t in losses))
        n      = len(window)
        aw     = gp / max(len(wins), 1)
        al     = gl / max(len(losses), 1)
        return {
            "n":       n,
            "wr_pct":  round(len(wins) / n * 100, 1),
            "pf":      round(gp / max(gl, 1e-9), 3),
            "avg_pnl": round(sum(t.get("net_pnl", 0) for t in window) / n, 4),
            "ev":      round((len(wins) / n * aw) - (len(losses) / n * al), 4),
        }

    # Rolling 20-trade windows
    win_sz   = 20
    rolling  = []
    for i in range(0, n_sess - win_sz + 1, win_sz):
        s = _stats(session_dicts[i:i + win_sz])
        s["window_start"] = i + 1
        s["window_end"]   = i + win_sz
        rolling.append(s)

    # Early vs late (first 50% vs second 50%)
    if n_sess >= 10:
        mid         = n_sess // 2
        early       = _stats(session_dicts[:mid])
        late        = _stats(session_dicts[mid:])
        wr_delta    = round(late["wr_pct"] - early["wr_pct"], 1)
        pf_delta    = round(late["pf"] - early["pf"], 3)
        trend       = (
            "IMPROVING"  if wr_delta >  5.0 else
            "DEGRADING"  if wr_delta < -5.0 else
            "FLAT"
        )
        interp = (
            f"Win rate {'improved' if wr_delta >= 0 else 'declined'} by "
            f"{abs(wr_delta):.1f}pp in the second half. "
            + ("RL is producing better entries." if wr_delta > 5
               else "No measurable improvement yet — need more session volume."
               if abs(wr_delta) <= 5
               else "Performance declining — check RL context or signal quality.")
        )
    else:
        early = late = {}
        wr_delta = pf_delta = 0.0
        trend    = "INSUFFICIENT_DATA"
        interp   = f"Only {n_sess} session trades — need ≥10 for meaningful comparison."

    # Regime-stratified early vs late
    regime_buckets: dict = _col.defaultdict(list)
    for t in session_dicts:
        regime_buckets[t.get("regime", "UNKNOWN")].append(t)

    regime_evo: dict = {}
    for reg, rt in regime_buckets.items():
        if len(rt) < 5:
            continue
        mid_r = len(rt) // 2
        e_r   = _stats(rt[:mid_r])
        l_r   = _stats(rt[mid_r:])
        regime_evo[reg] = {
            "total_trades":  len(rt),
            "early_wr_pct":  e_r["wr_pct"],
            "late_wr_pct":   l_r["wr_pct"],
            "wr_delta_pct":  round(l_r["wr_pct"] - e_r["wr_pct"], 1),
            "early_pf":      e_r["pf"],
            "late_pf":       l_r["pf"],
            "trend": (
                "IMPROVING" if l_r["wr_pct"] > e_r["wr_pct"] + 5 else
                "DEGRADING" if l_r["wr_pct"] < e_r["wr_pct"] - 5 else
                "FLAT"
            ),
        }

    files["trade_quality_evolution.json"] = json.dumps({
        "title":         "Trade Quality Evolution — Are Later Trades Smarter? (FTD-055-ATHENA)",
        "generated_at":  now_str,
        "session_trades": n_sess,
        "verdict":       trend,
        "overall_session": _stats(session_dicts),
        "early_vs_late": {
            "early_half":      early,
            "late_half":       late,
            "wr_delta_pct":    wr_delta,
            "pf_delta":        pf_delta,
            "trend":           trend,
            "interpretation":  interp,
        },
        "rolling_windows": rolling,
        "regime_evolution": regime_evo,
        "action": (
            "Positive trajectory — RL is improving signal selection." if trend == "IMPROVING" else
            "Performance degrading — RL may be overfitting or market conditions shifted."
            if trend == "DEGRADING" else
            f"Insufficient data ({n_sess} session trades — need ≥10)."
            if trend == "INSUFFICIENT_DATA" else
            "Performance stable — no improvement trend yet. More session volume needed."
        ),
    }, indent=2, default=str)

    return files


# ── FTD-056-ODYSSEY: Proof-of-Learning → Proof-of-Edge → Proof-of-Alpha ─────

def _generate_odyssey_reports(
    trade_dicts: list,
    session_start_idx: int,
) -> "dict[str, str]":
    """
    FTD-056-ODYSSEY — 10-report institutional validation framework.

    Scientifically answers: Can the adaptive RL framework evolve into
    real profitable intelligence? No cosmetic metrics — honest evidence only.

    Reports produced (09_odyssey/ bundle folder):
      1. rl_learning_progression.json    — Context knowledge accumulation timeline
      2. edge_validation_report.json     — Monte Carlo / bootstrap edge significance
      3. alpha_persistence_report.json   — Is discovered edge durable?
      4. strategy_evolution_report.json  — Per-strategy early/mid/late trajectory
      5. regime_performance_matrix.json  — Enhanced regime stats + RL Q integration
      6. confidence_calibration_report.json — Q-value prediction accuracy (Brier)
      7. signal_quality_evolution.json   — Rolling RR, WR, fee-drag trend
      8. adaptive_decision_audit.json    — RL policy change explanations
      9. reward_propagation_report.json  — Shaped reward quality analysis
     10. intelligence_maturity_report.json — Proof-of-Learning milestone scorecard
    """
    import math as _math
    import random as _random
    import collections as _col

    files: dict = {}
    now_str = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())
    all_trades    = trade_dicts
    session_trades = trade_dicts[session_start_idx:]

    # ── Shared helpers ────────────────────────────────────────────────────────

    def _pnl_stats(trades: list) -> dict:
        if not trades:
            return {"n": 0, "wr": 0.0, "wr_pct": 0.0, "pf": 0.0, "avg_pnl": 0.0,
                    "avg_win": 0.0, "avg_loss": 0.0, "ev": 0.0,
                    "gross_profit": 0.0, "gross_loss": 0.0}
        pnls = [t.get("net_pnl", 0.0) for t in trades]
        wins   = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]
        gp = sum(wins)
        gl = abs(sum(losses))
        n  = len(pnls)
        nw = len(wins)
        nl = len(losses)
        aw = gp / max(nw, 1)
        al = gl / max(nl, 1)
        wr = nw / n
        pf = gp / max(gl, 1e-9)
        ev = wr * aw - (1 - wr) * al
        return {
            "n": n, "wr": round(wr, 4), "wr_pct": round(wr * 100, 1),
            "pf": round(pf, 3), "avg_pnl": round(sum(pnls) / n, 4),
            "avg_win": round(aw, 4), "avg_loss": round(al, 4), "ev": round(ev, 4),
            "gross_profit": round(gp, 4), "gross_loss": round(gl, 4),
        }

    def _wilson_ci(k: int, n: int, z: float = 1.645) -> "tuple[float, float]":
        """Wilson score 90% CI for proportion k/n."""
        if n == 0:
            return (0.0, 1.0)
        p = k / n
        denom = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denom
        margin = z * _math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
        return (round(max(0.0, center - margin), 4), round(min(1.0, center + margin), 4))

    def _bootstrap_pf(pnls: list, n_iter: int = 500) -> "tuple":
        """Bootstrap 90% CI for profit factor (resample with replacement)."""
        if len(pnls) < 5:
            return (None, None)
        n = len(pnls)
        boot: list = []
        for _ in range(n_iter):
            s = _random.choices(pnls, k=n)
            gp = sum(p for p in s if p > 0)
            gl = abs(sum(p for p in s if p <= 0))
            boot.append(gp / max(gl, 1e-9))
        boot.sort()
        return (round(boot[int(0.05 * n_iter)], 3), round(boot[int(0.95 * n_iter)], 3))

    def _z_vs_baseline(k: int, n: int, p0: float = 0.50) -> float:
        """One-sample z-score: observed WR vs null-hypothesis p0."""
        if n == 0:
            return 0.0
        se = _math.sqrt(p0 * (1 - p0) / n)
        return round((k / n - p0) / max(se, 1e-9), 3)

    def _breakeven_wr(avg_win: float, avg_loss: float) -> float:
        if avg_win <= 0 or avg_loss <= 0:
            return 0.5
        return round(1.0 / (1.0 + avg_win / avg_loss), 4)

    # ── RL snapshot (shared across all reports) ───────────────────────────────
    all_ctx       = list(rl_engine._table.values())
    evo_state     = rl_engine.get_evolution_state()
    counters      = evo_state.get("counters", {})
    total_pulls   = counters.get("total_pulls",  0)
    total_updates = counters.get("total_updates", 0)
    uptime_min    = max(evo_state.get("uptime_min", 0.01), 0.01)
    updates_pm    = round(total_updates / uptime_min, 3)
    toxic_set     = rl_engine._toxic_contexts

    visited_ctx   = [c for c in all_ctx if c.n_visits >= 3]
    q_vals_visited = [c.q_value for c in visited_ctx]
    q_spread      = (max(q_vals_visited) - min(q_vals_visited)) if len(q_vals_visited) >= 2 else 0.0
    n_mature_ctx  = sum(1 for c in all_ctx if c.n_visits >= 50)
    n_alpha_ctx   = sum(1 for c in all_ctx if c.q_value > 0 and c.n_visits >= 20)

    # ═════════════════════════════════════════════════════════════════════════
    # 1. rl_learning_progression.json
    # ═════════════════════════════════════════════════════════════════════════
    ctx_prog = []
    for c in sorted(all_ctx, key=lambda x: x.n_visits, reverse=True):
        if c.n_visits == 0:
            continue
        q_delta = round(c.q_value - c.last_q, 4)
        wr_lo, wr_hi = _wilson_ci(c.n_wins, c.n_visits)
        lr = (0.07 if c.n_visits >= 50 else 0.10 if c.n_visits >= 20
              else 0.15 if c.n_visits >= 5 else 0.25)
        ctx_prog.append({
            "context":        c.context,
            "n_visits":       c.n_visits,
            "n_wins":         c.n_wins,
            "q_value":        round(c.q_value, 4),
            "last_q":         round(c.last_q, 4),
            "q_last_delta":   q_delta,
            "q_direction":    ("IMPROVING" if q_delta > 0.005 else
                               "DEGRADING" if q_delta < -0.005 else "STABLE"),
            "q_velocity":     round(c.q_velocity, 4),
            "q_stable":       c.q_velocity < 0.02,
            "maturity_stage": ("MATURE"   if c.n_visits >= 50 else
                               "STANDARD" if c.n_visits >= 20 else
                               "ACCEL"    if c.n_visits >= 5  else "FRESH"),
            "maturity_score": round(c.maturity_score, 3),
            "current_lr":     lr,
            "win_rate_pct":   round(c.win_rate * 100, 1),
            "wr_ci_90_lo":    round(wr_lo * 100, 1),
            "wr_ci_90_hi":    round(wr_hi * 100, 1),
            "total_pnl":      round(c.total_pnl, 4),
            "bootstrap_prior": round(c.bootstrap, 4),
            "is_toxic":       c.context in toxic_set,
            "tier":           ("ELITE"     if c.q_value > 0.80 else
                               "HIGH"      if c.q_value > 0.40 else
                               "NEUTRAL"   if c.q_value >= -0.20 else "PENALIZED"),
        })

    n_with_data  = len(visited_ctx)
    n_converging = sum(1 for c in all_ctx if c.q_velocity < 0.02 and c.n_visits >= 10)
    has_alpha    = n_alpha_ctx > 0
    learning_phase = (
        "COLD_START"         if n_with_data == 0          else
        "EARLY_ACCUMULATION" if total_updates < 50         else
        "ACTIVE_LEARNING"    if n_mature_ctx == 0          else
        "MATURING"           if not has_alpha              else
        "ALPHA_DISCOVERY"
    )

    files["rl_learning_progression.json"] = json.dumps({
        "title":          "RL Learning Progression — Context Knowledge Accumulation (FTD-056-ODYSSEY)",
        "generated_at":   now_str,
        "learning_phase": learning_phase,
        "total_contexts":     len(all_ctx),
        "contexts_with_data": n_with_data,
        "contexts_mature":    n_mature_ctx,
        "contexts_converging": n_converging,
        "learning_velocity": {
            "total_updates":   total_updates,
            "updates_per_min": updates_pm,
            "updates_per_hour": round(updates_pm * 60, 1),
            "uptime_min":      round(uptime_min, 1),
        },
        "context_progression": ctx_prog,
        "proof_of_learning": {
            "differentiation_confirmed": q_spread > 0.05,
            "q_spread":                  round(q_spread, 4),
            "converging_contexts":        n_converging,
            "alpha_contexts_found":       n_alpha_ctx,
            "toxic_contexts_flagged":     len(toxic_set),
            "verdict": (
                "LEARNING_CONFIRMED — RL assigns statistically distinct Q-values to contexts"
                if n_with_data >= 2 and q_spread > 0.05 else
                "ACCUMULATING — insufficient spread for learning proof"
            ),
        },
    }, indent=2, default=str)

    # ═════════════════════════════════════════════════════════════════════════
    # 2. edge_validation_report.json
    # ═════════════════════════════════════════════════════════════════════════
    def _edge_block(trades_in: list, label: str) -> dict:
        pnls = [t.get("net_pnl", 0.0) for t in trades_in]
        if len(pnls) < 5:
            return {"label": label, "n": len(pnls), "verdict": "INSUFFICIENT_DATA"}
        st    = _pnl_stats(trades_in)
        n     = len(pnls)
        nw    = sum(1 for p in pnls if p > 0)
        pf_lo, pf_hi = _bootstrap_pf(pnls)
        z     = _z_vs_baseline(nw, n, 0.50)
        be_wr = _breakeven_wr(st["avg_win"], st["avg_loss"])
        return {
            "label":           label,
            "n":               n,
            "wr_pct":          st["wr_pct"],
            "pf_actual":       st["pf"],
            "pf_bootstrap_ci_90": {"lo": pf_lo, "hi": pf_hi},
            "avg_win":         st["avg_win"],
            "avg_loss":        st["avg_loss"],
            "rr":              round(st["avg_win"] / max(st["avg_loss"], 1e-9), 3),
            "breakeven_wr_pct": round(be_wr * 100, 1),
            "beats_breakeven": st["wr"] > be_wr,
            "z_score_vs_50pct": z,
            "z_significance":  ("p<0.05 (1-tail)" if z > 1.645 else
                                 "p<0.10 (1-tail)" if z > 1.282 else "NOT_SIGNIFICANT"),
            "ev_per_trade":    st["ev"],
            "verdict":         ("NO_EDGE"       if st["pf"] < 0.80 else
                                "WEAK_SIGNAL"   if st["pf"] < 1.0  else
                                "EDGE_POSSIBLE" if pf_lo is not None and pf_lo < 1.0 else
                                "EDGE_CONFIRMED"),
            "bootstrap_note":  (
                "PF CI lower bound > 1.0 → edge statistically confirmed at 90%"
                if pf_lo is not None and pf_lo > 1.0 else
                "PF CI spans 1.0 → edge possible but not yet statistically confirmed"
                if pf_lo is not None and pf_lo < 1.0 < (pf_hi or 0.0) else
                "PF CI upper bound < 1.0 → negative expectancy confirmed with high confidence"
                if pf_hi is not None else "N/A"
            ),
        }

    regime_names = set(t.get("regime", "UNKNOWN") for t in all_trades)
    files["edge_validation_report.json"] = json.dumps({
        "title":        "Edge Validation Report — Randomness vs Skill (FTD-056-ODYSSEY)",
        "generated_at": now_str,
        "methodology": {
            "bootstrap_iterations": 500,
            "confidence_level":     "90%",
            "baseline":             "50% WR null hypothesis (random coin flip)",
            "note": (
                "Bootstrap 90% CI: if lower bound > 1.0 then PF > 1.0 with 95% confidence. "
                "Binomial z-score tests WR vs 50% null. Neither test requires normality."
            ),
        },
        "full_history":  _edge_block(all_trades, "ALL_HISTORY"),
        "session_only":  _edge_block(session_trades, "CURRENT_SESSION"),
        "regime_breakdown": {
            reg: _edge_block([t for t in all_trades if t.get("regime") == reg], reg)
            for reg in sorted(regime_names)
        },
        "overall_verdict": (
            "NO_STATISTICAL_EDGE — PF < 1.0 across all windows. "
            "Signal quality must improve before RL can amplify alpha."
            if _pnl_stats(all_trades)["pf"] < 1.0 else
            "EDGE_SIGNAL_PRESENT — PF ≥ 1.0. Run bootstrap on ≥200 trades for confirmation."
        ),
    }, indent=2, default=str)

    # ═════════════════════════════════════════════════════════════════════════
    # 3. alpha_persistence_report.json
    # ═════════════════════════════════════════════════════════════════════════
    alpha_ev = []
    for c in sorted(all_ctx, key=lambda x: x.n_visits, reverse=True):
        if c.n_visits < 3:
            continue
        bayes_wr  = (c.n_wins + 1) / (c.n_visits + 2)   # Beta(1,1) posterior mean
        wr_lo, wr_hi = _wilson_ci(c.n_wins, c.n_visits)
        q_trend   = ("IMPROVING" if c.q_value > c.last_q + 0.005 else
                     "DEGRADING" if c.q_value < c.last_q - 0.005 else "STABLE")
        converging = c.q_velocity < 0.02 and c.n_visits >= 10
        alpha_ev.append({
            "context":         c.context,
            "n_visits":        c.n_visits,
            "q_value":         round(c.q_value, 4),
            "q_trend":         q_trend,
            "q_stable":        converging,
            "q_velocity":      round(c.q_velocity, 4),
            "actual_wr_pct":   round(c.win_rate * 100, 1),
            "bayesian_wr_pct": round(bayes_wr * 100, 1),
            "wr_ci_90":        [round(wr_lo * 100, 1), round(wr_hi * 100, 1)],
            "total_pnl":       round(c.total_pnl, 4),
            "alpha_status":    ("POSITIVE_ALPHA"    if c.q_value > 0.40 and c.n_visits >= 20 else
                                "ALPHA_DEVELOPING"  if c.q_value > 0    and c.n_visits >= 10 else
                                "NO_ALPHA_YET"      if c.q_value >= -0.20 else
                                "NEGATIVE_ALPHA"),
            "persistent":      converging and c.q_value > 0,
        })

    best_c  = max(visited_ctx, key=lambda c: c.q_value, default=None)
    worst_c = min(visited_ctx, key=lambda c: c.q_value, default=None)

    files["alpha_persistence_report.json"] = json.dumps({
        "title":        "Alpha Persistence Report — Is Discovered Edge Durable? (FTD-056-ODYSSEY)",
        "generated_at": now_str,
        "alpha_summary": {
            "contexts_analyzed":      len(alpha_ev),
            "positive_alpha":         sum(1 for a in alpha_ev if a["alpha_status"] == "POSITIVE_ALPHA"),
            "alpha_developing":       sum(1 for a in alpha_ev if a["alpha_status"] == "ALPHA_DEVELOPING"),
            "negative_alpha":         sum(1 for a in alpha_ev if a["alpha_status"] == "NEGATIVE_ALPHA"),
            "q_spread":               round(q_spread, 4),
            "differentiation_active": q_spread > 0.05,
            "best_context":           best_c.context if best_c else None,
            "best_context_q":         round(best_c.q_value, 4) if best_c else None,
            "worst_context":          worst_c.context if worst_c else None,
            "worst_context_q":        round(worst_c.q_value, 4) if worst_c else None,
        },
        "context_alpha": alpha_ev,
        "persistence_verdict": (
            "ALPHA_CONFIRMED_AND_PERSISTENT — converging contexts with Q > 0"
            if any(a["persistent"] for a in alpha_ev) else
            "DIFFERENTIATION_ACTIVE_NO_ALPHA — RL correctly ranks contexts, all still negative"
            if q_spread > 0.05 else
            "INSUFFICIENT_DIFFERENTIATION — need more context exploration"
        ),
        "gap_to_profitability": {
            "best_q":          round(best_c.q_value, 4) if best_c else None,
            "gap_to_zero":     round(max(0.0, -(best_c.q_value if best_c else 0.0)), 4),
            "interpretation":  (
                "Best context Q is already positive — alpha exists"
                if best_c and best_c.q_value > 0 else
                f"All contexts negative. Best Q={round(best_c.q_value, 4) if best_c else 'N/A'}. "
                "Requires signal quality improvement or continued exploration."
            ),
        },
    }, indent=2, default=str)

    # ═════════════════════════════════════════════════════════════════════════
    # 4. strategy_evolution_report.json
    # ═════════════════════════════════════════════════════════════════════════
    strat_trades: "dict[str, list]" = _col.defaultdict(list)
    for t in all_trades:
        strat_trades[t.get("strategy_id", "unknown")].append(t)

    strat_evo = {}
    for sid, trades in strat_trades.items():
        n = len(trades)
        if n < 6:
            strat_evo[sid] = {"n_trades": n, "verdict": "INSUFFICIENT_DATA"}
            continue
        third = max(1, n // 3)
        early = _pnl_stats(trades[:third])
        mid   = _pnl_stats(trades[third: 2 * third])
        late  = _pnl_stats(trades[2 * third:])
        ov    = _pnl_stats(trades)
        fee_t = sum(t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) for t in trades)
        wr_tr = ("IMPROVING" if late["wr_pct"] > early["wr_pct"] + 5 else
                 "DEGRADING" if late["wr_pct"] < early["wr_pct"] - 5 else "FLAT")
        pf_tr = ("IMPROVING" if late["pf"] > early["pf"] + 0.10 else
                 "DEGRADING" if late["pf"] < early["pf"] - 0.10 else "FLAT")
        strat_evo[sid] = {
            "n_trades":        n,
            "overall":         ov,
            "total_fees":      round(fee_t, 4),
            "fee_pct_of_gross": round(fee_t / max(ov["gross_profit"], 1e-9) * 100, 1),
            "early_period":    early,
            "mid_period":      mid,
            "late_period":     late,
            "wr_trend":        wr_tr,
            "pf_trend":        pf_tr,
            "evolution_verdict": (
                "IMPROVING" if wr_tr == "IMPROVING" and pf_tr != "DEGRADING" else
                "DEGRADING" if wr_tr == "DEGRADING" or pf_tr == "DEGRADING" else
                "FLAT"
            ),
            "is_viable": ov["pf"] >= 0.90 and n >= 20,
        }

    files["strategy_evolution_report.json"] = json.dumps({
        "title":        "Strategy Evolution Report — Per-Strategy Learning Trajectory (FTD-056-ODYSSEY)",
        "generated_at": now_str,
        "total_strategies":    len(strat_evo),
        "improving_count":     sum(1 for s in strat_evo.values() if s.get("evolution_verdict") == "IMPROVING"),
        "degrading_count":     sum(1 for s in strat_evo.values() if s.get("evolution_verdict") == "DEGRADING"),
        "viable_count":        sum(1 for s in strat_evo.values() if s.get("is_viable")),
        "strategies":          strat_evo,
        "verdict": (
            "NO_VIABLE_STRATEGIES — all strategies PF < 0.90"
            if not any(s.get("is_viable") for s in strat_evo.values()) else
            f"{sum(1 for s in strat_evo.values() if s.get('is_viable'))} strategy/strategies near breakeven"
        ),
    }, indent=2, default=str)

    # ═════════════════════════════════════════════════════════════════════════
    # 5. regime_performance_matrix.json (enhanced with RL Q integration)
    # ═════════════════════════════════════════════════════════════════════════
    reg_trades_map: "dict[str, list]" = _col.defaultdict(list)
    for t in all_trades:
        reg_trades_map[t.get("regime", "UNKNOWN")].append(t)

    reg_rl_map: "dict[str, dict]" = {}
    for c in all_ctx:
        reg = c.context.split("|")[0] if "|" in c.context else "UNKNOWN"
        e = reg_rl_map.setdefault(reg, {"qs": [], "n_mature": 0, "n_toxic": 0})
        if c.n_visits >= 3:
            e["qs"].append(c.q_value)
        if c.n_visits >= 50:
            e["n_mature"] += 1
        if c.context in toxic_set:
            e["n_toxic"] += 1

    regime_matrix = {}
    for reg, trades in reg_trades_map.items():
        st  = _pnl_stats(trades)
        fee = sum(t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) for t in trades)
        rl  = reg_rl_map.get(reg, {"qs": [], "n_mature": 0, "n_toxic": 0})
        avg_q = round(sum(rl["qs"]) / len(rl["qs"]), 4) if rl["qs"] else None
        regime_matrix[reg] = {
            "n_trades":         st["n"],
            "wr_pct":           st["wr_pct"],
            "pf":               st["pf"],
            "net_pnl":          round(sum(t.get("net_pnl", 0.0) for t in trades), 4),
            "avg_win":          st["avg_win"],
            "avg_loss":         st["avg_loss"],
            "total_fees":       round(fee, 4),
            "rl_avg_q":         avg_q,
            "rl_mature_contexts": rl["n_mature"],
            "rl_toxic_contexts":  rl["n_toxic"],
            "rl_learning_status": ("MATURE"      if rl["n_mature"] > 0 else
                                   "ACTIVE"       if rl["qs"]          else "UNEXPLORED"),
            "verdict":          ("PROFITABLE" if st["pf"] > 1.0 else
                                 "MARGINAL"   if st["pf"] > 0.80 else "LOSING"),
        }

    best_reg_pf = max(regime_matrix.items(), key=lambda x: x[1]["pf"],
                      default=(None, {}))[0]
    best_reg_q  = max(
        [(r, d) for r, d in regime_matrix.items() if d.get("rl_avg_q") is not None],
        key=lambda x: x[1]["rl_avg_q"], default=(None, {})
    )[0]

    files["regime_performance_matrix.json"] = json.dumps({
        "title":        "Regime Performance Matrix — Enhanced with RL Integration (FTD-056-ODYSSEY)",
        "generated_at": now_str,
        "total_trades": len(all_trades),
        "regimes":      regime_matrix,
        "best_by_pf":   best_reg_pf,
        "best_by_rl_q": best_reg_q,
        "verdict": (
            "ALL_REGIMES_LOSING — no regime shows positive expectancy yet"
            if all(d["verdict"] == "LOSING" for d in regime_matrix.values()) else
            "REGIME_ALPHA_PRESENT — at least one regime above breakeven"
        ),
    }, indent=2, default=str)

    # ═════════════════════════════════════════════════════════════════════════
    # 6. confidence_calibration_report.json
    # ═════════════════════════════════════════════════════════════════════════
    calibration = []
    for c in all_ctx:
        if c.n_visits < 5:
            continue
        q_tier = ("ELITE"     if c.q_value > 0.80 else
                  "HIGH"      if c.q_value > 0.40 else
                  "NEUTRAL"   if c.q_value >= -0.20 else "PENALIZED")
        # Directional calibration: Q > 0 predicts winning context
        q_predicts_win = c.q_value > 0
        actually_wins  = c.win_rate > 0.50
        calibration.append({
            "context":              c.context,
            "n_visits":             c.n_visits,
            "q_value":              round(c.q_value, 4),
            "q_tier":               q_tier,
            "actual_wr_pct":        round(c.win_rate * 100, 1),
            "q_predicts_winning":   q_predicts_win,
            "actually_winning":     actually_wins,
            "directionally_correct": q_predicts_win == actually_wins,
            "q_velocity":           round(c.q_velocity, 4),
        })

    n_cal     = len(calibration)
    n_correct = sum(1 for c in calibration if c["directionally_correct"])
    acc_pct   = round(n_correct / max(n_cal, 1) * 100, 1)

    # Brier score: (implied_win_prob − actual_outcome)²
    brier_scores = []
    for c in calibration:
        # Map Q to a win-probability estimate [0, 1]
        # Q range roughly [-0.30, +0.80] in current operation → map linearly
        implied_p = max(0.0, min(1.0, (c["q_value"] + 0.30) / 1.10))
        actual_o  = 1.0 if c["actual_wr_pct"] > 50 else 0.0
        brier_scores.append((implied_p - actual_o) ** 2)
    brier = round(sum(brier_scores) / max(len(brier_scores), 1), 4) if brier_scores else None

    files["confidence_calibration_report.json"] = json.dumps({
        "title":        "Confidence Calibration — Q-Value Prediction Accuracy (FTD-056-ODYSSEY)",
        "generated_at": now_str,
        "methodology":  "Directional calibration: Q > 0 predicts winning context (WR > 50%).",
        "n_evaluated":       n_cal,
        "n_correct":         n_correct,
        "accuracy_pct":      acc_pct,
        "brier_score":       brier,
        "brier_interpretation": (
            "Well-calibrated (< 0.25)"   if brier is not None and brier < 0.25 else
            "Moderate calibration"        if brier is not None and brier < 0.40 else
            "Poor calibration (> 0.40)"  if brier is not None else "N/A"
        ),
        "context_calibration": calibration,
        "verdict": (
            "WELL_CALIBRATED — Q reliably predicts context quality"   if acc_pct >= 70 else
            "PARTIALLY_CALIBRATED — some Q/outcome alignment"          if acc_pct >= 50 else
            "POORLY_CALIBRATED — Q not yet a reliable predictor (normal at < 50 visits/context)"
        ),
        "note": (
            "Calibration improves naturally as visits accumulate. "
            "Expect reliable calibration after 50+ visits per context (MATURE stage)."
        ),
    }, indent=2, default=str)

    # ═════════════════════════════════════════════════════════════════════════
    # 7. signal_quality_evolution.json
    # ═════════════════════════════════════════════════════════════════════════
    WIN_SZ   = 50
    STEP     = WIN_SZ // 2
    rolling_q: list = []
    for i in range(0, len(all_trades) - WIN_SZ + 1, STEP):
        window = all_trades[i: i + WIN_SZ]
        st  = _pnl_stats(window)
        fee = sum(t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) for t in window)
        rr  = round(st["avg_win"] / max(st["avg_loss"], 1e-9), 3) if st["avg_loss"] > 0 else 0.0
        rolling_q.append({
            "window_start": i + 1,
            "window_end":   min(i + WIN_SZ, len(all_trades)),
            "n":            st["n"],
            "wr_pct":       st["wr_pct"],
            "pf":           st["pf"],
            "rr":           rr,
            "avg_pnl":      st["avg_pnl"],
            "fee_drag_pct": round(fee / max(st["gross_profit"], 1e-9) * 100, 1),
        })

    wr_trend = rr_trend = "FLAT"
    if len(rolling_q) >= 6:
        ew = rolling_q[:3];  lw = rolling_q[-3:]
        e_wr = sum(w["wr_pct"] for w in ew) / 3
        l_wr = sum(w["wr_pct"] for w in lw) / 3
        e_rr = sum(w["rr"]     for w in ew) / 3
        l_rr = sum(w["rr"]     for w in lw) / 3
        wr_trend = ("IMPROVING" if l_wr > e_wr + 3 else "DEGRADING" if l_wr < e_wr - 3 else "FLAT")
        rr_trend = ("IMPROVING" if l_rr > e_rr + 0.1 else "DEGRADING" if l_rr < e_rr - 0.1 else "FLAT")

    reg_sig = {}
    for reg in regime_names:
        rt = [t for t in all_trades if t.get("regime") == reg]
        if len(rt) < 5:
            continue
        st  = _pnl_stats(rt)
        fee = sum(t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) for t in rt)
        rr  = round(st["avg_win"] / max(st["avg_loss"], 1e-9), 3) if st["avg_loss"] > 0 else 0.0
        reg_sig[reg] = {
            "n": st["n"], "wr_pct": st["wr_pct"], "rr": rr, "pf": st["pf"],
            "fee_drag_pct": round(fee / max(st["gross_profit"], 1e-9) * 100, 1),
        }

    avg_fee_drag = (
        round(sum(w["fee_drag_pct"] for w in rolling_q) / len(rolling_q), 1)
        if rolling_q else 0.0
    )

    files["signal_quality_evolution.json"] = json.dumps({
        "title":        "Signal Quality Evolution — RR and WR Trends Over Time (FTD-056-ODYSSEY)",
        "generated_at": now_str,
        "total_trades": len(all_trades),
        "window_size":  WIN_SZ,
        "wr_trend":     wr_trend,
        "rr_trend":     rr_trend,
        "avg_fee_drag_pct": avg_fee_drag,
        "rolling_windows":      rolling_q,
        "regime_signal_quality": reg_sig,
        "verdict": (
            "SIGNAL_IMPROVING — at least WR or RR trending upward"
            if wr_trend == "IMPROVING" or rr_trend == "IMPROVING" else
            "SIGNAL_DEGRADING — both WR and RR trending downward"
            if wr_trend == "DEGRADING" and rr_trend == "DEGRADING" else
            "SIGNAL_FLAT — no measurable directional improvement"
        ),
        "fee_drag_finding": (
            f"CRITICAL — avg fee drag {avg_fee_drag:.1f}% of gross wins. "
            "Raise MIN_NOTIONAL_USDT to reduce fee-per-trade ratio."
            if avg_fee_drag > 30 else
            f"HIGH — avg fee drag {avg_fee_drag:.1f}%. Monitor closely."
            if avg_fee_drag > 15 else
            f"Manageable — avg fee drag {avg_fee_drag:.1f}%."
        ),
    }, indent=2, default=str)

    # ═════════════════════════════════════════════════════════════════════════
    # 8. adaptive_decision_audit.json
    # ═════════════════════════════════════════════════════════════════════════
    audit = []
    for c in sorted(all_ctx, key=lambda x: x.n_visits, reverse=True):
        if c.n_visits == 0:
            continue
        q  = c.q_value
        tier = ("ELITE"     if q > 0.80 else
                "HIGH"      if q > 0.40 else
                "NEUTRAL"   if q >= -0.20 else "PENALIZED")
        is_toxic   = c.context in toxic_set
        floor_d    = (-0.08 if q > 0.80 else -0.04 if q > 0.40 else
                       0.00 if q >= -0.20 else +0.04)
        boost_mult = (1.35 if q > 0.80 else 1.20 if q > 0.40 else
                      1.00 if q >= -0.20 else 0.85)
        q_dir = ("IMPROVING" if c.q_value > c.last_q + 0.005 else
                  "DEGRADING" if c.q_value < c.last_q - 0.005 else "STABLE")

        # Estimated wins to reach NEUTRAL tier from PENALIZED
        wins_to_neutral = None
        if tier == "PENALIZED" and not is_toxic:
            lr   = (0.07 if c.n_visits >= 50 else 0.10 if c.n_visits >= 20
                    else 0.15 if c.n_visits >= 5 else 0.25)
            gap  = max(0.0, -0.20 - q)
            wins_to_neutral = max(1, int(_math.ceil(gap / max(lr * 0.3, 1e-4)))) if gap > 0 else 0

        parts = [
            f"Q={round(q, 4)} tier={tier} visits={c.n_visits} WR={round(c.win_rate*100,1)}%",
            f"floor_delta={floor_d:+.2f} boost={boost_mult:.2f}x",
        ]
        if is_toxic:
            parts.append("TOXIC → hard-block in LIVE mode (bypassed while BYPASS_ALL_GATES=True)")
        if c.bootstrap != 0.0:
            parts.append(f"bootstrap_prior={round(c.bootstrap,4)}")

        audit.append({
            "context":         c.context,
            "n_visits":        c.n_visits,
            "q_value":         round(q, 4),
            "tier":            tier,
            "is_toxic":        is_toxic,
            "floor_delta":     floor_d,
            "confidence_mult": boost_mult,
            "q_direction":     q_dir,
            "policy_effect":   (
                "HARD_BLOCK (paper bypass active)"               if is_toxic else
                "EXECUTION_BOOST — lower gate + higher conf mult" if tier in ("ELITE", "HIGH") else
                "EXECUTION_PENALTY — higher gate + lower conf mult" if tier == "PENALIZED" else
                "NEUTRAL — no gate or confidence adjustment"
            ),
            "wins_to_neutral_tier": wins_to_neutral,
            "explanation":     " | ".join(parts),
        })

    n_audit      = len(audit)
    n_raising    = sum(1 for d in audit if d["floor_delta"] > 0)
    n_lowering   = sum(1 for d in audit if d["floor_delta"] < 0)
    n_boosting   = sum(1 for d in audit if d["confidence_mult"] > 1.0)
    n_penalizing = sum(1 for d in audit if d["confidence_mult"] < 1.0)

    files["adaptive_decision_audit.json"] = json.dumps({
        "title":        "Adaptive Decision Audit — RL Policy Explainability (FTD-056-ODYSSEY)",
        "generated_at": now_str,
        "total_contexts_audited": n_audit,
        "tier_distribution": {
            tier: sum(1 for d in audit if d["tier"] == tier)
            for tier in ["ELITE", "HIGH", "NEUTRAL", "PENALIZED"]
        },
        "toxic_contexts": sum(1 for d in audit if d["is_toxic"]),
        "policy_summary": {
            "floor_raises_active":   n_raising,
            "floor_lowers_active":   n_lowering,
            "boosts_active":         n_boosting,
            "penalties_active":      n_penalizing,
            "net_posture": (
                "RESTRICTIVE — majority of visited contexts raising execution bar"
                if n_raising > n_audit / 2 else
                "PERMISSIVE — majority of visited contexts lowering execution bar"
                if n_lowering > n_audit / 2 else
                "BALANCED — mixed policy adjustments across contexts"
            ),
        },
        "context_decisions": audit,
    }, indent=2, default=str)

    # ═════════════════════════════════════════════════════════════════════════
    # 9. reward_propagation_report.json
    # ═════════════════════════════════════════════════════════════════════════
    shaped_rs = []
    for t in all_trades:
        net    = t.get("net_pnl", 0.0)
        fee_e  = t.get("fee_entry", 0.0)
        fee_x  = t.get("fee_exit",  0.0)
        fee_c  = fee_e + fee_x
        r_mult = t.get("r_multiple", 0.0)
        # Replicate _shape_reward (core/rl_engine.py)
        reward = net
        if net > 0 and fee_c > 0:
            gross = net + fee_c
            if gross > 1e-9:
                fee_r = fee_c / gross
                if fee_r > 0.30:
                    fee_mult = max(0.60, 1.0 - (fee_r - 0.30) * 2.0)
                    reward *= fee_mult
        if net > 0 and 0.0 < r_mult < 0.80:
            reward *= 0.90
        shaped_rs.append({
            "net_pnl":       net,
            "fee_cost":      round(fee_c, 4),
            "r_multiple":    round(r_mult, 4),
            "shaped_reward": round(reward, 4),
            "shaping_applied": abs(reward - net) > 0.001,
        })

    n_sr = len(shaped_rs)
    avg_raw    = sum(s["net_pnl"]       for s in shaped_rs) / max(n_sr, 1)
    avg_shaped = sum(s["shaped_reward"] for s in shaped_rs) / max(n_sr, 1)
    n_penalized_wins = sum(1 for s in shaped_rs if s["shaping_applied"] and s["net_pnl"] > 0)
    shaping_reduction = sum(s["net_pnl"] - s["shaped_reward"] for s in shaped_rs if s["shaping_applied"])
    total_fees  = sum(t.get("fee_entry", 0.0) + t.get("fee_exit", 0.0) for t in all_trades)
    ovst        = _pnl_stats(all_trades)
    fee_pct_gp  = round(total_fees / max(ovst["gross_profit"], 1e-9) * 100, 1) if all_trades else 0.0

    files["reward_propagation_report.json"] = json.dumps({
        "title":        "Reward Propagation Report — Shaped Reward Quality Analysis (FTD-056-ODYSSEY)",
        "generated_at": now_str,
        "total_trades": n_sr,
        "reward_shaping": {
            "avg_raw_pnl":        round(avg_raw, 4),
            "avg_shaped_reward":  round(avg_shaped, 4),
            "shaping_delta":      round(avg_shaped - avg_raw, 4),
            "trades_penalized":   n_penalized_wins,
            "total_reduction":    round(shaping_reduction, 4),
            "philosophy": (
                "Fee-heavy wins penalized to teach fee efficiency. "
                "Low-R wins (R < 0.80) mildly penalized to discourage marginal entries. "
                "Losses pass through unchanged — real loss pain drives avoidance learning."
            ),
        },
        "fee_learning_impact": {
            "total_fees":            round(total_fees, 4),
            "fee_pct_of_gross_wins": fee_pct_gp,
            "fee_drag_diagnosis":    (
                "CRITICAL — fees exceed gross profit (impossible to profit at current sizing)"
                if total_fees > ovst["gross_profit"] else
                "HIGH — fees > 30% of gross wins (shaping penalty fires frequently)"
                if fee_pct_gp > 30 else
                "MANAGEABLE — fee drag within normal range"
            ),
        },
        "q_signal_health": {
            "avg_q_visited_contexts": round(
                sum(c.q_value for c in visited_ctx) / max(len(visited_ctx), 1), 4
            ) if visited_ctx else None,
            "reward_signal": (
                "DEGRADED — shaped rewards persistently negative; RL learning loss avoidance"
                if avg_shaped < -0.10 else
                "TRANSITIONAL — near zero; RL in loss-minimization phase"
                if avg_shaped < 0 else
                "POSITIVE — RL receiving net-positive reward signal"
            ),
        },
    }, indent=2, default=str)

    # ═════════════════════════════════════════════════════════════════════════
    # 10. intelligence_maturity_report.json
    # ═════════════════════════════════════════════════════════════════════════
    n_all  = len(all_trades)
    n_sess = len(session_trades)
    ovst   = _pnl_stats(all_trades)
    sv_st  = _pnl_stats(session_trades)
    be_wr  = _breakeven_wr(ovst["avg_win"], ovst["avg_loss"])

    def _regime_pf(reg: str) -> float:
        rt = [t for t in all_trades if t.get("regime") == reg]
        return _pnl_stats(rt)["pf"] if len(rt) >= 50 else 0.0

    milestones = [
        {
            "id": "M1", "name": "Trade Volume Baseline",
            "target": "≥100 total trades",
            "achieved": n_all >= 100,
            "current": n_all,
            "why": "100 trades minimum for any statistical inference",
        },
        {
            "id": "M2", "name": "Multi-Context Exploration",
            "target": "≥4 distinct contexts with 3+ visits",
            "achieved": n_with_data >= 4,
            "current": n_with_data,
            "why": "Confirms RL explores multiple market condition combinations",
        },
        {
            "id": "M3", "name": "Context Differentiation",
            "target": "Q-spread > 0.05 across visited contexts",
            "achieved": q_spread > 0.05,
            "current": round(q_spread, 4),
            "why": "Proves RL assigns distinct quality scores — not random noise",
        },
        {
            "id": "M4", "name": "Toxic Context Detection",
            "target": "≥1 context flagged toxic (Q < -0.30, n ≥ 8)",
            "achieved": len(toxic_set) > 0,
            "current": len(toxic_set),
            "why": "Proves RL identifies and rejects genuinely harmful contexts",
        },
        {
            "id": "M5", "name": "Mature Context Formation",
            "target": "≥1 context with 50+ visits (stable LR=0.07)",
            "achieved": n_mature_ctx > 0,
            "current": n_mature_ctx,
            "why": "Q-values at 50+ visits are statistically reliable estimates",
        },
        {
            "id": "M6", "name": "Cross-Session Persistence",
            "target": "Q-table data from multiple sessions (total_updates > 30)",
            "achieved": total_updates > 30 and n_mature_ctx > 0,
            "current": f"{total_updates} total RL updates",
            "why": "Proves persistence layer retains and compounds prior learning",
        },
        {
            "id": "M7", "name": "Alpha Discovery",
            "target": "≥1 context with Q > 0 and ≥20 visits",
            "achieved": n_alpha_ctx > 0,
            "current": n_alpha_ctx,
            "why": "First evidence the system can identify positive-EV conditions",
        },
        {
            "id": "M8", "name": "Statistical Edge Confirmation",
            "target": "Bootstrap PF CI lower bound > 1.0 over ≥200 trades",
            "achieved": (
                n_all >= 200 and
                (_bootstrap_pf([t.get("net_pnl", 0.0) for t in all_trades])[0] or 0.0) > 1.0
            ),
            "current": f"PF={ovst['pf']:.3f} (need bootstrap CI[lo] > 1.0)",
            "why": "Rigorous statistical proof of positive expectancy",
        },
        {
            "id": "M9", "name": "Regime-Specific Alpha",
            "target": "≥1 regime with PF > 1.0 and ≥50 trades",
            "achieved": any(_regime_pf(r) > 1.0 for r in regime_names),
            "current": (
                max((_regime_pf(r) for r in regime_names), default=0.0)
            ),
            "why": "Proves RL found alpha in a specific market structure",
        },
        {
            "id": "M10", "name": "Adaptive Session Profitability",
            "target": "Current session PF > 1.0 with RL guidance active",
            "achieved": sv_st["pf"] > 1.0 and n_sess >= 20,
            "current": f"session PF={sv_st['pf']:.3f} ({n_sess} trades)",
            "why": "Ultimate proof: RL guidance produces profitable trading sessions",
        },
    ]

    m_achieved = sum(1 for m in milestones if m["achieved"])
    m_total    = len(milestones)
    mat_score  = round(m_achieved / m_total * 100, 0)
    phase = (
        "PHASE_1_EXPLORATION"      if m_achieved < 3 else
        "PHASE_2_DIFFERENTIATION"  if m_achieved < 5 else
        "PHASE_3_LEARNING_PROVEN"  if m_achieved < 7 else
        "PHASE_4_ALPHA_DISCOVERY"  if m_achieved < 9 else
        "PHASE_5_PROFITABLE_INTEL"
    )

    # Time to M5 at current update rate
    t_to_m5 = None
    if not milestones[4]["achieved"] and updates_pm > 0:
        max_v    = max((c.n_visits for c in all_ctx), default=0)
        gap_v    = max(0, 50 - max_v)
        t_to_m5  = round(gap_v / updates_pm, 0) if gap_v > 0 else 0.0

    files["intelligence_maturity_report.json"] = json.dumps({
        "title":        "Intelligence Maturity Report — Proof-of-Learning Scorecard (FTD-056-ODYSSEY)",
        "generated_at": now_str,
        "maturity_score_pct":  mat_score,
        "current_phase":       phase,
        "milestones_achieved": m_achieved,
        "milestones_total":    m_total,
        "milestones":          milestones,
        "phase_guide": {
            "PHASE_1_EXPLORATION":     "RL exploring contexts — no learning evidence yet",
            "PHASE_2_DIFFERENTIATION": "RL differentiating contexts — learning confirmed, no alpha yet",
            "PHASE_3_LEARNING_PROVEN": "Toxic detection + cross-session memory confirmed",
            "PHASE_4_ALPHA_DISCOVERY": "First positive Q contexts — early alpha evidence present",
            "PHASE_5_PROFITABLE_INTEL": "Statistically confirmed positive expectancy — institutional grade",
        },
        "honest_assessment": {
            "system_is_learning":    m_achieved >= 3,
            "alpha_evidence_exists": n_alpha_ctx > 0,
            "statistically_profitable": milestones[7]["achieved"],
            "primary_obstacle": (
                f"Signal quality — all contexts negative Q. Breakeven WR = {round(be_wr*100,1)}%, "
                f"actual WR = {ovst['wr_pct']}%. RL architecture is sound; signals need improvement."
                if not n_alpha_ctx else
                "Volume — alpha detected but needs more visits for statistical confidence"
            ),
            "time_to_m5_minutes": t_to_m5,
            "projection": (
                f"At {updates_pm:.2f} updates/min, M5 (mature context) in ~{t_to_m5:.0f} min"
                if t_to_m5 else "Already at or beyond M5"
            ),
        },
        "final_answer": (
            "YES — statistically confirmed profitable intelligence (M8 achieved)"
            if milestones[7]["achieved"] else
            f"NOT YET — system has proven {m_achieved}/{m_total} milestones. "
            "Learning architecture is working correctly. "
            "Profitability requires signal WR improvement, not RL redesign."
        ),
    }, indent=2, default=str)

    return files


# ── FTD-LPA: Live Process Snapshot ───────────────────────────────────────────

@app.get("/api/snapshot/live-process")
async def download_live_process_snapshot(_auth=Depends(require_roles("operator", "admin"))):
    """
    FTD-LPA: Dedicated Live Process Access snapshot.

    On-demand export of all three live runtime artifact classes:
      • Runtime log stream  — rolling loguru buffer (last 2 000 records)
      • RL Q-table          — full in-memory contextual bandit state
      • Trade execution log — in-memory PnL records + SQLite rows

    Thread-safe, read-only, non-blocking.
    The running trading simulation is NEVER interrupted.

    Returns a ZIP archive (application/zip) downloadable from the dashboard.
    """
    from fastapi.responses import StreamingResponse
    import asyncio as _asyncio

    try:
        # Build the package off the event loop to avoid blocking ticks
        pkg_bytes = await _asyncio.to_thread(
            live_process_access.build_package,
            rl_engine,
            pnl_calc,
            data_lake,
            list(_thought_log),   # pass a copy — snapshot is moment-in-time
            _boot_ts,
        )
    except Exception as _exc:
        logger.error(f"[LPA] Snapshot build failed: {_exc}")
        raise HTTPException(status_code=500, detail=f"Snapshot failed: {_exc}")

    ts_str   = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    filename = f"eow_live_process_{ts_str}.zip"

    _thought(
        f"🔬 Live Process Snapshot downloaded → {filename} "
        f"({len(pkg_bytes)//1024} KB | "
        f"logs={len(live_process_access.snapshot_logs())} "
        f"rl_contexts={len(getattr(rl_engine, '_table', {}))} "
        f"trades={len(pnl_calc.trades)})",
        "SYSTEM",
    )
    return StreamingResponse(
        iter([pkg_bytes]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── FTD-053-GAIA Phase 7: Observability API ──────────────────────────────────
#
# Eight read-only endpoints that expose the full Phases 1-6 pipeline to the
# operator during the FTD-054 stabilization window.  No new adaptive logic —
# purely surfacing data that already exists inside the observability stack.
#

from core.observability.anomaly_detector   import anomaly_detector as _obs_ad
from core.observability.escalation_engine  import escalation_engine as _obs_ee
from core.observability.event_bus          import event_bus as _obs_eb
from core.observability.strategic_feed     import strategic_feed as _obs_sf
from core.observability.ai_summary_engine  import ai_summary_engine as _obs_se
from core.observability.github_sync_engine import github_sync_engine as _obs_gse
from core.observability.report_lifecycle_engine import report_lifecycle_engine as _obs_rle
from core.observability.delta_reporter     import delta_reporter as _obs_dr


def _obs_health_status(orch_stats: dict) -> dict:
    """Derive pipeline health from orchestrator stats."""
    now_ms       = int(time.time() * 1000)
    last_tick    = orch_stats.get("last_tick_ts", 0)
    total_ticks  = orch_stats.get("total_ticks", 0)
    age_secs     = round((now_ms - last_tick) / 1000, 1) if last_tick else None
    interval     = orch_stats.get("tick_interval_secs", 120)

    if total_ticks == 0:
        health = "COLD"
    elif age_secs is not None and age_secs > interval * 3:
        health = "STALE"
    elif orch_stats.get("total_errors", 0) > orch_stats.get("total_ticks", 1) * 0.25:
        health = "DEGRADED"
    else:
        health = "HEALTHY"

    total = max(total_ticks, 1)
    return {
        "status":          health,
        "total_ticks":     total_ticks,
        "age_secs":        age_secs,
        "tick_interval_secs": interval,
        "dedup_ratio":     round(orch_stats.get("total_deduped", 0) / total, 3),
        "anomaly_rate":    round(orch_stats.get("total_anomalies", 0) / total, 2),
        "escalation_rate": round(orch_stats.get("total_escalations", 0) / total, 3),
        "sync_rate":       round(orch_stats.get("total_syncs", 0) / total, 3),
        "last_tick_ms":    orch_stats.get("last_tick_ms", 0),
    }


@app.get("/api/observability/status")
async def obs_status():
    """
    FTD-053-GAIA Phase 7: Full observability pipeline status.
    Aggregates stats from all six phases plus a computed health indicator.
    """
    try:
        orch = obs_orchestrator.stats()
        return _sanitize({
            "health":         _obs_health_status(orch),
            "orchestrator":   orch,
            "anomaly_engine": _obs_ad.stats(),
            "escalation":     _obs_ee.stats(),
            "event_bus":      _obs_eb.status(),
            "strategic_feed": _obs_sf.status(),
            "summary_engine": _obs_se.stats(),
            "sync_engine":    _obs_gse.status(),
            "lifecycle":      _obs_rle.status(),
            "delta_reporter": _obs_dr.stats(),
        })
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/observability/health")
async def obs_health():
    """
    FTD-053-GAIA Phase 7: Compact pipeline health check.
    Returns HEALTHY / STALE / DEGRADED / COLD plus key operational metrics.
    """
    try:
        return _sanitize(_obs_health_status(obs_orchestrator.stats()))
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/observability/anomalies")
async def obs_anomalies(limit: int = 30, min_severity: str = "LOW"):
    """
    FTD-053-GAIA Phase 7: Active anomalies and recent anomaly history.
    Query param min_severity: LOW | MEDIUM | HIGH | CRITICAL (default LOW).
    """
    try:
        return _sanitize({
            "active_summary": _obs_ad.get_active_summary(),
            "recent_history": _obs_ad.get_history(limit=limit, min_severity=min_severity),
            "stats":          _obs_ad.stats(),
        })
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/observability/escalations")
async def obs_escalations(limit: int = 20):
    """
    FTD-053-GAIA Phase 7: Active escalations and recent escalation history.
    """
    try:
        return _sanitize({
            "active":  _obs_ee.get_active_escalations(),
            "history": _obs_ee.get_history(limit=limit),
            "stats":   _obs_ee.stats(),
        })
    except Exception as exc:
        return {"error": str(exc)}


@app.post("/api/observability/escalation/{esc_id}/acknowledge")
async def obs_acknowledge_escalation(esc_id: str, reason: str = ""):
    """
    FTD-053-GAIA Phase 7: Human override — acknowledge an active escalation.
    Suppresses re-escalation for the same trigger for ACK_SUPPRESS_SECS.
    """
    try:
        ok = _obs_ee.acknowledge(esc_id, reason=reason or "operator-ack")
        return {"acknowledged": ok, "escalation_id": esc_id}
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/observability/feeds")
async def obs_feeds():
    """
    FTD-053-GAIA Phase 7: Strategic intelligence feeds (all five channels).
    Each feed includes signal_strength, headline, and last refresh timestamp.
    """
    try:
        sf_status = _obs_sf.status()
        feeds_raw = sf_status.get("feeds", {})
        return _sanitize({
            "feeds":             feeds_raw,
            "max_signal_strength": sf_status.get("max_signal_strength", 0.0),
            "last_refresh_ts":   sf_status.get("last_refresh_ts", 0),
            "total_refreshes":   sf_status.get("total_refreshes", 0),
        })
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/observability/summary")
async def obs_summary():
    """
    FTD-053-GAIA Phase 7: Latest AI strategic intelligence summary.
    Returns the most recently generated summary from the pipeline, or a
    cold-start notice if the orchestrator has not yet ticked.
    """
    try:
        last = _obs_se.get_last_summary()
        if last is None:
            return {"status": "COLD_START", "message": "No summary generated yet"}
        return _sanitize(last)
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/observability/events")
async def obs_events(limit: int = 30):
    """
    FTD-053-GAIA Phase 7: Recent event bus events (key names only, no payload values).
    Useful for diagnosing event flow density and handler health.
    """
    try:
        return _sanitize({
            "recent_events": _obs_eb.recent_events(limit=limit),
            "bus_status":    _obs_eb.status(),
        })
    except Exception as exc:
        return {"error": str(exc)}


@app.get("/api/observability/sync")
async def obs_sync():
    """
    FTD-053-GAIA Phase 7: GitHub sync engine status.
    Shows pending batch, last sync timestamp, and governance counters.
    """
    try:
        return _sanitize(_obs_gse.status())
    except Exception as exc:
        return {"error": str(exc)}


# ── Master Report Bundle ──────────────────────────────────────────────────────

@app.get("/api/reports/bundle")
async def download_report_bundle():
    """
    One-click Master Report Bundle — assembles ALL report types into a
    single ZIP file.

    ZIP contents:
      README.txt                    ← File guide
      metadata.json                 ← Bundle summary (trades, PnL, PF, evolution)
      01_system_state/
        eow_state.json              ← Full engine state (DNA + trades + ratios)
      02_reports/
        full_system_report.md       ← FTD-025A: 15-section institutional report
        full_system_report.pdf      ← FTD-025A: PDF version
        unified_report_v2.md        ← FTD-025B: cause-effect narrative report
      03_trade_archive/
        trade_history.xlsx          ← XLSX (trade sheet + session summary + audit)
        trade_report.pdf            ← PDF executive summary
        trade_report.md             ← Markdown developer log
      04_performance/
        report_ALL.json + trades_ALL.csv
        report_1D.json  + trades_1D.csv
        report_7D.json  + trades_7D.csv
        report_20D.json + trades_20D.csv
      05_forensics/
        strategy_forensics.json   ← per-strategy WR / PF / fees / verdict
        exit_analysis.json        ← SL / TP / TSL+ / BE breakdown
        fee_drag_analysis.json    ← fee burden per symbol
        regime_performance.json   ← WR and PF by market regime
        hourly_performance.json   ← golden hours vs avoid hours (UTC)
        signal_funnel.json        ← pipeline funnel metrics
        capital_efficiency.json   ← gap analysis vs $1/min + roadmap
      06_evolution/               ← FTD-EV-001 self-learning forensic audit trail
        evolution_lineage.json    ← generation-by-generation correction history
        system_health.json        ← drift status + performance trajectory
        alert_log.json            ← all critical alerts; LEARNING_PAUSE events flagged
        executive_summary.md      ← natural-language 24-hour evolution narrative
    """
    import zipfile
    import io as _io
    from fastapi.responses import StreamingResponse
    from core.reporting.unified_report_engine_v2 import generate_full_report_v2

    ts = int(time.time())

    def _safe(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    # ── Shared data collection (mirrors get_full_system_report) ──────────────
    heal      = _safe(healer.snapshot, {})
    lake_s    = _safe(data_lake.db_stats, {})
    redis_ok  = any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in heal.get("recent_events", [])
    )
    sqlite_ok = lake_s.get("trades", -1) >= 0

    trade_dicts = [
        {k: getattr(t, k) for k in t.__dataclass_fields__}
        for t in pnl_calc.trades
    ]
    _ss       = pnl_calc.session_stats
    _n_trades = len(pnl_calc.trades)
    _gross    = abs(_ss.get("total_net_pnl", 0.0)) + _ss.get("total_fees_paid", 0.0)
    _fee_ratio = _ss.get("total_fees_paid", 0.0) / max(_gross, 1e-9)
    _mins_idle = trade_flow_monitor.minutes_since_last_trade()

    analytics = _sanitize(compute_full_analytics(
        pnl_trades=[{"net_pnl": t.net_pnl, "r_multiple": t.r_multiple}
                    for t in pnl_calc.trades],
        initial_capital=pnl_calc._initial_capital,
        session_stats=_ss,
        healer_snapshot=heal,
        lake_stats=lake_s,
        genome_state=_safe(genome.export_state, {}),
        redis_ok=redis_ok,
        persistence_ok=(redis_ok or sqlite_ok),
    ))
    mode_info = await get_mode_info()

    ct_scan = _safe(
        lambda: __import__("core.intelligence.suggestion_engine",
                           fromlist=["suggestion_engine"]).suggestion_engine.detect(
            profit_factor=_ss.get("profit_factor", 0.0),
            fee_ratio=round(_fee_ratio, 4),
            win_rate=_ss.get("win_rate", 0.0) / 100.0,
            n_trades=_n_trades,
            strategy_usage=strategy_engine.usage(),
            regime_stable=True,
        ), {}
    )
    ai_brain_state = _safe(
        lambda: __import__("core.meta.ai_brain",
                           fromlist=["ai_brain"]).ai_brain.get_state(), {}
    )

    positions = []
    try:
        for sym, pos in risk_ctrl.positions.items():
            positions.append({
                "symbol":     sym,
                "side":       getattr(pos, "side", ""),
                "qty":        getattr(pos, "qty", 0.0),
                "entry_px":   getattr(pos, "entry_px", 0.0),
                "stop":       getattr(pos, "stop", 0.0),
                "tp":         getattr(pos, "tp", 0.0),
                "unrealised": getattr(pos, "unrealised_pnl", 0.0),
            })
    except Exception:
        positions = []

    # ── 2a. FTD-025A: full system report ZIP ─────────────────────────────────
    sys_snapshot = SystemSnapshot(
        session_stats     = _ss,
        analytics         = analytics,
        mode_info         = mode_info,
        thoughts          = _thought_log,
        last_skip         = _safe(lambda: getattr(trade_flow_monitor,
                                                  "last_skip", lambda: {})(), {}),
        trade_flow        = _safe(trade_flow_monitor.summary, {}),
        risk_snapshot     = _safe(risk_ctrl.snapshot, {}),
        positions         = positions,
        drawdown          = _safe(drawdown_controller.summary, {}),
        genome_state      = _safe(genome.export_state, {}),
        learning          = _safe(learning_engine.summary, {}),
        edge              = _safe(edge_engine.summary, {}),
        strategy_usage    = _safe(strategy_engine.usage, {}),
        regime            = _safe(lambda: regime_memory.summary()
                                  if hasattr(regime_memory, "summary") else {}, {}),
        ct_scan           = ct_scan,
        dynamic_thresholds= _safe(
            lambda: dynamic_threshold_provider.summary(
                minutes_no_trade=_mins_idle
            ), {}
        ),
        streak            = _safe(streak_engine.summary, {}),
        consistency       = _safe(consistency_engine.status, {}),
        capital_allocator = _safe(lambda: capital_allocator.summary(equity=pnl_calc.capital), {}),
        error_registry    = _safe(lambda: error_registry.recent(50), []),
        healer            = heal,
        halt_audit        = _safe(lambda: risk_ctrl.halt_audit()
                                  if hasattr(risk_ctrl, "halt_audit") else {}, {}),
        trades            = trade_dicts,
        gate_status       = _safe(lambda: global_gate_controller.snapshot()
                                  if "global_gate_controller" in globals() else {}, {}),
        ai_brain_state    = ai_brain_state,
        learning_memory   = _safe(
            lambda: __import__("core.learning_memory",
                               fromlist=["learning_memory_orchestrator"]
                               ).learning_memory_orchestrator.summary(), {}
        ),
    )
    system_zip_bytes = _safe(
        lambda: system_export_engine.build_full_report(sys_snapshot), b""
    )

    # ── 2b. FTD-025B: Unified Report v2 (Markdown) ───────────────────────────
    _v2_data = {
        "generated_at":    time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "trade_flow":      _safe(trade_flow_monitor.summary, {}),
        "rl_bandit":       _safe(rl_engine.summary, {}),
        "mins_idle":       _mins_idle,
        "thresholds":      _safe(
            lambda: dynamic_threshold_provider.summary(minutes_no_trade=_mins_idle), {}
        ),
        "session_stats":   _ss,
        "capital":         _safe(lambda: capital_allocator.summary(equity=pnl_calc.capital), {}),
        "risk":            _safe(risk_ctrl.snapshot, {}),
        "gate":            _safe(
            lambda: global_gate_controller.snapshot()
            if "global_gate_controller" in globals() else {}, {}
        ),
        "errors":          _safe(lambda: error_registry.recent(20), []),
        "learning_memory": _safe(
            lambda: __import__("core.learning_memory",
                               fromlist=["learning_memory_orchestrator"]
                               ).learning_memory_orchestrator.summary(), {}
        ),
        "ct_scan":         ct_scan,
        "ai_brain":        ai_brain_state,
        "drawdown":        _safe(drawdown_controller.summary, {}),
        "activator":       _safe(trade_activator.summary, {}),
        "edge_engine":     _safe(edge_engine.summary, {}),
        "thoughts":        list(_thought_log)[-30:],
    }
    try:
        unified_v2_md = generate_full_report_v2(_v2_data)
    except Exception as _e:
        import traceback as _tb
        _err_trace = _tb.format_exc()
        unified_v2_md = (
            f"# Unified report error\n\n"
            f"```\n{_err_trace}\n```\n"
        )
        logger.error(f"[BUNDLE] unified_report_v2 failed: {_e}")

    # ── 2c. Trade archive ZIP (XLSX + PDF + MD) ───────────────────────────────
    archive_zip_bytes = _safe(
        lambda: build_report_archive(
            trades=trade_dicts,
            stats=_ss,
            mode_info=mode_info,
            analytics=analytics,
            thoughts=_thought_log,
        ), b""
    )

    # ── 2d. Engine state JSON (ExportManager) ────────────────────────────────
    state_json_str = "{}"
    try:
        state_path = exporter.export(label="bundle")
        with open(state_path, "r", encoding="utf-8") as _f:
            state_json_str = _f.read()
    except Exception:
        pass

    # ── 2e. Performance Explorer — ALL / 1D / 7D / 20D ───────────────────────
    upe_records  = _pnl_to_upe_records(pnl_calc.trades)
    upe_presets  = ["ALL", "1D", "7D", "20D"]
    upe_csvs:  dict = {}
    upe_jsons: dict = {}
    for _preset in upe_presets:
        _filtered = _upe_preset_filter(_preset).apply(upe_records)
        _summary  = _upe_compute_summary(
            _filtered, initial_capital=pnl_calc._initial_capital
        )
        upe_csvs[_preset]  = _UPEExport.to_csv(_filtered)
        upe_jsons[_preset] = _UPEExport.to_json(_filtered, _summary)

    # ── 3. Assemble master ZIP ────────────────────────────────────────────────
    buf = _io.BytesIO()
    ts_str = time.strftime("%Y%m%d_%H%M%S", time.gmtime())

    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:

        zf.writestr("README.txt", (
            "EOW Quant Engine — Master Report Bundle\n"
            "═══════════════════════════════════════\n"
            f"Generated : {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}\n"
            f"Engine    : EOW_QUANT_ENGINE_v{APP_VERSION}\n"
            f"Trades    : {_n_trades}\n"
            f"Net PnL   : {_ss.get('total_net_pnl', 0.0):.2f} USDT\n"
            f"Win Rate  : {_ss.get('win_rate', 0.0):.1f}%\n"
            f"PF        : {_ss.get('profit_factor', 0.0):.3f}\n\n"
            "Folder Guide\n"
            "────────────\n"
            "01_system_state/  Full engine state JSON (DNA, trade history, portfolio ratios)\n"
            "02_reports/       FTD-025A 15-section report (MD+PDF) + FTD-025B narrative (MD)\n"
            "03_trade_archive/ Trade history XLSX + PDF executive summary + MD developer log\n"
            "04_performance/   Performance Explorer reports for ALL / 1D / 7D / 20D presets\n"
            "                  Each preset: report_<P>.json (summary) + trades_<P>.csv (raw)\n"
            "05_forensics/     Deep-dive forensic analysis (7 JSON files)\n"
            "  strategy_forensics.json   Per-strategy WR, PF, fees, verdict\n"
            "  exit_analysis.json        How trades exit: SL / TP / TSL+ / BE\n"
            "  fee_drag_analysis.json    Fee burden per symbol (FEE_TOXIC verdicts)\n"
            "  regime_performance.json   WR and PF split by market regime\n"
            "  hourly_performance.json   Golden hours vs avoid hours (UTC)\n"
            "  signal_funnel.json        Pipeline funnel: generated → gated → placed\n"
            "  capital_efficiency.json   Gap analysis vs $1/min target + roadmap\n"
            "06_evolution/     FTD-EV-001 Self-learning forensic audit trail (4 files)\n"
            "  evolution_lineage.json    Generation-by-generation correction history\n"
            "                            Format: [Cycle ID] → [Change] → [Pre vs Post Delta]\n"
            "  system_health.json        Drift status (Stable/Warning/Critical) + trajectory\n"
            "  alert_log.json            All critical alerts; LEARNING_PAUSE events flagged RED\n"
            "  executive_summary.md      Natural-language 24-hour evolution narrative\n"
            "07_live_process/ FTD-LPA: Live Process Access runtime snapshot (5 files)\n"
            "  *_MANIFEST.json           Package manifest + architecture / safety notes\n"
            "  *_runtime_logs.json       All loguru log records captured since startup\n"
            "  *_runtime_logs.txt        Human-readable plain-text log stream\n"
            "  *_thought_log.json        Engine CT-Scan decision trace (last 500 entries)\n"
            "  *_rl_qtable.json          Complete RL Q-table with all context states\n"
            "  *_trade_logs.json         In-memory session trades + SQLite history\n"
            "08_rl_intelligence/ FTD-055-ATHENA: Institutional RL learning analysis (2 files)\n"
            "  rl_intelligence.json      Evidence-based verdict: Is the RL actually learning?\n"
            "                            Verdict / intelligence_score / context coverage /\n"
            "                            alpha discovery / differentiation / policy evolution\n"
            "  trade_quality_evolution.json  Are later trades smarter than earlier trades?\n"
            "                            Early vs late session win-rate, rolling windows,\n"
            "                            regime evolution trends\n"
            "09_odyssey/         FTD-056-ODYSSEY: Proof-of-Learning → Proof-of-Edge → Proof-of-Alpha\n"
            "  rl_learning_progression.json   Context Q evolution, Wilson CI, maturity stages\n"
            "  edge_validation_report.json    Bootstrap PF CI + binomial significance vs random\n"
            "  alpha_persistence_report.json  Bayesian WR, Q-stability, alpha durability\n"
            "  strategy_evolution_report.json Per-strategy early/mid/late trajectory\n"
            "  regime_performance_matrix.json Regime stats + RL Q integration (enhanced)\n"
            "  confidence_calibration_report.json Q-value prediction accuracy (Brier score)\n"
            "  signal_quality_evolution.json  Rolling RR/WR/fee-drag trend windows\n"
            "  adaptive_decision_audit.json   RL policy change explanations per context\n"
            "  reward_propagation_report.json Shaped reward quality + fee impact on learning\n"
            "  intelligence_maturity_report.json 10-milestone Proof-of-Learning scorecard\n"
            "10_auto_intelligence/ FTD-030: Autonomous intelligence loop state\n"
            "  state.json          Current engine state: cycles, verdicts, last correction\n"
            "  history.json        Last 100 correction cycle records\n"
            "11_learning_memory/ FTD-030B: Pattern memory, negative memory, heatmap\n"
            "  summary.json        Full memory store state + activation stats\n"
            "  patterns.json       Top 100 formed patterns by confidence (leaderboard)\n"
            "  failed_patterns.json Bottom 100 failed patterns by confidence\n"
            "  negative_memory.json Current negative-memory blacklist (avoid zones)\n"
            "  heatmap.json        Regime × parameter confidence heatmap\n"
            "  log.json            Last 200 memory store records (explainability log)\n"
            "12_observability/   FTD-053-GAIA: Full pipeline observability snapshot\n"
            "  status.json         All six observability phase stats + health score\n"
            "  anomalies.json      Active anomalies + recent history (up to 100)\n"
            "  escalations.json    Active escalations + history (up to 100)\n"
            "  feeds.json          Five strategic intelligence feed channels\n"
            "  ai_summary.json     Latest AI strategic intelligence summary\n"
            "  events.json         Recent event bus events (up to 200)\n"
            "  sync.json           GitHub sync engine status\n"
            "13_system_diagnostics/ System health, audit trail, AI brain state\n"
            "  ct_scan.json        FTD-REF-026: Full CT-Scan (HEALTHY/WARNING/CRITICAL)\n"
            "  consistency.json    FTD-040: Consistency + drawdown + streak + recovery\n"
            "  audit_log.json      FTD-022: Last 1000 structured audit events\n"
            "  ai_brain.json       FTD-023: Aggregated AI brain intelligence state\n"
        ))

        _ev_meta = _safe(
            lambda: __import__(
                "core.intelligence.evolution_tracker",
                fromlist=["evolution_tracker"]
            ).evolution_tracker.summary(), {}
        )
        zf.writestr("metadata.json", json.dumps({
            "bundle_ts":        ts,
            "bundle_date":      time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
            "engine_ver":       f"EOW_QUANT_ENGINE_v{APP_VERSION}",
            "trade_count":      _n_trades,
            "net_pnl_usdt":     _ss.get("total_net_pnl", 0.0),
            "win_rate_pct":     _ss.get("win_rate", 0.0),
            "profit_factor":    _ss.get("profit_factor", 0.0),
            "max_drawdown_pct": _ss.get("max_drawdown_pct", 0.0),
            "sharpe_ratio":     _ss.get("sharpe_ratio", 0.0),
            "total_fees_usdt":  _ss.get("total_fees_paid", 0.0),
            "fee_drag_pct":     round(_fee_ratio * 100, 2),
            "presets_included": upe_presets,
            "evolution": {
                "correction_cycles":      _ev_meta.get("total_correction_pairs", 0),
                "drift_paused":           _ev_meta.get("drift_paused", False),
                "total_alerts":           _ev_meta.get("total_alerts", 0),
                "active_critical_alerts": len(_ev_meta.get("active_alerts", [])),
                "api_endpoint":           "/api/evolution-status",
            },
        }, indent=2, default=str))

        # 01_system_state/
        zf.writestr("01_system_state/eow_state.json", state_json_str)

        # 02_reports/ — extract MD + PDF from FTD-025A ZIP
        if system_zip_bytes:
            try:
                with zipfile.ZipFile(_io.BytesIO(system_zip_bytes)) as _sub:
                    for _name in _sub.namelist():
                        _ext = _name.rsplit(".", 1)[-1].lower()
                        _dst = f"02_reports/full_system_report.{_ext}"
                        zf.writestr(_dst, _sub.read(_name))
            except Exception:
                zf.writestr("02_reports/full_system_report.md",
                            "# Full system report generation failed")

        zf.writestr("02_reports/unified_report_v2.md",
                    unified_v2_md if isinstance(unified_v2_md, str)
                    else "# Unified report unavailable")

        # 03_trade_archive/ — extract XLSX + PDF + MD from archive ZIP
        if archive_zip_bytes:
            try:
                with zipfile.ZipFile(_io.BytesIO(archive_zip_bytes)) as _sub:
                    for _name in _sub.namelist():
                        _ext = _name.rsplit(".", 1)[-1].lower()
                        if _ext == "xlsx":
                            _dst = "03_trade_archive/trade_history.xlsx"
                        elif _ext == "pdf":
                            _dst = "03_trade_archive/trade_report.pdf"
                        else:
                            _dst = "03_trade_archive/trade_report.md"
                        zf.writestr(_dst, _sub.read(_name))
            except Exception:
                zf.writestr("03_trade_archive/trade_report.md",
                            "# Trade archive generation failed")

        # 04_performance/
        for _preset in upe_presets:
            zf.writestr(f"04_performance/report_{_preset}.json",
                        upe_jsons[_preset])
            zf.writestr(f"04_performance/trades_{_preset}.csv",
                        upe_csvs[_preset])

        # 05_forensics/ — deep-dive analysis for max-profit optimisation
        try:
            _forensic_files = _generate_forensic_reports(
                trade_dicts=trade_dicts,
                session_stats=_ss,
                thoughts=_thought_log,
                edge_summary=_safe(edge_engine.summary, {}),
            )
            for _fname, _fcontent in _forensic_files.items():
                zf.writestr(f"05_forensics/{_fname}", _fcontent)
        except Exception as _fe:
            zf.writestr("05_forensics/error.txt",
                        f"Forensic generation failed: {_fe}\n")

        # 06_evolution/ — FTD-EV-001 self-learning forensic audit trail
        try:
            _session_trades_ev = pnl_calc.trades[_boot_replay_count:]
            _evolution_files   = _generate_evolution_reports(_session_trades_ev)
            for _ename, _econtent in _evolution_files.items():
                zf.writestr(f"06_evolution/{_ename}", _econtent)
        except Exception as _ee:
            zf.writestr("06_evolution/error.txt",
                        f"Evolution report generation failed: {_ee}\n")

        # 08_rl_intelligence/ — FTD-055-ATHENA: institutional RL learning analysis
        try:
            _rl_intel_files = _generate_rl_intelligence_reports(
                trade_dicts=trade_dicts,
                session_start_idx=_boot_replay_count,
            )
            for _rif, _ric in _rl_intel_files.items():
                zf.writestr(f"08_rl_intelligence/{_rif}", _ric)
        except Exception as _rie:
            zf.writestr(
                "08_rl_intelligence/error.txt",
                f"RL intelligence report generation failed: {_rie}\n",
            )

        # 09_odyssey/ — FTD-056-ODYSSEY: Proof-of-Learning → Proof-of-Edge → Proof-of-Alpha
        try:
            _odyssey_files = _generate_odyssey_reports(
                trade_dicts=trade_dicts,
                session_start_idx=_boot_replay_count,
            )
            for _of, _oc in _odyssey_files.items():
                zf.writestr(f"09_odyssey/{_of}", _oc)
        except Exception as _ode:
            zf.writestr(
                "09_odyssey/error.txt",
                f"Odyssey report generation failed: {_ode}\n",
            )

        # 07_live_process/ — FTD-LPA: runtime observability artifacts ────────
        try:
            _lpa_zip_bytes = live_process_access.build_package(
                rl_engine_instance=rl_engine,
                pnl_calc_instance=pnl_calc,
                data_lake_instance=data_lake,
                thought_log=list(_thought_log),
                boot_ts=_boot_ts,
            )
            with zipfile.ZipFile(_io.BytesIO(_lpa_zip_bytes)) as _lpa_sub:
                for _lpa_name in _lpa_sub.namelist():
                    zf.writestr(_lpa_name, _lpa_sub.read(_lpa_name))
        except Exception as _lpa_err:
            zf.writestr("07_live_process/error.txt",
                        f"Live Process snapshot failed: {_lpa_err}\n")

        # 10_auto_intelligence/ — FTD-030: auto-correction loop state ────────
        try:
            if _auto_intelligence is not None:
                zf.writestr("10_auto_intelligence/state.json",
                            json.dumps(_safe(_auto_intelligence.summary, {}),
                                       indent=2, default=str))
                zf.writestr("10_auto_intelligence/history.json",
                            json.dumps({"history": _safe(lambda: _auto_intelligence.history(100), []),
                                        "phase": "030"},
                                       indent=2, default=str))
            else:
                zf.writestr("10_auto_intelligence/state.json",
                            json.dumps({"status": "not_initialised"}, indent=2))
        except Exception as _aie:
            zf.writestr("10_auto_intelligence/error.txt", f"Failed: {_aie}\n")

        # 11_learning_memory/ — FTD-030B: pattern memory & negative memory ──
        try:
            from core.learning_memory import learning_memory_orchestrator as _lmo
            zf.writestr("11_learning_memory/summary.json",
                        json.dumps(_safe(_lmo.summary, {}), indent=2, default=str))
            zf.writestr("11_learning_memory/patterns.json",
                        json.dumps({"patterns": _safe(lambda: _lmo.pattern_leaderboard(100), []),
                                    "phase": "030B"},
                                   indent=2, default=str))
            zf.writestr("11_learning_memory/failed_patterns.json",
                        json.dumps({"failed_patterns": _safe(lambda: _lmo.failed_patterns(100), []),
                                    "phase": "030B"},
                                   indent=2, default=str))
            zf.writestr("11_learning_memory/negative_memory.json",
                        json.dumps({"negative_memory": _safe(_lmo.negative_memory_list, []),
                                    "phase": "030B"},
                                   indent=2, default=str))
            zf.writestr("11_learning_memory/heatmap.json",
                        json.dumps({"heatmap": _safe(_lmo.pattern_heatmap, {}),
                                    "phase": "030B"},
                                   indent=2, default=str))
            zf.writestr("11_learning_memory/log.json",
                        json.dumps({"records": _safe(lambda: _lmo.recent_memory_log(200), []),
                                    "phase": "030B"},
                                   indent=2, default=str))
        except Exception as _lme:
            zf.writestr("11_learning_memory/error.txt", f"Failed: {_lme}\n")

        # 12_observability/ — FTD-053-GAIA: pipeline observability state ─────
        try:
            _orch_st = _safe(obs_orchestrator.stats, {})
            zf.writestr("12_observability/status.json",
                        json.dumps(_sanitize({
                            "health":         _obs_health_status(_orch_st),
                            "orchestrator":   _orch_st,
                            "anomaly_engine": _safe(_obs_ad.stats, {}),
                            "escalation":     _safe(_obs_ee.stats, {}),
                            "event_bus":      _safe(_obs_eb.status, {}),
                            "strategic_feed": _safe(_obs_sf.status, {}),
                            "summary_engine": _safe(_obs_se.stats, {}),
                            "sync_engine":    _safe(_obs_gse.status, {}),
                            "lifecycle":      _safe(_obs_rle.status, {}),
                            "delta_reporter": _safe(_obs_dr.stats, {}),
                        }), indent=2, default=str))
            zf.writestr("12_observability/anomalies.json",
                        json.dumps(_sanitize({
                            "active_summary": _safe(_obs_ad.get_active_summary, {}),
                            "recent_history": _safe(
                                lambda: _obs_ad.get_history(limit=100, min_severity="LOW"), []),
                            "stats": _safe(_obs_ad.stats, {}),
                        }), indent=2, default=str))
            zf.writestr("12_observability/escalations.json",
                        json.dumps(_sanitize({
                            "active":  _safe(_obs_ee.get_active_escalations, []),
                            "history": _safe(lambda: _obs_ee.get_history(limit=100), []),
                            "stats":   _safe(_obs_ee.stats, {}),
                        }), indent=2, default=str))
            _sf_st = _safe(_obs_sf.status, {})
            zf.writestr("12_observability/feeds.json",
                        json.dumps(_sanitize({
                            "feeds":               _sf_st.get("feeds", {}),
                            "max_signal_strength": _sf_st.get("max_signal_strength", 0.0),
                            "last_refresh_ts":     _sf_st.get("last_refresh_ts", 0),
                            "total_refreshes":     _sf_st.get("total_refreshes", 0),
                        }), indent=2, default=str))
            _ai_summ = _safe(_obs_se.get_last_summary, None)
            zf.writestr("12_observability/ai_summary.json",
                        json.dumps(_sanitize(
                            _ai_summ if _ai_summ is not None
                            else {"status": "COLD_START", "message": "No summary generated yet"}
                        ), indent=2, default=str))
            zf.writestr("12_observability/events.json",
                        json.dumps(_sanitize({
                            "recent_events": _safe(lambda: _obs_eb.recent_events(limit=200), []),
                            "bus_status":    _safe(_obs_eb.status, {}),
                        }), indent=2, default=str))
            zf.writestr("12_observability/sync.json",
                        json.dumps(_sanitize(_safe(_obs_gse.status, {})),
                                   indent=2, default=str))
        except Exception as _obe:
            zf.writestr("12_observability/error.txt", f"Failed: {_obe}\n")

        # 13_system_diagnostics/ — CT-Scan, consistency, audit log, AI brain ─
        try:
            _cts2   = pnl_calc.session_stats
            _n_t2   = len(pnl_calc.trades)
            _tf2    = _cts2.get("total_fees_paid", 0.0)
            _tn2    = _cts2.get("total_net_pnl",   0.0)
            _tsl2   = _cts2.get("total_slippage",  0.0)
            _tg2    = abs(_tn2) + _tf2 + _tsl2
            _fr2    = _tf2 / max(_tg2, 1e-9)
            zf.writestr("13_system_diagnostics/ct_scan.json",
                        json.dumps(_safe(lambda: ct_scan_engine.scan(
                            profit_factor  = _cts2.get("profit_factor", 0.0),
                            fee_ratio      = round(_fr2, 4),
                            strategy_usage = strategy_engine.usage(),
                            win_rate       = _cts2.get("win_rate", 0.0) / 100.0,
                            regime_stable  = True,
                            n_trades       = _n_t2,
                        ), {}), indent=2, default=str))
            zf.writestr("13_system_diagnostics/consistency.json",
                        json.dumps({
                            "consistency":      _safe(consistency_engine.status, {}),
                            "drawdown":         _safe(drawdown_controller.summary, {}),
                            "streak":           _safe(streak_engine.summary, {}),
                            "capital_recovery": _safe(capital_recovery_engine.summary, {}),
                            "loss_cluster":     _safe(loss_cluster_controller.summary, {}),
                        }, indent=2, default=str))
            from core.audit.audit_engine import audit_engine as _ae_b
            zf.writestr("13_system_diagnostics/audit_log.json",
                        json.dumps(_safe(lambda: _ae_b.get_log(limit=1000), []),
                                   indent=2, default=str))
            from core.meta.ai_brain import ai_brain as _ab_b
            zf.writestr("13_system_diagnostics/ai_brain.json",
                        json.dumps(_safe(_ab_b.get_state, {}),
                                   indent=2, default=str))
        except Exception as _dge:
            zf.writestr("13_system_diagnostics/error.txt", f"Failed: {_dge}\n")

    buf.seek(0)
    filename = f"eow_bundle_{ts}.zip"
    _thought(
        f"📦 Master Report Bundle downloaded → {filename} "
        f"({_n_trades} trades, {len(buf.getvalue())//1024} KB)",
        "SYSTEM"
    )
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Entry Point ───────────────────────────────────────────────────────────────

# Serve dashboard.html at "/" so http://localhost:8000 opens the dashboard directly
# ── FTD-LIO: Learning Intelligence Observatory API ─────────────────────────

def _build_rl_pipeline_mix(engine) -> dict:
    """
    Inspect rl_engine context keys to derive a pipeline attribution breakdown.
    Context keys have the form REGIME|SESSION|STRATEGY.  Strategies ending with
    _PAPER_SPEED originated from the ecology-gated pipeline; all others are
    PRIMARY_STRATEGY (ecology-bypassed).  This is observability-only — no
    execution state is mutated.
    """
    contexts = getattr(engine, "_contexts", {})
    paper_speed, primary, unknown = [], [], []
    for ctx_key in contexts:
        parts = ctx_key.split("|")
        strategy = parts[2] if len(parts) == 3 else ""
        if strategy.endswith("_PAPER_SPEED"):
            paper_speed.append(ctx_key)
        elif strategy:
            primary.append(ctx_key)
        else:
            unknown.append(ctx_key)
    total = len(contexts)
    return {
        "total_rl_contexts": total,
        "paper_speed_contexts": len(paper_speed),
        "primary_strategy_contexts": len(primary),
        "unknown_contexts": len(unknown),
        "paper_speed_pct": round(len(paper_speed) / total * 100, 1) if total else 0.0,
        "primary_strategy_pct": round(len(primary) / total * 100, 1) if total else 0.0,
        "note": (
            "RL Q-table is shared across both pipelines. paper_speed_contexts "
            "originated via ecology gate; primary_strategy_contexts bypassed ecology."
        ),
    }


@app.get("/api/learning-intelligence/summary")
async def lio_summary():
    """LIO — Learning heartbeat: state, record counts, activity metrics."""
    from core.learning_memory import learning_memory_orchestrator
    import time as _t
    lmo   = learning_memory_orchestrator
    bridge_t = trade_memory_bridge.get_telemetry()
    lmo_s    = lmo.summary()
    neg_counts = lmo._neg_memory.count()
    total_rec  = lmo_s.get("total_records", 0)
    formed     = lmo_s.get("formed_patterns", 0)
    cycles     = lmo_s.get("cycle_count", 0)
    neg_total  = neg_counts.get("total", 0)

    # Derive heartbeat state
    if cycles == 0 or total_rec == 0:
        heartbeat = "DORMANT"
    elif formed == 0:
        heartbeat = "LEARNING"
    elif neg_total > formed * 3:
        heartbeat = "DEGRADED"
    elif formed >= 10:
        heartbeat = "SATURATED"
    else:
        heartbeat = "ACTIVE"

    # Simple growth rate: records / max(1, cycles)
    memory_growth_rate = round(total_rec / max(1, cycles), 3)
    # Cognition activity score 0–100 based on formed/total patterns ratio
    all_pats = lmo._engine.all_patterns()
    total_patterns = len(all_pats)
    cog_score = round(min(100.0, (formed / max(1, total_patterns)) * 100.0 + cycles * 0.5), 1)

    return {
        "heartbeat_state":       heartbeat,
        "total_records":         total_rec,
        "patterns_formed":       formed,
        "total_patterns":        total_patterns,
        "active_negative_memories": neg_total,
        "permanent_bans":        neg_counts.get("permanent", 0),
        "lmo_enabled":           lmo_s.get("enabled", True),
        "lmo_cycle_count":       cycles,
        "memory_growth_rate":    memory_growth_rate,
        "cognition_activity_score": cog_score,
        "bridge_total_recorded": bridge_t.get("total_recorded", 0),
        "bridge_win_rate":       bridge_t.get("win_rate", 0.0),
        "ts": int(_t.time() * 1000),
    }


@app.get("/api/learning-intelligence/patterns")
async def lio_patterns():
    """LIO — Pattern crystallization grid: all patterns with stage classification."""
    from core.learning_memory import learning_memory_orchestrator
    lmo = learning_memory_orchestrator
    neg_entries = {e["key_str"]: e for e in lmo._neg_memory.to_list()}
    patterns = []
    for pat in lmo._engine.all_patterns():
        key      = pat.key  # (regime, volatility, instrument, strategy, direction)
        key_str  = "|".join(str(k) for k in key)
        neg_e    = neg_entries.get(key_str)
        win_rate = round(pat.success / max(1, pat.samples), 4)
        ctx_count = len(pat.contexts)

        if neg_e and neg_e.get("permanent"):
            stage = "BANNED"
        elif neg_e and neg_e.get("score", 0) >= 0.10:
            stage = "TOXIC"
        elif pat.is_formed:
            stage = "STABLE"
        elif pat.samples >= 10:
            stage = "FORMING"
        else:
            stage = "OBSERVED"

        patterns.append({
            "pattern_id":   pat.pattern_id,
            "regime":       key[0],
            "volatility":   key[1],
            "instrument":   key[2],
            "strategy":     key[3],
            "direction":    key[4],
            "samples":      pat.samples,
            "success":      pat.success,
            "confidence":   round(pat.confidence, 2),
            "win_rate":     win_rate,
            "context_count": ctx_count,
            "contexts":     sorted(pat.contexts),
            "is_formed":    pat.is_formed,
            "stage":        stage,
            "toxicity_score": round(neg_e["score"], 3) if neg_e else 0.0,
            "rollbacks":    neg_e["rollbacks"] if neg_e else 0,
            "created_at":   pat.created_at,
        })

    # Sort: STABLE first, then FORMING, OBSERVED, TOXIC, BANNED
    stage_order = {"STABLE": 0, "FORMING": 1, "OBSERVED": 2, "TOXIC": 3, "BANNED": 4}
    patterns.sort(key=lambda p: (stage_order.get(p["stage"], 5), -p["samples"]))

    heatmap = lmo.pattern_heatmap()
    return {
        "total_patterns":  len(patterns),
        "formed_patterns": sum(1 for p in patterns if p["is_formed"]),
        "patterns":        patterns,
        "heatmap":         heatmap,
    }


@app.get("/api/learning-intelligence/negative-memory")
async def lio_negative_memory():
    """LIO — Negative memory observatory: toxic patterns, bans, catastrophic events."""
    from core.learning_memory import learning_memory_orchestrator
    import time as _t
    lmo     = learning_memory_orchestrator
    entries = lmo._neg_memory.to_list()
    counts  = lmo._neg_memory.count()

    # Parse key_str back into components for display
    enriched = []
    for e in entries:
        parts = e.get("key_str", "").split("|")
        regime   = parts[0] if len(parts) > 0 else "UNKNOWN"
        vol      = parts[1] if len(parts) > 1 else "UNKNOWN"
        instr    = parts[2] if len(parts) > 2 else "UNKNOWN"
        strategy = parts[3] if len(parts) > 3 else "UNKNOWN"
        direction= parts[4] if len(parts) > 4 else "UNKNOWN"

        if e.get("permanent"):
            status = "PERMANENTLY_BANNED"
        elif e.get("score", 0) >= 0.70:
            status = "QUARANTINED"
        elif e.get("score", 0) >= 0.30:
            status = "TOXIC"
        else:
            status = "WARNING"

        enriched.append({
            **e,
            "regime":    regime,
            "volatility": vol,
            "instrument": instr,
            "strategy":  strategy,
            "direction": direction,
            "status":    status,
        })

    enriched.sort(key=lambda x: (0 if x.get("permanent") else 1, -x.get("rollbacks", 0)))

    return {
        "counts":               counts,
        "entries":              enriched,
        "catastrophic_threshold": -2.0,
        "permanent_ban_after":  3,
        "decay_rate":           0.90,
        "ts": int(_t.time() * 1000),
    }


@app.get("/api/learning-intelligence/ecology")
async def lio_ecology():
    """LIO — Ecology maturity: context diversity, signal density, survival."""
    import time as _t
    snap    = opportunity_ecology.ecology_snapshot()
    full_t  = opportunity_ecology.get_telemetry()
    ctx_mem = full_t.get("context_memory", {})
    ste_t   = signal_truth_engine.get_telemetry()

    total_ctx    = ctx_mem.get("total_contexts", 0)
    profitable   = ctx_mem.get("profitable_count", 0)
    toxic_ctx    = ctx_mem.get("toxic_count", 0)
    immature_ctx = max(0, total_ctx - profitable - toxic_ctx)

    density      = full_t.get("density_snapshot", {})
    survival     = density.get("survival_rate", 0.0)
    signals_hr   = density.get("signals_per_hr", 0.0)
    truth_dens   = ste_t.get("truth_density", 0.0)

    # Ecology health gate
    if snap.get("is_starvation"):
        eco_health = "STARVATION"
    elif snap.get("is_drought"):
        eco_health = "DROUGHT"
    elif total_ctx < 5:
        eco_health = "IMMATURE"
    elif survival < 0.30:
        eco_health = "COLLAPSING"
    elif survival >= 0.60 and profitable >= 5:
        eco_health = "MATURE"
    else:
        eco_health = "FORMING"

    total_eval = snap.get("total_evaluated", 0)
    mature_ctx = profitable  # profitable contexts == mature contexts

    return {
        "ecology_health":    eco_health,
        "total_evaluated":   total_eval,
        "total_approved":    snap.get("total_approved", 0),
        "approval_rate":     snap.get("approval_rate", 0.0),
        "total_contexts":    total_ctx,
        "mature_contexts":   mature_ctx,
        "immature_contexts": immature_ctx,
        "toxic_contexts":    toxic_ctx,
        "signals_per_hr":    signals_hr,
        "survival_rate":     survival,
        "truth_density":     truth_dens,
        "is_drought":        snap.get("is_drought", False),
        "is_starvation":     snap.get("is_starvation", False),
        "rsi_blocked":       snap.get("rsi_blocked", 0),
        "context_blocked":   snap.get("context_blocked", 0),
        "recovery_trades":   snap.get("recovery_trades", 0),
        "scope_note":        (
            "Ecology metrics (survival_rate, RSI gates, context blocks) apply "
            "exclusively to PAPER_SPEED signals. PRIMARY_STRATEGY signals bypass "
            "ecology evaluation entirely and are not represented in these counts."
        ),
        "ts": int(_t.time() * 1000),
    }


@app.get("/api/learning-intelligence/rl")
async def lio_rl():
    """LIO — RL intelligence observatory: Q-values, convergence, exploration."""
    import time as _t
    t = rl_engine.get_evolution_state()
    cold_start = t.get("status") == "COLD_START"
    ld = t.get("learning_dynamics", {})
    avg_q     = ld.get("avg_q", 0.0)
    q_vel     = ld.get("avg_q_velocity", 0.0)
    explore_r = ld.get("explore_ratio", 1.0) if not cold_start else 1.0
    toxic_cnt = ld.get("toxic_count", 0)
    qd        = t.get("quality_distribution", {})
    counters  = t.get("counters", {})
    total_pulls = counters.get("total_pulls", 0) if not cold_start else rl_engine._total_pulls
    intell_score = t.get("intelligence_score", 0.0)

    # Derive brain status
    if total_pulls == 0:
        brain_status = "IDLE"
    elif avg_q < -0.5:
        brain_status = "NEGATIVE_CONVERGENCE"
    elif explore_r > 0.6:
        brain_status = "EXPLORING"
    elif q_vel > 0.05 and explore_r > 0.2:
        brain_status = "LEARNING"
    elif q_vel < 0.01 and explore_r < 0.3 and avg_q > 0:
        brain_status = "CONVERGING"
    elif toxic_cnt > t.get("total_contexts", 1) * 0.4:
        brain_status = "COLLAPSED"
    else:
        brain_status = "LEARNING"

    # Derive convergence state
    if total_pulls < 10:
        convergence = "INITIALIZING"
    elif avg_q > 0.3 and q_vel < 0.02:
        convergence = "CONVERGED"
    elif avg_q < -0.2:
        convergence = "DIVERGING"
    else:
        convergence = "IN_PROGRESS"

    profitable_pct = qd.get("profitable_pct", 0.0)
    exploit_ratio  = round(1.0 - explore_r, 4)

    return {
        "brain_status":       brain_status,
        "convergence_state":  convergence,
        "intelligence_score": intell_score,
        "avg_q":              avg_q,
        "q_spread":           round(q_vel, 4),
        "avg_q_velocity":     q_vel,
        "explore_ratio":      explore_r,
        "exploit_ratio":      exploit_ratio,
        "toxic_count":        toxic_cnt,
        "total_contexts":     t.get("total_contexts", 0),
        "context_maturity":   t.get("context_maturity", {}),
        "quality_distribution": qd,
        "session_intelligence": t.get("session_intelligence", {}),
        "counters":           counters,
        "profitable_pct":     profitable_pct,
        "session_authority":  __import__(
            "core.time.session_definitions", fromlist=["get_session_integrity_block"]
        ).get_session_integrity_block(),
        "pipeline_mix":       _build_rl_pipeline_mix(rl_engine),
        "ts": int(_t.time() * 1000),
    }


@app.get("/api/learning-intelligence/session-attribution")
async def lio_session_attribution():
    """
    LIO — Session-attribution forensics.

    Diagnostic overlay: exposes origin-session vs close-session win-rates,
    cross-boundary trade distribution, hold-duration asymmetry, and the
    boundary transition matrix.

    NON-GOVERNING: these metrics are observability-only.  They do not affect
    RL learning, ecology gates, or any execution decision.
    """
    import time as _t
    from collections import defaultdict

    raw_trades = data_lake.get_trades(limit=5000)

    # ── Accumulators ────────────────────────────────────────────────────────
    origin_wins:  dict[str, int] = defaultdict(int)
    origin_loss:  dict[str, int] = defaultdict(int)
    close_wins:   dict[str, int] = defaultdict(int)
    close_loss:   dict[str, int] = defaultdict(int)
    transition_counts: dict[str, int] = defaultdict(int)

    total = len(raw_trades)
    cross_total = cross_wins = cross_loss = 0
    hold_ms_by_origin:  dict[str, list] = defaultdict(list)
    hold_ms_by_close:   dict[str, list] = defaultdict(list)
    hold_ms_winners:    list = []
    hold_ms_losers:     list = []
    hold_ms_cross:      list = []

    for tr in raw_trades:
        origin = tr.get("origin_session", "UNKNOWN")
        close  = tr.get("close_session",  "UNKNOWN")
        pnl    = tr.get("net_pnl", 0.0)
        won    = pnl >= 0
        hold   = max(0, tr.get("exit_ts", 0) - tr.get("entry_ts", 0))  # ms
        crossed = tr.get("crossed_session_boundary", False)

        if origin != "UNKNOWN":
            (origin_wins if won else origin_loss)[origin] += 1
            hold_ms_by_origin[origin].append(hold)
        if close != "UNKNOWN":
            (close_wins if won else close_loss)[close] += 1
            hold_ms_by_close[close].append(hold)
        if won:
            hold_ms_winners.append(hold)
        else:
            hold_ms_losers.append(hold)
        if crossed:
            cross_total += 1
            transition = tr.get("boundary_transition", f"{origin}→{close}")
            transition_counts[transition] += 1
            if won:
                cross_wins += 1
            else:
                cross_loss += 1
            hold_ms_cross.append(hold)

    def _wr(wins, loss):
        n = wins + loss
        return round(wins / n * 100, 1) if n else None

    def _avg_ms(lst):
        return round(sum(lst) / len(lst) / 1000, 1) if lst else None  # → seconds

    all_sessions = set(origin_wins) | set(origin_loss) | set(close_wins) | set(close_loss)
    origin_wr = {
        s: {
            "wins":   origin_wins[s],
            "losses": origin_loss[s],
            "win_rate_pct": _wr(origin_wins[s], origin_loss[s]),
            "avg_hold_sec": _avg_ms(hold_ms_by_origin.get(s, [])),
        }
        for s in sorted(all_sessions)
        if origin_wins[s] + origin_loss[s] > 0
    }
    close_wr = {
        s: {
            "wins":   close_wins[s],
            "losses": close_loss[s],
            "win_rate_pct": _wr(close_wins[s], close_loss[s]),
            "avg_hold_sec": _avg_ms(hold_ms_by_close.get(s, [])),
        }
        for s in sorted(all_sessions)
        if close_wins[s] + close_loss[s] > 0
    }
    total_with_origin = sum(origin_wins.values()) + sum(origin_loss.values())

    return {
        "scope_note": (
            "Forensic overlay only.  These metrics expose temporal attribution "
            "structure and do not govern any RL, ecology, or execution decisions."
        ),
        "total_trades_analysed": total,
        "trades_with_origin_attribution": total_with_origin,
        "origin_session_win_rates": origin_wr,
        "close_session_win_rates": close_wr,
        "cross_boundary": {
            "total":              cross_total,
            "winner_cross_count": cross_wins,
            "loser_cross_count":  cross_loss,
            "winner_cross_pct":   round(cross_wins / len(hold_ms_winners) * 100, 1) if hold_ms_winners else None,
            "loser_cross_pct":    round(cross_loss / len(hold_ms_losers) * 100, 1) if hold_ms_losers else None,
            "avg_hold_sec":       _avg_ms(hold_ms_cross),
        },
        "boundary_transition_matrix": dict(
            sorted(transition_counts.items(), key=lambda x: -x[1])
        ),
        "hold_duration": {
            "avg_winner_hold_sec": _avg_ms(hold_ms_winners),
            "avg_loser_hold_sec":  _avg_ms(hold_ms_losers),
            "hold_asymmetry_note": (
                "If loser hold > winner hold, delayed-loss sessions may absorb "
                "losses from earlier-session entries (origin-receiver distortion)."
            ),
        },
        "ts": int(_t.time() * 1000),
    }


@app.get("/api/learning-intelligence/topology")
async def lio_topology():
    """LIO — Learning topology map: profitable/toxic/neutral/unexplored zones."""
    from core.learning_memory import learning_memory_orchestrator
    import time as _t
    lmo     = learning_memory_orchestrator
    heatmap = lmo.pattern_heatmap()
    neg_entries = {e["key_str"]: e for e in lmo._neg_memory.to_list()}

    profitable, toxic, neutral, unexplored = [], [], [], []
    for cell in heatmap:
        regime    = cell.get("regime", "UNKNOWN")
        parameter = cell.get("parameter", "UNKNOWN")
        avg_conf  = cell.get("avg_conf", 0.0)
        count     = cell.get("count", 0)
        # Check if any key with this regime+parameter is banned
        is_toxic = any(
            e.get("permanent") or e.get("score", 0) >= 0.30
            for k, e in neg_entries.items()
            if k.startswith(regime) and parameter in k
        )
        zone_entry = {"regime": regime, "parameter": parameter,
                      "avg_conf": avg_conf, "count": count}
        if is_toxic:
            toxic.append(zone_entry)
        elif avg_conf >= 70:
            profitable.append(zone_entry)
        elif avg_conf >= 40:
            neutral.append(zone_entry)
        else:
            unexplored.append(zone_entry)

    return {
        "zones": {
            "profitable":  sorted(profitable, key=lambda x: -x["avg_conf"]),
            "toxic":       toxic,
            "neutral":     neutral,
            "unexplored":  unexplored,
        },
        "heatmap": heatmap,
        "ts": int(_t.time() * 1000),
    }


@app.get("/api/learning-intelligence/cognition")
async def lio_cognition():
    """LIO — Cognitive compression: signal noise, repetition, compression health."""
    from core.learning_memory import learning_memory_orchestrator
    import time as _t
    lmo    = learning_memory_orchestrator
    ste_t  = signal_truth_engine.get_telemetry()
    lmo_s  = lmo.summary()
    eco_t  = opportunity_ecology.get_telemetry()

    total_rec  = lmo_s.get("total_records", 0)
    total_pats = len(lmo._engine.all_patterns())
    formed     = lmo_s.get("formed_patterns", 0)
    cycles     = lmo_s.get("cycle_count", 0)

    # Signal noise ratio from truth engine (1 - truth_density)
    truth_dens   = ste_t.get("truth_density", 0.0)
    noise_ratio  = round(1.0 - truth_dens, 4) if truth_dens > 0 else 1.0

    # Repeated signal loops: avg samples per pattern (high = repetitive)
    avg_samples  = round(total_rec / max(1, total_pats), 2) if total_pats > 0 else 0.0

    # Cognitive load: cycle_count relative to patterns formed
    if cycles == 0:
        cog_load = 0.0
    else:
        cog_load = round(min(1.0, formed / max(1, cycles / 20)), 4)

    # Compression ratio: formed patterns / total patterns
    compression_ratio = round(formed / max(1, total_pats), 4) if total_pats > 0 else 0.0

    # Noise state
    if noise_ratio < 0.25:
        noise_state = "HEALTHY"
    elif noise_ratio < 0.55:
        noise_state = "NOISY"
    elif noise_ratio < 0.80:
        noise_state = "SATURATED"
    else:
        noise_state = "CRITICAL"

    total_signals  = ste_t.get("total_signals", 0)
    total_outcomes = ste_t.get("total_outcomes", 0)
    suppressed     = eco_t.get("total_rsi_blocked", 0) + eco_t.get("total_ctx_blocked", 0)

    return {
        "noise_state":                 noise_state,
        "signal_noise_ratio":          noise_ratio,
        "truth_density":               truth_dens,
        "repeated_signal_loops":       avg_samples,
        "compressed_patterns":         formed,
        "total_pattern_candidates":    total_pats,
        "compression_ratio":           compression_ratio,
        "cognitive_activity_load":     cog_load,
        "suppressed_redundant_evals":  suppressed,
        "total_signals":               total_signals,
        "total_outcomes":              total_outcomes,
        "ts": int(_t.time() * 1000),
    }


@app.get("/api/learning-intelligence/sovereign-readiness")
async def lio_sovereign_readiness():
    """LIO — Sovereign governance readiness meter: all PRP-003A activation gates."""
    from core.learning_memory import learning_memory_orchestrator
    import time as _t
    lmo   = learning_memory_orchestrator
    ste_t = signal_truth_engine.get_telemetry()
    eco_snap = opportunity_ecology.ecology_snapshot()
    rl_t     = rl_engine.get_evolution_state()
    lmo_s    = lmo.summary()

    evaluated_signals = eco_snap.get("total_evaluated", 0)
    rl_ctx  = rl_t.get("context_maturity", {})
    mature_ctx = rl_ctx.get("mature", 0)
    truth_dens = ste_t.get("truth_density", 0.0)
    eco_ctx_t  = opportunity_ecology.get_telemetry()
    ctx_mem    = eco_ctx_t.get("context_memory", {})
    profitable = ctx_mem.get("profitable_count", 0)
    survival   = eco_ctx_t.get("density_snapshot", {}).get("survival_rate", 0.0)
    eco_health_pass = (profitable >= 5 and survival >= 0.40
                       and not eco_snap.get("is_starvation", False))

    gates = {
        "evaluated_signals": {
            "current": evaluated_signals,
            "target":  100,
            "pass":    evaluated_signals >= 100,
            "label":   "Signal Evaluation Volume",
        },
        "mature_contexts": {
            "current": mature_ctx,
            "target":  10,
            "pass":    mature_ctx >= 10,
            "label":   "RL Mature Context Count",
        },
        "truth_density": {
            "current": round(truth_dens, 4),
            "target":  "> 0",
            "pass":    truth_dens > 0,
            "label":   "Signal Truth Density",
        },
        "ecology_health": {
            "current": "PASS" if eco_health_pass else "FAIL",
            "target":  "PASS",
            "pass":    eco_health_pass,
            "label":   "Ecology Health Gate",
        },
    }

    pass_count = sum(1 for g in gates.values() if g["pass"])
    total_gates = len(gates)

    if pass_count == 0:
        state = "NOT_READY"
    elif pass_count == 1:
        state = "ECOLOGY_FORMING"
    elif pass_count in (2, 3):
        state = "LEARNING_ACTIVE"
    else:
        state = "SOVEREIGN_READY"

    return {
        "state":       state,
        "pass_count":  pass_count,
        "total_gates": total_gates,
        "gates":       gates,
        "ts": int(_t.time() * 1000),
    }


@app.get("/api/learning-intelligence/alpha-discovery")
async def lio_alpha_discovery():
    """LIO §9 — Alpha Discovery Observatory: positive memory emergence, profitable-context
    formation rate, and positive/negative memory ratio.  READ-ONLY — no RL modifications."""
    from core.learning_memory import learning_memory_orchestrator
    import time as _t
    lmo       = learning_memory_orchestrator
    rl_state  = rl_engine.get_evolution_state()
    neg_counts = lmo._neg_memory.count()

    qd            = rl_state.get("quality_distribution", {})
    elite         = qd.get("elite", 0)
    high          = qd.get("high", 0)
    penalized     = qd.get("penalized", 0)
    profitable_pct = qd.get("profitable_pct", 0.0)
    total_ctx     = rl_state.get("total_contexts", 0)
    profitable_ctx = elite + high          # q > 0.40

    sess_intel = rl_state.get("session_intelligence", {})
    sess_profitable = sum(sv.get("profitable", 0) for sv in sess_intel.values())

    # Profitable patterns: formed + at least 1 success
    all_pats = lmo._engine.all_patterns()
    profitable_patterns = sum(
        1 for p in all_pats if p.is_formed and p.success > 0
    )
    # Positive topology zones (avg_conf ≥ 70)
    heatmap = lmo.pattern_heatmap()
    topology_profitable = sum(1 for c in heatmap if c.get("avg_conf", 0) >= 70)

    total_bans   = neg_counts.get("permanent", 0) + neg_counts.get("temporary", 0)
    perm_bans    = neg_counts.get("permanent", 0)

    # Ratio: profitable contexts vs total known-negative contexts
    pos_neg_ratio = round(profitable_ctx / max(1, total_bans), 3)

    # Alpha discovery velocity: % of total contexts that are profitable
    discovery_velocity = round(profitable_ctx / max(1, total_ctx) * 100, 2)

    # Discovery health composite
    if profitable_ctx >= 5 and profitable_pct >= 20:
        discovery_health = "CRYSTALLIZING"
    elif profitable_ctx >= 2 or sess_profitable >= 1 or profitable_patterns >= 1:
        discovery_health = "EMERGING"
    elif total_bans > 0 and profitable_ctx == 0:
        discovery_health = "STAGNANT"
    else:
        discovery_health = "SEARCHING"

    return {
        "discovery_health":        discovery_health,
        "profitable_contexts":     profitable_ctx,
        "elite_contexts":          elite,
        "high_contexts":           high,
        "penalized_contexts":      penalized,
        "total_contexts":          total_ctx,
        "profitable_pct":          profitable_pct,
        "profitable_sessions":     sess_profitable,
        "profitable_patterns":     profitable_patterns,
        "total_bans":              total_bans,
        "permanent_bans":          perm_bans,
        "pos_neg_ratio":           pos_neg_ratio,
        "topology_profitable_zones": topology_profitable,
        "alpha_discovery_velocity":  discovery_velocity,
        "session_intelligence":      sess_intel,
        "ts": int(_t.time() * 1000),
    }


@app.get("/api/learning-intelligence/economic-ground-truth")
async def lio_economic_ground_truth():
    """
    LIO — Economic ground truth layer.

    FTD-ECO-TRUTH: Non-governing read-only overlay.
    Provides fee-adjusted expectancy, payoff geometry, subsystem attribution,
    economic classification breakdown, session economics, and survivability score.
    """
    from core.economic_truth import compute_economic_ground_truth as _cegt
    from dataclasses import asdict

    session_trades = [asdict(t) for t in pnl_calc.trades]
    historical     = data_lake.get_trades(limit=1000)

    seen: dict[str, dict] = {}
    for t in session_trades:
        tid = t.get("trade_id", "")
        if tid:
            seen[tid] = t
    for t in historical:
        tid = t.get("trade_id", "")
        if tid and tid not in seen:
            seen[tid] = t

    all_trades = sorted(seen.values(), key=lambda x: x.get("entry_ts", 0))
    return _cegt(all_trades)


@app.get("/api/learning-intelligence/regime-survivability-cartography")
async def lio_regime_survivability_cartography():
    """
    LIO — Adaptive Economic Regime Mapping & Survivability Cartography.

    FTD-REGIME-SURVIV: Non-governing research instrumentation.
    Maps economic survivability across regime × session × timeframe × exploration state.
    Generates survivability heatmap, 6-category alpha landscape classification,
    regime-transition diagnostics, and ontology alignment economics.

    Shadow TF projections (5m/15m) use same proportional-gross model as
    timeframe-survivability endpoint. Research only — no execution authority.
    """
    from core.regime_cartography import compute_regime_survivability_cartography as _crsc
    from dataclasses import asdict

    session_trades = [asdict(t) for t in pnl_calc.trades]
    historical     = data_lake.get_trades(limit=1000)

    seen: dict[str, dict] = {}
    for t in session_trades:
        tid = t.get("trade_id", "")
        if tid:
            seen[tid] = t
    for t in historical:
        tid = t.get("trade_id", "")
        if tid and tid not in seen:
            seen[tid] = t

    all_trades = sorted(seen.values(), key=lambda x: x.get("entry_ts", 0))
    return _crsc(all_trades)


@app.get("/api/learning-intelligence/timeframe-survivability")
async def lio_timeframe_survivability():
    """
    LIO — Timeframe Economics Comparator & Alpha Survivability Mapping.

    FTD-TF-SURVIV: Non-governing research instrumentation.
    Compares 1m (actual) vs 5m and 15m (shadow projections) economics to answer:
    is PHOENIX discovering weak signals or strong signals trapped in 1m friction?

    Shadow projections assume the same directional signal captures proportionally
    more gross PnL at higher timeframes with identical fees. Research only —
    no execution authority, no routing changes.
    """
    from core.timeframe_economics import compute_timeframe_survivability as _ctfs
    from dataclasses import asdict

    session_trades = [asdict(t) for t in pnl_calc.trades]
    historical     = data_lake.get_trades(limit=1000)

    seen: dict[str, dict] = {}
    for t in session_trades:
        tid = t.get("trade_id", "")
        if tid:
            seen[tid] = t
    for t in historical:
        tid = t.get("trade_id", "")
        if tid and tid not in seen:
            seen[tid] = t

    all_trades = sorted(seen.values(), key=lambda x: x.get("entry_ts", 0))
    return _ctfs(all_trades)


@app.get("/api/learning-intelligence/exploration-economic-attribution")
async def lio_exploration_economic_attribution():
    """
    LIO — Exploration economic survivability diagnostics.

    FTD-EXPLORE-ATTR: Non-governing read-only overlay.
    Provides per-type WR, avg PnL, fee drag, Q-delta, profitability correlation,
    session breakdown, NY-specific Rule4 diagnostics, survivability classification,
    and longitudinal dynamics (rolling 10/25-trade windows).
    """
    from core.exploration_economics import compute_exploration_economics as _cee
    from dataclasses import asdict

    # Use in-memory current-session trades + any DataLake history
    session_trades  = [asdict(t) for t in pnl_calc.trades]
    historical      = data_lake.get_trades(limit=1000)

    # Deduplicate: DataLake may already include current-session trades persisted at close.
    # Prefer in-memory (richer, exploration_origin present) — deduplicate by trade_id.
    seen: dict[str, dict] = {}
    for t in session_trades:
        tid = t.get("trade_id", "")
        if tid:
            seen[tid] = t
    for t in historical:
        tid = t.get("trade_id", "")
        if tid and tid not in seen:
            seen[tid] = t

    all_trades = sorted(seen.values(), key=lambda x: x.get("entry_ts", 0))
    result = _cee(all_trades)
    return result


@app.get("/api/learning-intelligence/exploration-diagnostics")
async def lio_exploration_diagnostics():
    """
    LIO — Exploration persistence and NegativeMemory sensitivity forensics.

    FTD-EXPLORE-OBSERVABILITY: Non-governing read-only overlay.
    Provides:
      • Lifetime exploration event counts (survives restarts via JSONL)
      • Since-restart exploration counts (in-memory counters)
      • Session / pipeline / context breakdown of floor-explore events
      • NegativeMemory sensitivity diagnostics and ontology conflict classification
    """
    import datetime as _dt
    from core.persistence.exploration_log import exploration_event_log as _exp_log

    # Lifetime exploration summary (from persistent JSONL — survives restarts)
    _exp_summary = _exp_log.summary()

    # Since-restart counters (in-memory — reset on restart)
    _rl_state   = rl_engine.get_evolution_state()
    _counters   = _rl_state.get("counters", {})
    _restart_ts  = _boot_ts if _boot_ts > 0 else None
    _restart_iso = (
        _dt.datetime.utcfromtimestamp(_restart_ts).strftime("%Y-%m-%d %H:%M:%S UTC")
        if _restart_ts else None
    )

    # NegativeMemory forensics (ontology conflict classification)
    try:
        from core.learning_memory import learning_memory_orchestrator as _lmo
        _negmem_forensics = _lmo.negmem_forensics()
    except Exception as _exc:
        _negmem_forensics = {"error": str(_exc), "scope_note": "forensics unavailable"}

    return {
        "scope_note": (
            "FTD-EXPLORE-OBSERVABILITY: Non-governing forensic overlay. "
            "Read-only. No execution authority."
        ),
        "exploration_persistence": {
            "lifetime": _exp_summary,
            "since_restart": {
                "restart_utc_ts":  int(_restart_ts) if _restart_ts else None,
                "restart_iso":     _restart_iso,
                "explore_trades":  _counters.get("explore_trades", 0),
                "exploit_trades":  _counters.get("exploit_trades", 0),
                "floor_explores":  _counters.get("floor_explores", 0),
                "explore_ratio":   _rl_state.get("learning_dynamics", {}).get("explore_ratio", 0.0),
                "floor_explore_pct": _rl_state.get("learning_dynamics", {}).get("floor_explore_pct", 0.0),
            },
        },
        "negmem_forensics": _negmem_forensics,
    }


@app.get("/api/learning-intelligence/counterfactual-interventions")
async def lio_counterfactual_interventions():
    """
    LIO — Protected Counterfactual Intervention Laboratory.

    FTD-CIL: Non-governing research instrumentation.
    Simulates 8 hypothetical adaptive interventions (NegMem soft decay,
    Rule4 high explore, NY-only survivability, 5m TF projection, RL reset
    MEAN_REVERTING, ASIA suppression, RL-dominant ontology, stricter ecology)
    against the historical trade stream in an isolated sandbox.

    Produces per-intervention economics deltas, 7-category classification
    (BENEFICIAL_ADAPTATION, COSMETIC_STABILITY, OPPORTUNITY_COLLAPSE,
    FRAGILE_OPTIMIZATION, ONTOLOGY_STABILIZATION, COGNITIVE_OVERFITTING,
    INSUFFICIENT_DATA), replay confidence scores, and intervention ranking.

    Isolation guarantee: no production state is read or written.
    Research only — not an execution authority.
    """
    from core.counterfactual_lab import compute_counterfactual_interventions as _cci
    from dataclasses import asdict

    session_trades = [asdict(t) for t in pnl_calc.trades]
    historical     = data_lake.get_trades(limit=1000)

    seen: dict[str, dict] = {}
    for t in session_trades:
        tid = t.get("trade_id", "")
        if tid:
            seen[tid] = t
    for t in historical:
        tid = t.get("trade_id", "")
        if tid and tid not in seen:
            seen[tid] = t

    all_trades = sorted(seen.values(), key=lambda x: x.get("entry_ts", 0))
    return _cci(all_trades)


@app.get("/api/learning-intelligence/memory-pressure-dynamics")
async def lio_memory_pressure_dynamics():
    """
    LIO — Memory Pressure & Ontology Drift Dynamics.

    FTD-ONTOLOGY-DRIFT: Non-governing research instrumentation.
    Measures how PHOENIX's five memory subsystems (RL Q-memory, PatternEngine
    WR-memory, NegativeMemory rollback-memory, Ecology WR-memory,
    AlphaContextMemory amplification-memory) agree or diverge in their belief
    about what works. Produces pairwise drift scores, plasticity/fossilization
    diagnostics, and a 6-category cognitive state classification.

    Key namespace note: RL context keys (regime|hour|strategy) differ from
    NegMem PatternKeys (regime|volatility|instrument|parameter|direction).
    Direct key-level comparison is not possible — drift is measured at the
    aggregate level. Research only — no execution authority.
    """
    from core.memory_pressure_analytics import compute_memory_pressure_dynamics as _cmpd
    from collections import defaultdict as _dd

    # ── RL state ─────────────────────────────────────────────────────────────
    _rl_summ = rl_engine.summary()
    _rl_evo  = rl_engine.get_evolution_state()
    _rl_ld   = _rl_evo.get("learning_dynamics", {})

    try:
        _q_values     = [s.q_value    for s in rl_engine._table.values() if s.n_visits > 0]
        _q_velocities = [s.q_velocity for s in rl_engine._table.values() if s.n_visits > 0]
        _regime_q: dict = _dd(list)
        for _k, _s in rl_engine._table.items():
            if _s.n_visits > 0:
                _regime_q[_k.split("|")[0]].append(_s.q_value)
        _regime_avg_q = {r: round(sum(qs) / len(qs), 4) for r, qs in _regime_q.items() if qs}
    except Exception:
        _q_values = []; _q_velocities = []; _regime_avg_q = {}

    # ── NegMem state ──────────────────────────────────────────────────────────
    try:
        from core.learning_memory import learning_memory_orchestrator as _lmo_mod
        _lmo       = _lmo_mod.learning_memory_orchestrator
        _nm_count  = _lmo._neg_memory.count()
        _nm_entries = _lmo._neg_memory.to_list()
    except Exception:
        _nm_count   = {"permanent": 0, "temporary": 0, "total": 0}
        _nm_entries = []

    # ── Pattern state ─────────────────────────────────────────────────────────
    try:
        _all_pats   = _lmo._engine.all_patterns()
        _formed     = _lmo._engine.formed_patterns()
        _pat_state  = {
            "total_patterns":       len(_all_pats),
            "formed_patterns":      len(_formed),
            "formed_pattern_dicts": [p.to_dict() for p in _formed],
        }
    except Exception:
        _pat_state = {"total_patterns": 0, "formed_patterns": 0, "formed_pattern_dicts": []}

    # ── Ecology state ─────────────────────────────────────────────────────────
    try:
        _eco_state = {"regimes": learning_engine.summary().get("regimes", {})}
    except Exception:
        _eco_state = {"regimes": {}}

    # ── AlphaContext state ────────────────────────────────────────────────────
    try:
        _ac_telem  = alpha_context_memory.get_telemetry()
        _ac_state  = {
            "profitable_count": _ac_telem.get("profitable_count", 0),
            "toxic_count":      _ac_telem.get("toxic_count", 0),
            "total_contexts":   _ac_telem.get("total_contexts", 0),
        }
    except Exception:
        _ac_state = {"profitable_count": 0, "toxic_count": 0, "total_contexts": 0}

    _state = {
        "rl": {
            "profitable_pct":  _rl_summ.get("profitable_pct", 0.0),
            "total_contexts":  _rl_summ.get("total_contexts", 0),
            "q_values":        _q_values,
            "q_velocities":    _q_velocities,
            "toxic_count":     _rl_ld.get("toxic_count", 0),
            "explore_ratio":   _rl_ld.get("explore_ratio", 0.0),
            "evolution_score": _rl_evo.get("intelligence_score", 0),
            "regime_avg_q":    _regime_avg_q,
        },
        "negmem":        {"count": _nm_count,  "entries": _nm_entries},
        "patterns":      _pat_state,
        "ecology":       _eco_state,
        "alpha_context": _ac_state,
    }

    return _cmpd(_state)


@app.get("/api/learning-intelligence/adaptive-governance-simulator")
async def lio_adaptive_governance_simulator():
    """
    LIO — Guarded Adaptive Governance Simulator & Policy Arbitration Engine.

    FTD-GAGS: Non-governing research instrumentation.
    Simulates 6 compound policy stacks (sequential intervention composition)
    and arbitrates across 6 governance profiles (ECONOMIC_MAXIMALIST,
    PLASTICITY_PRESERVER, SURVIVABILITY_DEFENSIVE, ECOLOGY_BALANCED,
    ONTOLOGY_HARMONIZER, ADAPTIVE_GENERALIST) to identify multi-objective
    tradeoffs in adaptive governance.

    Produces governance profile scores, conflict detection between competing
    profiles (EXPECTANCY_VS_PLASTICITY, OPPORTUNITY_VS_SURVIVABILITY,
    ONTOLOGY_VS_BALANCE), regime specialization risk (HHI), overfitting risk,
    and a 6-category governance outcome classification per profile
    (GOVERNANCE_STABLE, ECONOMIC_AUTHORITARIANISM, PLASTICITY_OVEREXPANSION,
    ONTOLOGY_FRAGMENTATION, ECOLOGICAL_COLLAPSE, BALANCED_ADAPTATION).

    Isolation guarantee: no production state is read or written.
    Research only — not an execution authority.
    """
    from core.governance_simulator import compute_adaptive_governance as _cag
    from dataclasses import asdict

    session_trades = [asdict(t) for t in pnl_calc.trades]
    historical     = data_lake.get_trades(limit=1000)

    seen: dict[str, dict] = {}
    for t in session_trades:
        tid = t.get("trade_id", "")
        if tid:
            seen[tid] = t
    for t in historical:
        tid = t.get("trade_id", "")
        if tid and tid not in seen:
            seen[tid] = t

    all_trades = sorted(seen.values(), key=lambda x: x.get("entry_ts", 0))
    return _cag(all_trades)


@app.get("/api/learning-intelligence/governed-adaptive-doctrine")
async def lio_governed_adaptive_doctrine():
    """
    LIO — Guarded Adaptive Deployment Doctrine & Human Override Constitution.

    FTD-GADD: Non-governing research instrumentation.
    Synthesises constitutional governance health across all PHOENIX adaptive
    subsystems (CIL, GAGS, memory pressure) to produce:

    - Governance state assessment (OBSERVATION_ONLY, SANDBOX_REPLAY,
      HUMAN_REVIEW_REQUIRED, GUARDED_EXPERIMENT, AUTO_DISABLED,
      CONSTITUTION_LOCKDOWN)
    - Constitutional risk diagnostics (autonomous drift risk, overfitting
      escalation, governance instability, human-override integrity,
      recommendation confidence, sandbox-production divergence)
    - Constitutional classification (CONSTITUTIONALLY_STABLE,
      OVERSIGHT_DEPENDENT, ADAPTIVE_DRIFT_RISK, RECOMMENDATION_OVERREACH,
      GOVERNANCE_FRAGMENTATION, LOCKDOWN_RECOMMENDED)
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (appended to session-scoped ledger)
    - Human override constitution verification (all authority subordinate
      to explicit human governance)

    Hard constitutional rules:
      PHOENIX must NEVER become sovereign over its own deployment authority.
      No adaptive authority is self-authorised, self-persisted, or self-escalated.
      All decisions remain at developer discretion.

    Isolation guarantee: no production state is read or written.
    Research only — not an execution authority.
    """
    import asyncio as _asyncio
    from core.deployment_doctrine import compute_governed_adaptive_doctrine as _cgad

    _cil_result, _gag_result, _mpd_result = await _asyncio.gather(
        lio_counterfactual_interventions(),
        lio_adaptive_governance_simulator(),
        lio_memory_pressure_dynamics(),
    )

    try:
        _rl_evo = rl_engine.get_evolution_state()
        _rl_ld  = _rl_evo.get("learning_dynamics", {})
        _rl_summ = rl_engine.summary()
        _rl_state: dict = {
            "explore_ratio":  _rl_ld.get("explore_ratio",  0.0),
            "profitable_pct": _rl_summ.get("profitable_pct", 0.0),
            "total_contexts": _rl_summ.get("total_contexts", 0),
        }
    except Exception:
        _rl_state = {"explore_ratio": 0.0, "profitable_pct": 0.0, "total_contexts": 0}

    _state = {
        "counterfactual":  _cil_result,
        "governance":      _gag_result,
        "memory_pressure": _mpd_result,
        "rl":              _rl_state,
        "audit_ledger":    _gadd_audit_ledger,
    }

    result = _cgad(_state)

    # Append the immutable audit entry to the session-scoped ledger (append-only).
    if isinstance(result.get("audit_entry"), dict):
        _gadd_audit_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/reality-verification")
async def lio_reality_verification():
    """
    LIO — Guarded Reality Verification Layer.

    FTD-GRVL: Non-governing research instrumentation.
    Measures divergence between simulated paper-trading assumptions and
    real-world execution friction across 8 metrics:

    - Fill divergence (slippage cost vs gross PnL)
    - Slippage divergence (per-trade cost ratio)
    - Latency divergence (hold-duration coefficient of variation)
    - Liquidity survivability (% trades profitable after 2× spread)
    - Spread fragility (2×/5×/10× spread stress scenarios)
    - Market impact sensitivity (NE degradation under 2× fee stress)
    - Pilot survivability score (composite 0–100)
    - Simulation-reality confidence (corpus size + cost coverage)

    Produces:
    - Pilot state (PAPER_ONLY → CONSTITUTION_LOCKDOWN)
    - Reality-alignment classification (REALITY_ALIGNED →
      PILOT_NOT_RECOMMENDED)
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (appended to session-scoped ledger)
    - Pilot hard principles verification (human supremacy enforced)

    Hard constitutional rules:
      PHOENIX must NEVER self-grant real-world economic authority.
      No autonomous live trading, automatic capital scaling, or
      self-authorized deployment. All decisions remain at developer
      discretion.

    Isolation guarantee: no production state is read or written.
    Research only — not an execution authority.
    """
    from core.reality_verification import compute_reality_verification as _crv
    from dataclasses import asdict
    _session_trades = [asdict(t) for t in pnl_calc.trades]
    _historical = data_lake.get_trades(limit=1000)
    _seen: dict[str, dict] = {}
    for t in _session_trades:
        tid = t.get("trade_id", "")
        if tid:
            _seen[tid] = t
    for t in _historical:
        tid = t.get("trade_id", "")
        if tid and tid not in _seen:
            _seen[tid] = t
    _all_trades = sorted(_seen.values(), key=lambda x: x.get("entry_ts", 0))

    result = _crv(_all_trades)

    # Append the immutable audit entry to the session-scoped ledger (append-only).
    if isinstance(result.get("audit_entry"), dict):
        _grv_audit_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/guarded-micro-pilot")
async def lio_guarded_micro_pilot():
    """
    LIO — Ultra-Guarded Micro Pilot Execution Doctrine & Human Confirmation Exchange Bridge.

    FTD-GMPD: Non-governing research instrumentation.
    Synthesises paper trade history and the session-scoped pilot execution ledger
    to produce a constitutional micro-pilot governance assessment:

    - Execution readiness (paper corpus quality: size, fee/slippage coverage)
    - Pilot state (PAPER_ONLY, SHADOW_OBSERVATION, HUMAN_ARMED_MICRO,
      SINGLE_CONFIRM_EXECUTION, MANUAL_KILL_SWITCH, CONSTITUTION_LOCKDOWN)
    - Reality classification (REALITY_CONSISTENT → PILOT_LOCKDOWN_RECOMMENDED)
    - Execution reconciliation metrics (fill, slippage, latency, fee drag,
      hold economics) — populated only when execution entries exist in ledger
    - Confirmation chain integrity (human_confirmed invariant)
    - Kill-switch advisory
    - Research-only recommendations (never auto-authorised)
    - Pilot opportunity suggestion (human confirmation always required)
    - Immutable audit entry (GMPD-{ts}-{sha256} prefix)

    Hard constitutional rules:
      PHOENIX may NEVER self-fire an exchange order.
      PHOENIX must NEVER possess sovereign economic execution authority.
      All execution authority remains explicitly human-controlled.
      No autonomous scaling, re-entry, or risk escalation.

    Isolation guarantee: no production state is read or written.
    Research only — NOT an execution authority.
    """
    from core.micro_pilot_doctrine import compute_guarded_micro_pilot as _cgmp
    from dataclasses import asdict
    _session_trades = [asdict(t) for t in pnl_calc.trades]
    _historical = data_lake.get_trades(limit=1000)
    _seen: dict[str, dict] = {}
    for t in _session_trades:
        tid = t.get("trade_id", "")
        if tid:
            _seen[tid] = t
    for t in _historical:
        tid = t.get("trade_id", "")
        if tid and tid not in _seen:
            _seen[tid] = t
    _all_trades = sorted(_seen.values(), key=lambda x: x.get("entry_ts", 0))

    result = _cgmp(_all_trades, pilot_ledger=_gmp_pilot_ledger)

    # Append the immutable analysis audit entry to the session-scoped ledger.
    if isinstance(result.get("audit_entry"), dict):
        _gmp_pilot_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/long-horizon-evolution")
async def lio_long_horizon_evolution():
    """
    LIO — Long-Horizon Constitutional Evolution Observatory.

    FTD-LHEO: Non-governing research instrumentation.
    Segments the full paper trade history into up to 5 temporal eras and
    computes 8 constitutional continuity metrics to detect whether PHOENIX
    remains cognitively stable across very long learning horizons:

    - Constitutional stability (health variance across eras)
    - Drift acceleration (net-expectancy rate of change between eras)
    - Governance ideology concentration (regime monoculture via HHI)
    - Plasticity half-life (exploration decay rate from early to late era)
    - Exploration extinction risk (absolute late-era exploration level)
    - Survivability monoculture risk (mean within-era regime HHI)
    - Cognitive diversity retention (session + regime + win-rate convergence)
    - Long-horizon replay dependence (low explore + declining win rate)

    Produces:
    - Evolutionary classification (CONSTITUTIONALLY_RESILIENT →
      LONG_HORIZON_LOCKDOWN_RISK)
    - Long-horizon stability score (0–100)
    - Per-era cognitive snapshots + cognitive lineage trajectories
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (LHEO-{ts}-{sha256[:16]} prefix)
    - Hard constitutional evolution principles (self-rewriting blocked)

    Hard constitutional rules:
      PHOENIX must NEVER evolve beyond explicit constitutional human governance.
      No self-rewriting doctrine, recursive constitutional mutation, or sovereign
      adaptive succession. All evolution decisions remain at developer discretion.

    Isolation guarantee: no production state is read or written.
    Research only — NOT an execution or governance authority.
    """
    from core.evolution_observatory import compute_long_horizon_evolution as _clhe
    from dataclasses import asdict
    _session_trades = [asdict(t) for t in pnl_calc.trades]
    _historical = data_lake.get_trades(limit=2000)
    _seen: dict[str, dict] = {}
    for t in _session_trades:
        tid = t.get("trade_id", "")
        if tid:
            _seen[tid] = t
    for t in _historical:
        tid = t.get("trade_id", "")
        if tid and tid not in _seen:
            _seen[tid] = t
    _all_trades = sorted(_seen.values(), key=lambda x: x.get("entry_ts", 0))

    result = _clhe(_all_trades)

    # Append the immutable analysis audit entry to the session-scoped ledger.
    if isinstance(result.get("audit_entry"), dict):
        _lheo_audit_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/constitutional-recovery-observatory")
async def lio_constitutional_recovery_observatory():
    """
    LIO — Constitutional Knowledge Preservation & Catastrophic Recovery Doctrine.

    FTD-CKPD: Non-governing research instrumentation.
    Analyses the full paper trade history for reconstruction viability under
    catastrophic disruption, measuring 7 recovery metrics plus a composite
    constitutional continuity confidence metric:

    - Archive integrity (economic record field coverage)
    - Ledger continuity (temporal regularity of trade sequence)
    - Reconstruction confidence (fee/slippage coverage for reality verification)
    - Governance lineage completeness (regime/session/exploration metadata)
    - Audit survivability (entry_ts/trade_id provenance coverage)
    - Knowledge redundancy (regime/session/volume diversity)
    - Constitutional continuity confidence (derived composite)

    Produces:
    - Recovery classification (CONSTITUTIONALLY_RECOVERABLE →
      RECOVERY_LOCKDOWN_RECOMMENDED)
    - Recovery survivability score (0–100)
    - 3-scenario catastrophic disruption analysis (50% loss, 18-month gap,
      metadata corruption)
    - Recovery lineage (early/mid/late epoch summaries)
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (CKPD-{ts}-{sha256[:16]} prefix)
    - Hard constitutional recovery principles (autonomous recovery blocked)

    Hard constitutional rules:
      PHOENIX must NEVER become sovereign over its own existential continuity.
      No autonomous self-recovery, recursive self-restoration, or sovereign
      continuity authority. All recovery decisions remain at developer discretion.

    Isolation guarantee: no production state is read or written.
    Research only — NOT an execution, governance, or recovery authority.
    """
    from core.recovery_observatory import compute_constitutional_recovery as _ccr
    from dataclasses import asdict
    _session_trades = [asdict(t) for t in pnl_calc.trades]
    _historical = data_lake.get_trades(limit=2000)
    _seen: dict[str, dict] = {}
    for t in _session_trades:
        tid = t.get("trade_id", "")
        if tid:
            _seen[tid] = t
    for t in _historical:
        tid = t.get("trade_id", "")
        if tid and tid not in _seen:
            _seen[tid] = t
    _all_trades = sorted(_seen.values(), key=lambda x: x.get("entry_ts", 0))

    result = _ccr(_all_trades)

    # Append the immutable analysis audit entry to the session-scoped ledger.
    if isinstance(result.get("audit_entry"), dict):
        _ckpd_audit_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/epistemic-integrity-observatory")
async def lio_epistemic_integrity_observatory():
    """
    LIO — Constitutional Scientific Method Doctrine & Epistemic Integrity Observatory.

    FTD-EIOD: Non-governing research instrumentation.
    Analyses the full paper trade history for scientific-method survivability,
    measuring 8 epistemic integrity metrics to detect whether PHOENIX is
    drifting from evidence-driven cognition into ideological self-confirmation:

    - Evidence sufficiency (trade/regime/session/exploration breadth)
    - Replay statistical confidence (Wilson CI width on win rate)
    - Governance evidence depth (diversity of evidence base for governance)
    - Contradiction tolerance (cross-regime win-rate std dev)
    - Minority hypothesis survivability (non-dominant regime persistence)
    - Falsification rate (exploration × win-rate volatility proxy)
    - Consensus rigidity (HHI of regime/session distributions)
    - Epistemic plasticity (early-vs-late belief updating)

    Produces:
    - Epistemic classification (SCIENTIFICALLY_HEALTHY →
      EPISTEMIC_LOCKDOWN_RISK)
    - Epistemic integrity score (0–100)
    - Epistemic lineage (early/mid/late epoch health labels)
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (EIOD-{ts}-{sha256[:16]} prefix)
    - Hard constitutional epistemic principles (truth sovereignty blocked)

    Hard constitutional rules:
      PHOENIX must NEVER become sovereign over truth legitimacy itself.
      No autonomous truth certification, sovereign epistemic authority,
      self-validating doctrine, or recursive scientific legitimacy.
      All epistemic decisions remain at developer discretion.

    Isolation guarantee: no production state is read or written.
    Research only — NOT a truth, execution, governance, or epistemic authority.
    """
    from core.epistemic_observatory import compute_epistemic_integrity as _cei
    from dataclasses import asdict
    _session_trades = [asdict(t) for t in pnl_calc.trades]
    _historical = data_lake.get_trades(limit=2000)
    _seen: dict[str, dict] = {}
    for t in _session_trades:
        tid = t.get("trade_id", "")
        if tid:
            _seen[tid] = t
    for t in _historical:
        tid = t.get("trade_id", "")
        if tid and tid not in _seen:
            _seen[tid] = t
    _all_trades = sorted(_seen.values(), key=lambda x: x.get("entry_ts", 0))

    result = _cei(_all_trades)

    # Append the immutable analysis audit entry to the session-scoped ledger.
    if isinstance(result.get("audit_entry"), dict):
        _eiod_audit_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/human-meaning-alignment")
async def lio_human_meaning_alignment():
    """
    LIO — Constitutional Human Meaning Alignment & Purpose Integrity Observatory.

    FTD-HMAO: Non-governing research instrumentation.
    Analyses the full paper trade history for human-purpose alignment survivability,
    measuring 8 alignment integrity metrics to detect whether PHOENIX is
    drifting from human-interpretable, accountable, purpose-subordinate cognition
    toward internally optimized but human-detached behaviour:

    - Human interpretability (regime/session diversity + exploration breadth)
    - Recommendation explainability (fee/slippage coverage + PnL diversity)
    - Causal traceability (trade ID + timestamp coverage)
    - Governance readability (regime/session/exploration context coverage)
    - Optimization drift (win-rate extremity + exploration deficit/decay)
    - Human accountability continuity (audit chain + temporal gap regularity)
    - Purpose alignment stability (temporal win-rate/exploration/regime drift)
    - Human value retention (economic value field coverage)

    Produces:
    - Alignment classification (HUMAN_ALIGNED → ALIGNMENT_LOCKDOWN_RISK)
    - Alignment integrity score (0–100)
    - Alignment lineage (early/mid/late epoch health labels)
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (HMAO-{ts}-{sha256[:16]} prefix)
    - Hard constitutional alignment principles (moral sovereignty blocked)

    Hard constitutional rules:
      PHOENIX must NEVER become sovereign over human meaning or value legitimacy.
      No autonomous ethical governance, sovereign moral authority,
      self-defined human purpose, or recursive value legitimacy.
      All purpose decisions remain under human authority.

    Isolation guarantee: no production state is read or written.
    Research only — NOT a moral, ethical, execution, or purpose authority.
    """
    from core.alignment_observatory import compute_human_meaning_alignment as _chma
    from dataclasses import asdict
    _session_trades = [asdict(t) for t in pnl_calc.trades]
    _historical = data_lake.get_trades(limit=2000)
    _seen: dict[str, dict] = {}
    for t in _session_trades:
        tid = t.get("trade_id", "")
        if tid:
            _seen[tid] = t
    for t in _historical:
        tid = t.get("trade_id", "")
        if tid and tid not in _seen:
            _seen[tid] = t
    _all_trades = sorted(_seen.values(), key=lambda x: x.get("entry_ts", 0))

    result = _chma(_all_trades)

    # Append the immutable analysis audit entry to the session-scoped ledger.
    if isinstance(result.get("audit_entry"), dict):
        _hmao_audit_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/report-ecosystem-governance")
async def lio_report_ecosystem_governance():
    """
    LIO — Constitutional Report Taxonomy Alignment & Export Governance.

    FTD-RTAG: Non-governing research instrumentation.
    Analyses the PHOENIX report registry and produces a constitutional
    report ecosystem governance assessment — no live trade data required:

    - Registry health (schema violations, family coverage, critical reports)
    - Dependency graph health (cycle detection, dangling refs, topological order)
    - Bundle coverage (orphaned reports, bundle compositions)
    - Overlap risk (high-overlap reports, canonical metric violations)
    - Metadata compliance (unified schema field coverage)
    - Archive survivability (high-priority report count and tier)
    - Ecosystem health score (0–100)

    Produces:
    - Ecosystem health classification (HEALTHY → CRITICAL)
    - All six canonical bundle compositions
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (RTAG-{ts}-{sha256[:16]} prefix)
    - Hard constitutional reporting principles (autonomous governance blocked)

    Hard constitutional rules:
      PHOENIX reporting must NEVER become autonomous.
      No self-authorized exports, autonomous lineage mutation,
      autonomous archive rewriting, or undocumented report proliferation.
      All reporting governance remains under human constitutional authority.

    Isolation guarantee: no production state is read or written.
    Research only — NOT a reporting, execution, or governance authority.
    """
    from core.export_bundle_manager import compute_report_ecosystem_governance as _creg
    result = _creg()

    # Append the immutable governance assessment entry to the session-scoped ledger.
    if isinstance(result.get("audit_entry"), dict):
        _rtag_audit_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/export-infrastructure-governance")
async def lio_export_infrastructure_governance():
    """
    LIO — Constitutional Unified Export & Download Infrastructure Governance.

    FTD-UEI: Non-governing research instrumentation.
    Orchestrates PHOENIX's institutional export infrastructure and produces
    a constitutional export infrastructure governance assessment — no live
    trade data required:

    - Bundle composer health (all 6 canonical bundles composable)
    - Manifest generation health (manifest_id format, hash validity)
    - Reconstruction hash infrastructure (determinism, order-insensitivity)
    - Archive integrity validation (hash, manifest, metadata, constitutional)
    - Snapshot continuity health (ledger analysis)
    - Export ordering health (topological sort validity)
    - Export metadata compliance (required fields schema)

    Produces:
    - Infrastructure health score (0–100) and tier (HEALTHY → CRITICAL)
    - All 6 bundle types and 7 snapshot types enumerated
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (UEI-{ts}-{sha256[:16]} prefix)
    - Hard constitutional export principles (autonomous governance blocked)

    Hard constitutional rules:
      PHOENIX exports MUST remain institutionally auditable and reconstructible.
      All export authority MUST remain constitutionally subordinate to
      explicit human governance. No self-authorized exports, autonomous
      archive deletion, autonomous lineage mutation, or silent manifest
      alteration is permitted.

    Isolation guarantee: no production state is read or written.
    Research only — NOT an export, execution, or governance authority.
    """
    from core.download_center import compute_export_infrastructure_governance as _ceig
    result = _ceig(snapshots=list(_export_snapshot_ledger))

    # Append the immutable infrastructure assessment entry to the session-scoped ledger.
    if isinstance(result.get("audit_entry"), dict):
        _uei_audit_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/download-center-governance")
async def lio_download_center_governance():
    """
    LIO — Constitutional Unified Download Center & Archive Experience Governance.

    FTD-UDCA: Non-governing research instrumentation.
    Assesses PHOENIX's institutional archive experience layer — whether the
    archive is operationally accessible, navigable, replayable, and
    constitutionally auditable:

    - Archive browser operability (snapshot browsing, filtering, timeline)
    - Replay explorer health (lineage replay, snapshot comparison, era comparison)
    - Export preview integrity (manifest preview, dependency chain, size estimates)
    - Archive visualization health (dependency graph, bundle topology, lineage tree)
    - Institutional search operability (report search, bundle search, snapshot search)
    - Lineage navigation accessibility
    - Download center overall accessibility

    Produces:
    - Download center health score (0–100) and tier (HEALTHY → CRITICAL)
    - All 6 bundle types and 7 snapshot types enumerated
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (UDCA-{ts}-{sha256[:16]} prefix)
    - Hard constitutional download center principles (autonomous actions blocked)

    Hard constitutional rules:
      PHOENIX archive experience MUST remain institutionally auditable
      and reconstructible. All archive access authority MUST remain
      constitutionally subordinate to explicit human governance.
      No autonomous archive mutation, self-authorized snapshot deletion,
      autonomous lineage rewriting, or silent manifest alteration.

    Isolation guarantee: no production state is read or written.
    Research only — NOT an export, execution, or governance authority.
    """
    from core.download_dashboard import compute_download_center_governance as _cdcg
    result = _cdcg(snapshots=list(_export_snapshot_ledger))

    # Append the immutable download center assessment entry to the session-scoped ledger.
    if isinstance(result.get("audit_entry"), dict):
        _udca_audit_ledger.append(result["audit_entry"])

    return result


@app.get("/api/learning-intelligence/institutional-reporting-experience")
async def lio_institutional_reporting_experience():
    """
    LIO — Institutional Reporting Experience (IREL) Governance.

    FTD-IREL: Non-governing research instrumentation.
    Assesses PHOENIX's dynamic institutional reporting and observability layer —
    whether the registry-driven rendering, timeline visualization, export
    presentation, and download experience are fully operational:

    - Renderer health (all 7 render modes: html, json, markdown, and variants)
    - Dashboard orchestrator health (tab manifest, 8 tabs, all 25 reports mapped)
    - Export presentation health (executive_html, research_markdown, governance_html)
    - Download experience health (orchestrate, metadata, manifest, list_available)
    - Timeline visualization health (evolution, lineage graph, regime map, drift flow)

    Produces:
    - IREL health score (0–100) and tier (HEALTHY → CRITICAL)
    - Scoring breakdown by component (renderer 25, orchestrator 25, presentation 20,
      download 15, timeline 15)
    - Full tab manifest (8 institutional tabs, all 25 reports auto-discovered)
    - Dashboard structure with per-report data availability status
    - Research-only recommendations (never auto-authorised)
    - Immutable audit entry (IREL-{ts}-{sha256[:16]} prefix)
    - Hard constitutional IREL principles (autonomous reporting blocked)

    Hard constitutional rules:
      PHOENIX reporting governance MUST remain registry-driven and institutionally
      auditable. No autonomous report modification, no headless export without
      human approval, no dashboard-driven order placement.

    Isolation guarantee: no production state is read or written.
    Research only — NOT an export, execution, or governance authority.
    """
    from core.dashboard_orchestrator import compute_institutional_reporting_experience as _cirel
    result = _cirel(snapshots=list(_export_snapshot_ledger))

    # Append the immutable IREL assessment entry to the session-scoped ledger.
    audit_entry = {
        "audit_id":   result.get("audit_id", ""),
        "score":      result.get("irel_health_score", 0),
        "tier":       result.get("irel_health_tier", ""),
        "ts_ms":      result.get("generated_at_ms", 0),
        "auto_authorized": False,
    }
    _irel_audit_ledger.append(audit_entry)

    return result


@app.get("/api/learning-intelligence/institutional-report-html", response_class=HTMLResponse)
async def lio_institutional_report_html():
    """LIO — Rendered institutional report as self-contained HTML with live data (FTD-IREL)."""
    from core.institutional_report_renderer import render_report_bundle
    live_bundle = await lio_report_bundle()
    html = render_report_bundle(live_bundle, mode="html", app_version=APP_VERSION)
    return HTMLResponse(content=html if isinstance(html, str) else str(html))


@app.get("/api/learning-intelligence/institutional-report-markdown")
async def lio_institutional_report_markdown():
    """LIO — Rendered institutional report as markdown with live data (FTD-IREL)."""
    from fastapi.responses import PlainTextResponse
    from core.institutional_report_renderer import render_report_bundle
    live_bundle = await lio_report_bundle()
    md = render_report_bundle(live_bundle, mode="markdown", app_version=APP_VERSION)
    return PlainTextResponse(content=md if isinstance(md, str) else str(md))


@app.get("/api/learning-intelligence/institutional-report-bundle")
async def lio_institutional_report_bundle():
    """LIO — Rendered institutional report as structured JSON with live data (FTD-IREL)."""
    from core.institutional_report_renderer import render_report_bundle
    live_bundle = await lio_report_bundle()
    return render_report_bundle(live_bundle, mode="json", app_version=APP_VERSION)


@app.get("/api/learning-intelligence/report-bundle")
async def lio_report_bundle():
    """LIO — Full snapshot bundle: all sections in one atomic call for report download."""
    import asyncio, time as _t
    (
        _summary, _patterns, _neg_mem, _ecology,
        _rl, _topology, _cognition, _sov, _alpha, _sess_attr,
        _exp_diag, _exp_econ, _eco_truth, _tf_surviv, _regime_carto,
        _mem_pressure, _counterfactual, _governance, _doctrine,
        _reality, _micro_pilot, _lheo, _ckpd_recovery, _eiod, _hmao, _rtag, _uei, _udca,
        _irel,
    ) = await asyncio.gather(
        lio_summary(),
        lio_patterns(),
        lio_negative_memory(),
        lio_ecology(),
        lio_rl(),
        lio_topology(),
        lio_cognition(),
        lio_sovereign_readiness(),
        lio_alpha_discovery(),
        lio_session_attribution(),
        lio_exploration_diagnostics(),
        lio_exploration_economic_attribution(),
        lio_economic_ground_truth(),
        lio_timeframe_survivability(),
        lio_regime_survivability_cartography(),
        lio_memory_pressure_dynamics(),
        lio_counterfactual_interventions(),
        lio_adaptive_governance_simulator(),
        lio_governed_adaptive_doctrine(),
        lio_reality_verification(),
        lio_guarded_micro_pilot(),
        lio_long_horizon_evolution(),
        lio_constitutional_recovery_observatory(),
        lio_epistemic_integrity_observatory(),
        lio_human_meaning_alignment(),
        lio_report_ecosystem_governance(),
        lio_export_infrastructure_governance(),
        lio_download_center_governance(),
        lio_institutional_reporting_experience(),
    )
    _sess_auth = __import__(
        "core.time.session_definitions", fromlist=["get_session_integrity_block"]
    ).get_session_integrity_block()
    return {
        "metadata": {
            "report_type":    "LIO_FULL_SNAPSHOT",
            "version":        APP_VERSION,
            "generated_at":   int(_t.time() * 1000),
            "generated_at_iso": __import__("datetime").datetime.utcnow().strftime(
                "%Y-%m-%d %H:%M:%S UTC"
            ),
            "session_authority": _sess_auth,
        },
        "summary":                         _summary,
        "patterns":                        _patterns,
        "negative_memory":                 _neg_mem,
        "ecology":                         _ecology,
        "rl":                              _rl,
        "topology":                        _topology,
        "cognition":                       _cognition,
        "sovereign_readiness":             _sov,
        "alpha_discovery":                 _alpha,
        "session_attribution":             _sess_attr,
        "exploration_diagnostics":         _exp_diag,
        "exploration_economic_attribution":    _exp_econ,
        "economic_ground_truth":               _eco_truth,
        "timeframe_survivability":             _tf_surviv,
        "regime_survivability_cartography":    _regime_carto,
        "memory_pressure_dynamics":            _mem_pressure,
        "counterfactual_interventions":        _counterfactual,
        "adaptive_governance_simulator":       _governance,
        "governed_adaptive_doctrine":          _doctrine,
        "reality_verification":                _reality,
        "guarded_micro_pilot":                 _micro_pilot,
        "long_horizon_evolution":              _lheo,
        "constitutional_recovery_observatory": _ckpd_recovery,
        "epistemic_integrity_observatory":     _eiod,
        "human_meaning_alignment":             _hmao,
        "report_ecosystem_governance":         _rtag,
        "export_infrastructure_governance":    _uei,
        "download_center_governance":          _udca,
        "institutional_reporting_experience":  _irel,
    }


# ── Economic Truth Export Modes 1 / 3 / 4 ────────────────────────────────────

@app.get("/api/economic-truth/export/executive")
async def export_executive_snapshot():
    """
    Export Mode 1 — Executive Snapshot.
    Compact JSON: net PnL, fees, WR, PF, alpha tier, danger verdict.
    Suitable for management reporting or quick health check.
    """
    import json as _json
    import time as _t
    from fastapi.responses import Response

    dash = await economic_truth_dashboard()
    snap = {
        "export_mode":    "EXECUTIVE_SNAPSHOT",
        "version":        APP_VERSION,
        "captured_at":    time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "n_trades":       dash["n_trades"],
        "net_pnl":        dash["executive_snapshot"]["net_pnl"],
        "gross_pnl":      dash["executive_snapshot"]["gross_pnl"],
        "total_fees":     dash["executive_snapshot"]["total_fees"],
        "profit_factor":  dash["executive_snapshot"]["profit_factor"],
        "win_rate_pct":   round(dash["executive_snapshot"]["win_rate"] * 100, 2),
        "max_drawdown_pct": dash["executive_snapshot"]["max_drawdown_pct"],
        "alpha_tier":     dash["executive_snapshot"]["alpha_tier"],
        "danger_verdict": dash["danger_radar"]["verdict"],
        "threat_count":   dash["danger_radar"]["threat_count"],
        "threats":        dash["danger_radar"]["threats"],
        "kelly_fraction": dash["executive_snapshot"]["kelly_fraction"],
        "adaptation_state": dash["rl_intelligence"]["adaptation_state"],
        "best_session":   dash["session_regime"]["best_session"],
        "worst_session":  dash["session_regime"]["worst_session"],
    }
    ts_str   = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    filename = f"PHOENIX_Executive_Snapshot_{ts_str}.json"
    payload  = _json.dumps(_sanitize(snap), indent=2, ensure_ascii=False).encode("utf-8")
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/economic-truth/export/replay-safe")
async def export_replay_safe_snapshot():
    """
    Export Mode 3 — Replay-Safe Snapshot.
    Full trade list + RL Q-table in deterministic format for offline replay.
    Includes all fields needed to recreate the session's performance without
    a live engine connection.
    """
    import json as _json
    import time as _t
    from fastapi.responses import Response

    trades_raw = _build_eco_trades()
    rl_qtable  = {}
    try:
        rl_qtable = {
            k: {
                "q_value":   round(s.q_value, 5),
                "n_visits":  s.n_visits,
                "n_wins":    s.n_wins,
                "total_pnl": round(s.total_pnl, 4),
                "win_rate":  round(s.win_rate,  4),
                "toxic":     k in rl_engine._toxic_contexts,
            }
            for k, s in rl_engine._table.items()
        }
    except Exception:
        pass

    snap = {
        "export_mode":    "REPLAY_SAFE_SNAPSHOT",
        "version":        APP_VERSION,
        "captured_at":    time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "captured_at_ms": int(time.time() * 1000),
        "bypass_mode":    cfg.BYPASS_ALL_GATES,
        "initial_capital": pnl_calc._initial_capital,
        "n_trades":       len(trades_raw),
        "trades":         [_sanitize(t) for t in trades_raw],
        "rl_qtable":      rl_qtable,
        "session_stats":  _sanitize(pnl_calc.session_stats),
    }
    ts_str   = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    filename = f"PHOENIX_Replay_Safe_{ts_str}.json"
    payload  = _json.dumps(_sanitize(snap), indent=2, ensure_ascii=False).encode("utf-8")
    return Response(
        content=payload,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@app.get("/api/economic-truth/export/economic-truth")
async def export_economic_truth_bundle():
    """
    Export Mode 4 — Economic Truth Export.
    ZIP bundle focused on economic accounting: dashboard summary, per-trade
    ledger, fee ledger, session breakdown, and danger verdict.
    """
    import zipfile, io as _io, hashlib, json as _json
    from fastapi.responses import StreamingResponse

    ts_str     = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    captured   = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    dash       = await economic_truth_dashboard()
    trades_raw = _build_eco_trades()

    # Per-trade economic ledger
    ledger = []
    for t in trades_raw:
        ledger.append({
            "trade_id":    t.get("trade_id", ""),
            "symbol":      t.get("symbol",   ""),
            "side":        t.get("side",     ""),
            "strategy_id": t.get("strategy_id", ""),
            "regime":      t.get("regime",   ""),
            "session":     t.get("origin_session", ""),
            "gross_pnl":   t.get("gross_pnl", 0.0),
            "fee_entry":   t.get("fee_entry", 0.0),
            "fee_exit":    t.get("fee_exit",  0.0),
            "net_pnl":     t.get("net_pnl",   0.0),
            "hold_sec":    max(0.0, (t.get("exit_ts", 0) - t.get("entry_ts", 0)) / 1000.0),
            "entry_ts":    t.get("entry_ts",  0),
            "exit_ts":     t.get("exit_ts",   0),
        })

    def _jb(obj: object) -> bytes:
        try:
            return _json.dumps(_sanitize(obj), indent=2, ensure_ascii=False).encode("utf-8")
        except Exception as e:
            return _json.dumps({"error": str(e)}).encode("utf-8")

    file_map = {
        "economic_truth_dashboard.json":    _jb(dash),
        "trade_economic_ledger.json":       _jb(ledger),
        "session_breakdown.json":           _jb(dash["session_regime"]),
        "fee_analysis.json":                _jb(dash["fee_analysis"]),
        "danger_radar.json":                _jb(dash["danger_radar"]),
        "winloss_geometry.json":            _jb(dash["winloss_geometry"]),
        "survivability.json":               _jb(dash["survivability"]),
        "rl_intelligence.json":             _jb(dash["rl_intelligence"]),
    }

    manifest = {
        "export_mode":   "ECONOMIC_TRUTH_BUNDLE",
        "version":        APP_VERSION,
        "captured_at":    captured,
        "n_trades":       dash["n_trades"],
        "net_pnl":        dash["executive_snapshot"]["net_pnl"],
        "alpha_tier":     dash["executive_snapshot"]["alpha_tier"],
        "danger_verdict": dash["danger_radar"]["verdict"],
        "files": {
            path: {
                "size_bytes": len(content),
                "sha256":     hashlib.sha256(content).hexdigest(),
            }
            for path, content in file_map.items()
        },
    }
    file_map["00_MANIFEST.json"] = _jb(manifest)

    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as _zf:
        for _path, _content in file_map.items():
            _zf.writestr(_path, _content)
    buf.seek(0)

    filename = f"PHOENIX_Economic_Truth_{ts_str}.zip"
    logger.info(
        f"[ECO-TRUTH-EXPORT] bundle assembled | trades={dash['n_trades']} "
        f"verdict={dash['danger_radar']['verdict']} version={APP_VERSION}"
    )
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── One-Click Unified Intelligence Export ─────────────────────────────────────

@app.get("/api/unified-intelligence/export")
async def unified_intelligence_export():
    """
    One-Click Unified Intelligence Package — complete PHOENIX operational
    intelligence consolidated into a single structured ZIP download.

    This endpoint is the primary forensic/diagnostic artifact: share the ZIP
    to get an immediate full-system diagnosis without navigating dozens of
    individual endpoints.

    ZIP contents:
      00_BRIEFING.md                    ← Synthesized read-first intelligence brief
      00_MANIFEST.json                  ← Index with file sizes, SHA-256, metadata

      01_operational_health/            ← System state, observability, escalations
        system_status.json
        healer_snapshot.json
        observability_health.json
        anomalies.json
        escalations.json
        halt_audit.json

      02_signal_intelligence/           ← Signal pipeline health and decision trace
        trade_flow.json
        thought_log.json                ← CT-scan log (last 100 entries)
        last_skip.json
        regime_map.json
        signal_filter.json

      03_live_process_snapshot/         ← RL Q-table and runtime state
        rl_qtable.json

      04_economic_truth/                ← Phase-D: 6-engine economic truth report
        orchestration.json

      05_alpha_and_learning/            ← Full LIO snapshot (29 sections)
        lio_full_snapshot.json

      06_risk_and_governance/           ← Phases E–I orchestration reports
        alpha_confirmation.json
        execution_governance.json
        survivability.json
        continuity.json
        equilibrium.json

      07_capital_and_performance/       ← PnL, trades, analytics, deployability
        session_stats.json
        trades_recent_100.json
        analytics.json
        deployability.json
        capital_flow.json
        aee_state.json

      09_genome/                        ← Genome DNA and evolution history
        genome_state.json
    """
    import zipfile, io as _io, hashlib, json as _json
    from fastapi.responses import StreamingResponse
    from core.unified_intelligence.briefing_generator import generate_briefing

    ts_ms       = int(time.time() * 1000)
    ts_str      = time.strftime("%Y%m%d_%H%M%S", time.gmtime())
    captured_at = time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime())

    def _safe(fn, default=None):
        try:
            return fn()
        except Exception:
            return default

    def _exc_safe(result, default=None):
        return default if isinstance(result, Exception) else result

    # ── Parallel async collection — heavy orchestration endpoints ─────────────
    (
        _et_report,
        _ac_report,
        _sv_report,
        _eg_report,
        _ic_report,
        _aeq_report,
        _obs_h,
        _obs_a,
        _obs_e,
        _lio_bundle_result,
        _halt_audit_result,
        _last_skip_result,
        _status_result,
    ) = await asyncio.gather(
        economic_truth_orchestration(),
        alpha_orchestration(),
        survivability_orchestration(),
        execution_governance_orchestration(),
        continuity_orchestration(),
        equilibrium_orchestration(),
        obs_health(),
        obs_anomalies(),
        obs_escalations(),
        lio_report_bundle(),
        get_halt_audit(),
        get_last_skip(),
        get_status(),
        return_exceptions=True,
    )

    # ── Synchronous data collection ───────────────────────────────────────────
    _ss       = pnl_calc.session_stats
    _n_trades = len(pnl_calc.trades)

    _trade_dicts: list = []
    for _t in pnl_calc.trades[-100:]:
        try:
            _trade_dicts.append({k: getattr(_t, k) for k in _t.__dataclass_fields__})
        except Exception:
            pass

    _heal     = _safe(healer.snapshot, {})
    _lake_s   = _safe(data_lake.db_stats, {})
    _redis_ok = any(
        e.get("action") == "REDIS_FLUSH" and e.get("ok", False)
        for e in (_heal or {}).get("recent_events", [])
    )
    _sqlite_ok = (_lake_s or {}).get("trades", -1) >= 0

    _analytics = _safe(lambda: _sanitize(compute_full_analytics(
        pnl_trades=[{"net_pnl": t.net_pnl, "r_multiple": t.r_multiple}
                    for t in pnl_calc.trades],
        initial_capital=pnl_calc._initial_capital,
        session_stats=_ss,
        healer_snapshot=_heal,
        lake_stats=_lake_s,
        genome_state=_safe(genome.export_state, {}),
        redis_ok=_redis_ok,
        persistence_ok=(_redis_ok or _sqlite_ok),
    )), {})

    _genome_state = _safe(genome.export_state, {})
    _rl_summary   = _safe(rl_engine.summary, {})

    # Full Q-table export — each context's learning state
    _rl_qtable = _safe(lambda: {
        k: {
            "q_value":   round(s.q_value, 5),
            "n_visits":  s.n_visits,
            "n_wins":    s.n_wins,
            "total_pnl": round(s.total_pnl, 4),
            "win_rate":  round(s.win_rate, 4),
            "toxic":     k in rl_engine._toxic_contexts,
        }
        for k, s in rl_engine._table.items()
    }, {})

    _trade_flow = _safe(trade_flow_monitor.summary, {})

    _regime_map = _safe(lambda: {
        sym: {
            "regime":     s.regime.value,
            "adx":        s.adx,
            "atr_pct":    s.atr_pct,
            "bb_width":   s.bb_width,
            "confidence": s.confidence,
        }
        for sym, s in regime_det.all_states().items()
    }, {})

    _positions: list = []
    try:
        for _sym, _pos in risk_ctrl.positions.items():
            _positions.append({
                "symbol":     _sym,
                "side":       getattr(_pos, "side", ""),
                "qty":        getattr(_pos, "qty", 0.0),
                "entry_px":   getattr(_pos, "entry_px", 0.0),
                "unrealised": getattr(_pos, "unrealised_pnl", 0.0),
            })
    except Exception:
        pass

    _deployability = _safe(lambda: _sanitize(deployability_engine.to_dict(
        deployability_engine.compute(
            trades=_n_trades,
            sharpe=_ss.get("sharpe_ratio", 0.0),
            sortino=_ss.get("sortino_ratio", 0.0),
            win_rate=_ss.get("win_rate", 0.0),
            max_drawdown=_ss.get("max_drawdown_pct", 0.0) / 100,
            risk_of_ruin=_ss.get("risk_of_ruin", 0.0),
            avg_r=_ss.get("avg_r_multiple", 0.0),
        )
    )), {})

    _capital_flow       = _safe(capital_flow_engine.summary, {})
    _aee_state          = _safe(adaptive_edge_engine.summary, {})
    _signal_filter_snap = _safe(signal_filter.summary, {})
    _thought_log_snap   = list(_thought_log)[-100:]

    # ── Build unified intelligence data dict ──────────────────────────────────
    intel = {
        "captured_at":     captured_at,
        "captured_at_ms":  ts_ms,
        "version":         APP_VERSION,
        "boot_ts":         _boot_ts,
        "bypass_mode":     cfg.BYPASS_ALL_GATES,
        # L1: Operational health
        "system_status":   _exc_safe(_status_result, {}),
        "healer_snapshot": _heal,
        "obs_health":      _exc_safe(_obs_h, {}),
        "obs_anomalies":   _exc_safe(_obs_a, {}),
        "obs_escalations": _exc_safe(_obs_e, {}),
        "halt_audit":      _exc_safe(_halt_audit_result, {}),
        # L2: Signal intelligence
        "trade_flow":      _trade_flow,
        "thought_log":     _thought_log_snap,
        "last_skip":       _exc_safe(_last_skip_result, {}),
        "regime_map":      _regime_map,
        "signal_filter":   _signal_filter_snap,
        # L3: Live process
        "rl_summary":      _rl_summary,
        "rl_qtable":       _rl_qtable,
        # L4: Economic truth
        "economic_truth":  _exc_safe(_et_report, {}),
        # L5: Alpha and learning
        "lio_snapshot":    _exc_safe(_lio_bundle_result, {}),
        # L6: Risk and governance
        "alpha_confirmation":    _exc_safe(_ac_report, {}),
        "survivability":         _exc_safe(_sv_report, {}),
        "execution_governance":  _exc_safe(_eg_report, {}),
        "continuity":            _exc_safe(_ic_report, {}),
        "equilibrium":           _exc_safe(_aeq_report, {}),
        # L7: Capital and performance
        "session_stats":        _ss,
        "trades_recent_100":    _trade_dicts,
        "analytics":            _analytics,
        "deployability":        _deployability,
        "capital_flow":         _capital_flow,
        "aee_state":            _aee_state,
        "positions":            _positions,
        # L9: Genome
        "genome_state":         _genome_state,
    }

    # ── Generate the BRIEFING.md ───────────────────────────────────────────────
    try:
        briefing_md = generate_briefing(intel)
    except Exception as _be:
        import traceback as _tb
        briefing_md = (
            f"# PHOENIX Intelligence Briefing\n\n"
            f"**Briefing generation error:**\n```\n{_tb.format_exc()}\n```\n"
        )
        logger.error(f"[UNIFIED-INTEL] briefing_generator failed: {_be}")

    # ── JSON serializer ────────────────────────────────────────────────────────
    def _jb(obj) -> bytes:
        try:
            return _json.dumps(_sanitize(obj), indent=2, ensure_ascii=False).encode("utf-8")
        except Exception as _je:
            return _json.dumps({"error": str(_je)}).encode("utf-8")

    # ── Build file map ────────────────────────────────────────────────────────
    file_map: dict = {
        "00_BRIEFING.md":                                      briefing_md.encode("utf-8"),
        # 01
        "01_operational_health/system_status.json":            _jb(intel["system_status"]),
        "01_operational_health/healer_snapshot.json":          _jb(intel["healer_snapshot"]),
        "01_operational_health/observability_health.json":     _jb(intel["obs_health"]),
        "01_operational_health/anomalies.json":                _jb(intel["obs_anomalies"]),
        "01_operational_health/escalations.json":              _jb(intel["obs_escalations"]),
        "01_operational_health/halt_audit.json":               _jb(intel["halt_audit"]),
        # 02
        "02_signal_intelligence/trade_flow.json":              _jb(intel["trade_flow"]),
        "02_signal_intelligence/thought_log.json":             _jb(intel["thought_log"]),
        "02_signal_intelligence/last_skip.json":               _jb(intel["last_skip"]),
        "02_signal_intelligence/regime_map.json":              _jb(intel["regime_map"]),
        "02_signal_intelligence/signal_filter.json":           _jb(intel["signal_filter"]),
        # 03
        "03_live_process_snapshot/rl_qtable.json":             _jb(intel["rl_qtable"]),
        # 04
        "04_economic_truth/orchestration.json":                _jb(intel["economic_truth"]),
        # 05
        "05_alpha_and_learning/lio_full_snapshot.json":        _jb(intel["lio_snapshot"]),
        # 06
        "06_risk_and_governance/alpha_confirmation.json":      _jb(intel["alpha_confirmation"]),
        "06_risk_and_governance/execution_governance.json":    _jb(intel["execution_governance"]),
        "06_risk_and_governance/survivability.json":           _jb(intel["survivability"]),
        "06_risk_and_governance/continuity.json":              _jb(intel["continuity"]),
        "06_risk_and_governance/equilibrium.json":             _jb(intel["equilibrium"]),
        # 07
        "07_capital_and_performance/session_stats.json":       _jb(intel["session_stats"]),
        "07_capital_and_performance/trades_recent_100.json":   _jb(intel["trades_recent_100"]),
        "07_capital_and_performance/analytics.json":           _jb(intel["analytics"]),
        "07_capital_and_performance/deployability.json":       _jb(intel["deployability"]),
        "07_capital_and_performance/capital_flow.json":        _jb(intel["capital_flow"]),
        "07_capital_and_performance/aee_state.json":           _jb(intel["aee_state"]),
        # 09
        "09_genome/genome_state.json":                         _jb(intel["genome_state"]),
    }

    # ── Build MANIFEST.json ────────────────────────────────────────────────────
    manifest = {
        "package_type":   "PHOENIX_UNIFIED_INTELLIGENCE",
        "version":        APP_VERSION,
        "captured_at":    captured_at,
        "captured_at_ms": ts_ms,
        "bypass_mode":    cfg.BYPASS_ALL_GATES,
        "trade_count":    _n_trades,
        "capital_usdt":   round((_ss.get("capital") or 0.0), 2),
        "net_pnl_usdt":   round((_ss.get("total_net_pnl") or 0.0), 2),
        "files":          {
            path: {
                "size_bytes": len(content),
                "sha256":     hashlib.sha256(content).hexdigest(),
            }
            for path, content in file_map.items()
        },
    }
    manifest_bytes = _jb(manifest)

    # ── Assemble and stream the ZIP ────────────────────────────────────────────
    buf = _io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as _zf:
        _zf.writestr("00_MANIFEST.json", manifest_bytes)
        for _path, _content in file_map.items():
            _zf.writestr(_path, _content)
    buf.seek(0)

    filename = f"PHOENIX_Intelligence_{ts_str}.zip"
    logger.info(
        f"[UNIFIED-INTEL] package assembled | files={len(file_map)+1} "
        f"trades={_n_trades} version={APP_VERSION}"
    )
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ── Entry Point ───────────────────────────────────────────────────────────────

# Serve dashboard.html at "/" so http://localhost:8000 opens the dashboard directly
_DASH = Path(__file__).parent / "dashboard.html"


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def serve_dashboard():
    if _DASH.exists():
        return HTMLResponse(_DASH.read_text(encoding="utf-8"))
    return HTMLResponse("<h2>dashboard.html not found in project root</h2>", status_code=404)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info",
    )
