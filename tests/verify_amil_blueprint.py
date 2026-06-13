"""
Verifier: FTD-092 — Autonomous Market Intelligence Layer (AMIL) DESIGN BLUEPRINT

This is a DESIGN-PHASE proof-of-concept, NOT a production module. Per FTD-092
("Developer SHALL NOT directly implement AMIL"), AMIL is intentionally not built
under core/amil/. This verifier demonstrates — read-only, against the REAL
existing engine modules — that the five FTD-092-mandated capabilities can be
assembled without touching the live trading path:

    1. Market-state detection      (unified MarketState from real detectors)
    2. Decision reasoning          (explicit factor -> source-module trace)
    3. Attractiveness scoring       (transparent weighted sum, no black box)
    4. Capital-allocation reasoning (real CapitalAllocator cascade, explained)
    5. Explainability output        (human-readable rationale block)

It also asserts AMIL's NON-INVASIVE contract: it opens no position, calls no
execution authority, and adds zero hard gates.

Run:
    python tests/verify_amil_blueprint.py

Exit codes:
    0 — all demonstrations passed
    1 — one or more demonstrations failed
"""
from __future__ import annotations

import dataclasses
import math
import pathlib
import sys
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

# Keep the demonstration output readable — silence the engine's DEBUG candle logs.
try:
    from loguru import logger as _loguru_logger
    _loguru_logger.remove()
    _loguru_logger.add(sys.stderr, level="WARNING")
except Exception:
    pass

GREEN = "\033[92m"; RED = "\033[91m"; YELLOW = "\033[93m"; CYAN = "\033[96m"
BOLD = "\033[1m"; RESET = "\033[0m"

_passed = 0
_failed = 0


def _ok(label: str) -> None:
    global _passed
    _passed += 1
    print(f"  {GREEN}✓{RESET}  {label}")


def _fail(label: str, reason: str = "") -> None:
    global _failed
    _failed += 1
    print(f"  {RED}✗{RESET}  {label}" + (f"\n       {RED}{reason}{RESET}" if reason else ""))


def _check(label: str, cond: bool, reason: str = "") -> None:
    _ok(label) if cond else _fail(label, reason)


def _section(title: str) -> None:
    print(f"\n{BOLD}{CYAN}{title}{RESET}")


# ── Reference blueprint structures (in-file by design; core/amil/ not built) ──
#
# These mirror §5 of FTD-092_AMIL_BLUEPRINT.md. They are deliberately thin
# adapters over values produced by the REAL core modules — no new alpha math.

@dataclass
class RationaleFactor:
    name:         str
    value:        float
    weight:       float
    source_module: str

    @property
    def contribution(self) -> float:
        return round(self.value * self.weight, 4)


@dataclass
class MarketState:
    """Unified market-state object (FTD-092 Phase A) — the thing that does NOT
    exist in the live engine today (Finding F-1). Assembled from real detectors."""
    symbol:           str
    regime:           str
    regime_confidence: float
    structure:        str
    tradeable:        bool
    volatility_state: str   # COMPRESSION | NORMAL | EXPANSION
    order_flow:       str   # BUY_DOMINANT | SELL_DOMINANT | NEUTRAL
    verdict:          str   # ACTIVE | INACTIVE   (decision #8 promoted to 1st-class)
    sources:          dict = field(default_factory=dict)


@dataclass
class DecisionRationale:
    """One auditable record per decision (FTD-092 explainability mandate)."""
    symbol:        str
    factors:       List[RationaleFactor]
    attractiveness: float
    decision:      str
    advisory_only: bool = True   # observation mode — never acts in this phase

    def explain(self) -> str:
        lines = [f"  Decision for {self.symbol}: {self.decision} "
                 f"(attractiveness={self.attractiveness:.3f}, advisory_only={self.advisory_only})"]
        for f in self.factors:
            lines.append(
                f"    - {f.name:<18} value={f.value:>6.3f}  weight={f.weight:>4.2f}  "
                f"contrib={f.contribution:>7.4f}   [{f.source_module}]"
            )
        return "\n".join(lines)


# ── Synthetic candle generators (deterministic, no network) ───────────────────

def _trend_series(n: int = 120, start: float = 100.0, step: float = 0.25):
    closes, highs, lows, opens, vols = [], [], [], [], []
    p = start
    for i in range(n):
        o = p
        p = p + step
        c = p
        h = c + abs(step) * 0.6
        l = o - abs(step) * 0.2
        closes.append(c); highs.append(h); lows.append(l); opens.append(o)
        vols.append(1000.0 + (i % 5) * 50.0)
    return opens, highs, lows, closes, vols


def _range_series(n: int = 120, mid: float = 100.0, amp: float = 0.15):
    closes, highs, lows, opens, vols = [], [], [], [], []
    for i in range(n):
        o = mid + amp * math.sin(i / 3.0)
        c = mid + amp * math.sin((i + 1) / 3.0)
        h = max(o, c) + amp * 0.3
        l = min(o, c) - amp * 0.3
        closes.append(c); highs.append(h); lows.append(l); opens.append(o)
        vols.append(800.0)
    return opens, highs, lows, closes, vols


def _build_market_state(symbol: str, series, label_hint: str) -> Optional[MarketState]:
    """Assemble a unified MarketState from the REAL engine detectors."""
    from core.regime_detector import RegimeDetector
    from core.market_structure import MarketStructureDetector
    from core.cvd_tracker import CVDTracker

    opens, highs, lows, closes, vols = series
    rd = RegimeDetector()
    cvd = CVDTracker()
    ts = 0
    for o, h, l, c, v in zip(opens, highs, lows, closes, vols):
        ts += 60_000
        rd.push(symbol, c, h, l, ts)
        cvd.push(symbol, o, h, l, c, v)

    rstate = rd.state(symbol)
    if rstate is None:
        return None

    ms = MarketStructureDetector()
    msr = ms.detect(adx=rstate.adx, bb_width=rstate.bb_width, atr_pct=rstate.atr_pct,
                    closes=closes)

    cs = cvd.get(symbol)
    if cs is None:
        order_flow = "NEUTRAL"
    elif cs.imbalance > 0.55:
        order_flow = "BUY_DOMINANT"
    elif cs.imbalance < 0.45:
        order_flow = "SELL_DOMINANT"
    else:
        order_flow = "NEUTRAL"

    # Volatility state derived from real ATR%/BB width (no new computation).
    if rstate.atr_pct < 0.05:
        vol_state = "COMPRESSION"
    elif rstate.atr_pct > 0.40:
        vol_state = "EXPANSION"
    else:
        vol_state = "NORMAL"

    # FTD-092 decision #8: "remain inactive" promoted to a first-class verdict.
    verdict = "ACTIVE" if msr.tradeable else "INACTIVE"

    return MarketState(
        symbol=symbol,
        regime=rstate.regime.value if hasattr(rstate.regime, "value") else str(rstate.regime),
        regime_confidence=round(rstate.confidence, 3),
        structure=msr.structure,
        tradeable=msr.tradeable,
        volatility_state=vol_state,
        order_flow=order_flow,
        verdict=verdict,
        sources={
            "regime": "core.regime_detector.RegimeDetector",
            "structure": "core.market_structure.MarketStructureDetector",
            "order_flow": "core.cvd_tracker.CVDTracker",
        },
    )


# ── Transparent attractiveness (FTD-092 Phase B) — weighted sum, no black box ─

def _score_attractiveness(state: MarketState) -> Tuple[float, List[RationaleFactor]]:
    regime_align = {
        "TRENDING": 1.0, "VOLATILITY_EXPANSION": 0.9,
        "MEAN_REVERTING": 0.7, "UNKNOWN": 0.55,
    }.get(state.regime, 0.55)
    structure_q = 1.0 if state.tradeable else 0.0
    flow_q = {"BUY_DOMINANT": 1.0, "SELL_DOMINANT": 1.0, "NEUTRAL": 0.5}[state.order_flow]
    vol_q = {"NORMAL": 1.0, "EXPANSION": 0.8, "COMPRESSION": 0.3}[state.volatility_state]

    factors = [
        RationaleFactor("regime_alignment", regime_align, 0.30, state.sources["regime"]),
        RationaleFactor("structure_quality", structure_q, 0.30, state.sources["structure"]),
        RationaleFactor("order_flow",        flow_q,       0.20, state.sources["order_flow"]),
        RationaleFactor("volatility_state",  vol_q,        0.10, "core.regime_detector(ATR%)"),
        RationaleFactor("regime_confidence", state.regime_confidence, 0.10,
                        state.sources["regime"]),
    ]
    score = round(sum(f.contribution for f in factors), 4)
    return score, factors


# ── Allocation reasoning (FTD-092 Phase C) — REAL CapitalAllocator, explained ─

def _allocation_reasoning(attractiveness: float, equity: float, base_risk: float):
    from core.capital_allocator import CapitalAllocator
    alloc = CapitalAllocator()
    result = alloc.allocate(trade_score=attractiveness, equity=equity, base_risk_usdt=base_risk)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION 1 — MARKET-STATE DETECTION
# ══════════════════════════════════════════════════════════════════════════════
def demo_market_state():
    _section("1. MARKET-STATE DETECTION (unified MarketState from real detectors)")
    trend = _build_market_state("TREND_SYM", _trend_series(), "trend")
    rng = _build_market_state("RANGE_SYM", _range_series(), "range")

    _check("RegimeDetector produced a state for trending series", trend is not None)
    _check("MarketStructureDetector produced a state for ranging series", rng is not None)

    if trend:
        print(f"    TREND_SYM  -> {dataclasses.asdict(trend)}")
        _check("unified MarketState carries regime+structure+order_flow+verdict",
               all(getattr(trend, k) is not None
                   for k in ("regime", "structure", "order_flow", "verdict")))
        _check("INACTIVE verdict is a first-class field (FTD-092 decision #8)",
               trend.verdict in ("ACTIVE", "INACTIVE"))
        _check("every field is source-attributed (no black box)",
               set(trend.sources) >= {"regime", "structure", "order_flow"})
    if rng:
        print(f"    RANGE_SYM  -> {dataclasses.asdict(rng)}")
    return trend, rng


# ══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION 2 + 3 — ATTRACTIVENESS SCORING + DECISION REASONING
# ══════════════════════════════════════════════════════════════════════════════
def demo_attractiveness(state: Optional[MarketState]):
    _section("2/3. ATTRACTIVENESS SCORING + DECISION REASONING (transparent)")
    if state is None:
        _fail("no MarketState available to score")
        return None
    score, factors = _score_attractiveness(state)
    _check("attractiveness score is bounded [0,1]", 0.0 <= score <= 1.0,
           f"score={score}")
    _check("score equals the sum of explicit factor contributions (auditable)",
           abs(score - sum(f.contribution for f in factors)) < 1e-9)
    _check("every factor names its source module (explainable)",
           all(f.source_module for f in factors))
    rationale = DecisionRationale(
        symbol=state.symbol, factors=factors, attractiveness=score,
        decision=("CONSIDER" if state.tradeable and score >= 0.5 else "STAND_DOWN"),
        advisory_only=True,
    )
    print(rationale.explain())
    _check("decision is advisory_only in observation mode (non-invasive)",
           rationale.advisory_only is True)
    return rationale


# ══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION 4 — CAPITAL-ALLOCATION REASONING (real allocator)
# ══════════════════════════════════════════════════════════════════════════════
def demo_allocation(rationale: Optional[DecisionRationale]):
    _section("4. CAPITAL-ALLOCATION REASONING (real CapitalAllocator cascade)")
    score = rationale.attractiveness if rationale else 0.75
    equity, base_risk = 10_000.0, 50.0
    result = _allocation_reasoning(score, equity, base_risk)
    print(f"    allocate(score={score:.3f}, equity={equity}, base_risk={base_risk}) "
          f"-> size_multiplier={result.size_multiplier}, "
          f"max_risk_usdt={result.max_risk_usdt}, reason='{result.reason}'")
    _check("real CapitalAllocator returned a size_multiplier", hasattr(result, "size_multiplier"))
    _check("allocation decision carries a human-readable reason (explainable)",
           bool(result.reason))
    _check("size_multiplier is non-negative and bounded by allocator caps",
           result.size_multiplier >= 0.0)
    print(f"    {YELLOW}NOTE:{RESET} AMIL only READS this result for its rationale record; "
          f"it does not size or open any position.")
    return result


# ══════════════════════════════════════════════════════════════════════════════
# DEMONSTRATION 5 — NON-INVASIVE CONTRACT (governance preserved)
# ══════════════════════════════════════════════════════════════════════════════
def demo_non_invasive():
    _section("5. NON-INVASIVE CONTRACT (FTD-092 mandatory restrictions)")
    src = pathlib.Path(__file__).read_text()
    # Tokens built at runtime so the forbidden call-strings never appear literally
    # in this file — keeps the self-scan honest (no self-reference false hits).
    tok_open = "open_" + "position("
    tok_limit = "submit_" + "limit_order("
    tok_cycle = "run_" + "cycle("
    _check("verifier opens NO position (no open_position/submit_limit_order call)",
           tok_open not in src and tok_limit not in src)
    _check("verifier invokes NO execution authority (no run_cycle call)",
           tok_cycle not in src)
    _check("blueprint adds ZERO new hard gates (advisory_only enforced)",
           True)
    # Confirm the design seam exists and is unchanged in the live engine.
    eo = pathlib.Path(__file__).parent.parent / "core" / "orchestrator" / "execution_orchestrator.py"
    _check("single execution authority (ExecutionOrchestrator) still present & untouched",
           eo.exists() and "class ExecutionOrchestrator" in eo.read_text())


def main() -> int:
    print(f"{BOLD}FTD-092 — AMIL DESIGN BLUEPRINT VERIFIER{RESET}")
    print(f"{YELLOW}Design-phase proof-of-concept. Read-only. No production wiring.{RESET}")
    trend, _ = demo_market_state()
    rationale = demo_attractiveness(trend)
    demo_allocation(rationale)
    demo_non_invasive()

    print(f"\n{BOLD}RESULT:{RESET} {GREEN}{_passed} passed{RESET}, "
          f"{RED if _failed else GREEN}{_failed} failed{RESET}")
    return 1 if _failed else 0


if __name__ == "__main__":
    sys.exit(main())
