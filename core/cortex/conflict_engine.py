"""
PHOENIX CORTEX — Conflict Detection Engine  [CX-3]

Detects contradictory signals from modules that share the same decision
domain (entry, exit, position size, risk).  A conflict arises when two or
more active modules are producing signals that logically cannot both be
correct at the same time.

Conflict types
──────────────
  DIRECTION_CONFLICT     One module says BUY, another says SELL
  RISK_CONFLICT          Risk engine approves, but risk controller rejects (or vice versa)
  SIZE_CONFLICT          Capital allocator says increase size, risk engine says reduce
  GOVERNANCE_CONFLICT    Gate approves, safe mode wants to block
  REGIME_CONFLICT        Two regime detectors disagree on the current regime
  ECONOMIC_CONFLICT      Module A increases win rate but destroys profit factor
  STRATEGIC_CONFLICT     Trend-following signal conflicts with mean-reversion signal

Each ConflictEvent records:
  - The conflicting modules and their signals
  - Severity (LOW | MEDIUM | HIGH | CRITICAL)
  - Resolution recommendation (which module should take precedence per Constitutional Rule)
  - Whether trading should be blocked pending resolution

Constitutional Rules (immutable precedence):
  Rule-001: Risk Engine / Risk Controller cannot be overridden by signal modules
  Rule-002: Global Gate Controller has final authority over all trade execution
  Rule-003: Safe Mode Engine takes precedence over all Tier-B modules
  Rule-004: Drawdown Controller cannot be overridden by capital modules

Conflict scoring:
  Score = Σ(severity_weight × conflict_count)
  If score > CONFLICT_BLOCK_THRESHOLD → no trade
"""
from __future__ import annotations

import threading
import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple


# ── Constants ─────────────────────────────────────────────────────────────────

SEVERITY_LOW      = "LOW"
SEVERITY_MEDIUM   = "MEDIUM"
SEVERITY_HIGH     = "HIGH"
SEVERITY_CRITICAL = "CRITICAL"

_SEVERITY_WEIGHTS = {SEVERITY_LOW: 1, SEVERITY_MEDIUM: 3,
                     SEVERITY_HIGH: 8, SEVERITY_CRITICAL: 20}

CONFLICT_BLOCK_THRESHOLD = 15   # score above this → trading blocked

MAX_HISTORY = 200


# ── Constitutional Rules ──────────────────────────────────────────────────────

CONSTITUTIONAL_RULES: List[dict] = [
    {
        "rule_id": "RULE-001",
        "description": "Risk Engine and Risk Controller cannot be overridden by signal modules",
        "protected_modules": ["risk_engine", "risk_controller"],
        "overriding_tiers": ["A"],
        "resolution": "Defer to risk_engine / risk_controller",
    },
    {
        "rule_id": "RULE-002",
        "description": "Global Gate Controller has final execution authority",
        "protected_modules": ["global_gate_controller"],
        "overriding_tiers": ["A", "B"],
        "resolution": "Defer to global_gate_controller",
    },
    {
        "rule_id": "RULE-003",
        "description": "Safe Mode Engine takes precedence over all Tier-B modules",
        "protected_modules": ["safe_mode_engine"],
        "overriding_tiers": ["B"],
        "resolution": "Defer to safe_mode_engine",
    },
    {
        "rule_id": "RULE-004",
        "description": "Drawdown Controller cannot be overridden by capital allocation modules",
        "protected_modules": ["drawdown_controller"],
        "overriding_tiers": ["A", "B"],
        "resolution": "Defer to drawdown_controller",
    },
]


# ── Data Model ────────────────────────────────────────────────────────────────

@dataclass
class ModuleSignal:
    module_key: str
    signal_type: str     # direction | size | risk | regime | governance
    signal_value: Any    # "BUY"/"SELL", "INCREASE"/"DECREASE", "APPROVE"/"REJECT", etc.
    confidence: float    # 0–1
    timestamp: float = field(default_factory=time.time)
    metadata: Dict = field(default_factory=dict)


@dataclass
class ConflictEvent:
    conflict_id: str
    conflict_type: str
    severity: str
    module_a: str
    signal_a: Any
    module_b: str
    signal_b: Any
    description: str
    resolution: str
    block_trading: bool
    detected_at: float = field(default_factory=time.time)
    constitutional_rule: Optional[str] = None


# ── Engine ────────────────────────────────────────────────────────────────────

class ConflictDetectionEngine:
    """
    Receives module signals and detects contradictions.
    Maintains a rolling window of recent signals for real-time conflict analysis.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        # Rolling signal buffer: module_key → most recent ModuleSignal
        self._signals: Dict[str, ModuleSignal] = {}
        # Conflict history
        self._history: Deque[ConflictEvent] = deque(maxlen=MAX_HISTORY)
        self._conflict_score: float = 0.0
        self._last_scan_ts: float = 0.0

    # ── Signal Submission ─────────────────────────────────────────────────────

    def submit_signal(self, signal: ModuleSignal) -> None:
        """Any module can submit its current signal for conflict checking."""
        with self._lock:
            self._signals[signal.module_key] = signal

    def submit(
        self,
        module_key: str,
        signal_type: str,
        signal_value: Any,
        confidence: float = 1.0,
        metadata: Optional[Dict] = None,
    ) -> None:
        self.submit_signal(ModuleSignal(
            module_key=module_key,
            signal_type=signal_type,
            signal_value=signal_value,
            confidence=confidence,
            metadata=metadata or {},
        ))

    # ── Conflict Scan ─────────────────────────────────────────────────────────

    def scan(self) -> dict:
        """
        Scan all current signals for conflicts.
        Returns a ConflictReport with active conflicts and current score.
        """
        now = time.time()
        with self._lock:
            signals = dict(self._signals)

        conflicts: List[ConflictEvent] = []
        conflicts.extend(self._check_direction_conflicts(signals))
        conflicts.extend(self._check_risk_conflicts(signals))
        conflicts.extend(self._check_size_conflicts(signals))
        conflicts.extend(self._check_governance_conflicts(signals))
        conflicts.extend(self._check_economic_conflicts(signals))
        conflicts.extend(self._check_strategic_conflicts(signals))

        # Record new conflicts
        score = 0.0
        with self._lock:
            for c in conflicts:
                self._history.appendleft(c)
            score = sum(_SEVERITY_WEIGHTS[c.severity] for c in conflicts)
            self._conflict_score = score
            self._last_scan_ts = now

        block = score >= CONFLICT_BLOCK_THRESHOLD
        return {
            "scan_timestamp":   now,
            "active_conflicts": len(conflicts),
            "conflict_score":   score,
            "block_threshold":  CONFLICT_BLOCK_THRESHOLD,
            "trading_blocked":  block,
            "by_severity": {
                "CRITICAL": sum(1 for c in conflicts if c.severity == SEVERITY_CRITICAL),
                "HIGH":      sum(1 for c in conflicts if c.severity == SEVERITY_HIGH),
                "MEDIUM":    sum(1 for c in conflicts if c.severity == SEVERITY_MEDIUM),
                "LOW":       sum(1 for c in conflicts if c.severity == SEVERITY_LOW),
            },
            "conflicts": [self._serialise(c) for c in conflicts],
        }

    def current_score(self) -> float:
        with self._lock:
            return self._conflict_score

    def is_trading_blocked(self) -> bool:
        with self._lock:
            return self._conflict_score >= CONFLICT_BLOCK_THRESHOLD

    def history(self, limit: int = 50) -> List[dict]:
        with self._lock:
            return [self._serialise(c) for c in list(self._history)[:limit]]

    def constitutional_rules(self) -> List[dict]:
        return CONSTITUTIONAL_RULES

    # ── Conflict Checkers ─────────────────────────────────────────────────────

    def _check_direction_conflicts(
        self, signals: Dict[str, ModuleSignal]
    ) -> List[ConflictEvent]:
        """BUY vs SELL from different signal modules."""
        direction_signals = [
            s for s in signals.values()
            if s.signal_type == "direction"
            and s.signal_value in ("BUY", "SELL", "LONG", "SHORT")
        ]
        conflicts = []
        for i, s1 in enumerate(direction_signals):
            for s2 in direction_signals[i + 1:]:
                if self._opposite_directions(s1.signal_value, s2.signal_value):
                    # Higher severity if both are high-confidence
                    avg_conf = (s1.confidence + s2.confidence) / 2
                    sev = SEVERITY_HIGH if avg_conf > 0.7 else SEVERITY_MEDIUM
                    rule = self._apply_constitutional_rule(s1.module_key, s2.module_key)
                    conflicts.append(ConflictEvent(
                        conflict_id=f"DIR_{s1.module_key}_{s2.module_key}_{int(time.time())}",
                        conflict_type="DIRECTION_CONFLICT",
                        severity=sev,
                        module_a=s1.module_key, signal_a=s1.signal_value,
                        module_b=s2.module_key, signal_b=s2.signal_value,
                        description=(
                            f"{s1.module_key} signals {s1.signal_value} "
                            f"while {s2.module_key} signals {s2.signal_value}"
                        ),
                        resolution=rule["resolution"] if rule else
                                   "Hold trade pending manual resolution",
                        block_trading=sev == SEVERITY_HIGH,
                        constitutional_rule=rule["rule_id"] if rule else None,
                    ))
        return conflicts

    def _check_risk_conflicts(
        self, signals: Dict[str, ModuleSignal]
    ) -> List[ConflictEvent]:
        """Risk approval from one module contradicts rejection from another."""
        risk_signals = {
            k: s for k, s in signals.items()
            if s.signal_type == "risk"
            and s.signal_value in ("APPROVE", "REJECT", "BLOCK")
        }
        conflicts = []
        approvals  = [s for s in risk_signals.values() if s.signal_value == "APPROVE"]
        rejections = [s for s in risk_signals.values() if s.signal_value in ("REJECT", "BLOCK")]
        for a in approvals:
            for r in rejections:
                rule = self._apply_constitutional_rule(a.module_key, r.module_key)
                conflicts.append(ConflictEvent(
                    conflict_id=f"RISK_{a.module_key}_{r.module_key}_{int(time.time())}",
                    conflict_type="RISK_CONFLICT",
                    severity=SEVERITY_CRITICAL,
                    module_a=a.module_key, signal_a="APPROVE",
                    module_b=r.module_key, signal_b=r.signal_value,
                    description=(
                        f"{a.module_key} approves trade but "
                        f"{r.module_key} rejects/blocks it"
                    ),
                    resolution=rule["resolution"] if rule else
                               "Conservative: defer to the rejecting module (RULE-001)",
                    block_trading=True,
                    constitutional_rule=rule["rule_id"] if rule else "RULE-001",
                ))
        return conflicts

    def _check_size_conflicts(
        self, signals: Dict[str, ModuleSignal]
    ) -> List[ConflictEvent]:
        """Increase position size vs reduce exposure."""
        size_signals = [
            s for s in signals.values()
            if s.signal_type == "size"
            and s.signal_value in ("INCREASE", "DECREASE", "REDUCE")
        ]
        conflicts = []
        for i, s1 in enumerate(size_signals):
            for s2 in size_signals[i + 1:]:
                if (s1.signal_value == "INCREASE" and
                        s2.signal_value in ("DECREASE", "REDUCE")):
                    rule = self._apply_constitutional_rule(s1.module_key, s2.module_key)
                    conflicts.append(ConflictEvent(
                        conflict_id=f"SIZE_{s1.module_key}_{s2.module_key}_{int(time.time())}",
                        conflict_type="SIZE_CONFLICT",
                        severity=SEVERITY_HIGH,
                        module_a=s1.module_key, signal_a="INCREASE",
                        module_b=s2.module_key, signal_b=s2.signal_value,
                        description=(
                            f"{s1.module_key} wants to increase size "
                            f"while {s2.module_key} wants to reduce exposure"
                        ),
                        resolution=rule["resolution"] if rule else
                                   "Conservative: reduce exposure (RULE-001 / RULE-004)",
                        block_trading=False,
                        constitutional_rule=rule["rule_id"] if rule else "RULE-004",
                    ))
        return conflicts

    def _check_governance_conflicts(
        self, signals: Dict[str, ModuleSignal]
    ) -> List[ConflictEvent]:
        """Gate approves but safe mode wants to block."""
        gov_signals = {
            k: s for k, s in signals.items()
            if s.signal_type == "governance"
        }
        conflicts = []
        gate_sig   = gov_signals.get("global_gate_controller")
        safe_sig   = gov_signals.get("safe_mode_engine")
        if gate_sig and safe_sig:
            gate_ok = gate_sig.signal_value in ("OPEN", "APPROVE", "ALLOW")
            safe_block = safe_sig.signal_value in ("BLOCK", "SAFE_MODE", "HALT")
            if gate_ok and safe_block:
                conflicts.append(ConflictEvent(
                    conflict_id=f"GOV_GATE_SAFE_{int(time.time())}",
                    conflict_type="GOVERNANCE_CONFLICT",
                    severity=SEVERITY_CRITICAL,
                    module_a="global_gate_controller", signal_a=gate_sig.signal_value,
                    module_b="safe_mode_engine",        signal_b=safe_sig.signal_value,
                    description=(
                        "Global Gate Controller is open but Safe Mode Engine "
                        "is blocking — governance system inconsistency"
                    ),
                    resolution="Defer to Safe Mode Engine (RULE-002 + RULE-003)",
                    block_trading=True,
                    constitutional_rule="RULE-003",
                ))
        return conflicts

    def _check_economic_conflicts(
        self, signals: Dict[str, ModuleSignal]
    ) -> List[ConflictEvent]:
        """Module improves win rate but degrades profit factor — pyrrhic win."""
        econ_signals = [
            s for s in signals.values()
            if s.signal_type == "economic"
        ]
        conflicts = []
        for i, s1 in enumerate(econ_signals):
            for s2 in econ_signals[i + 1:]:
                wr1 = s1.metadata.get("win_rate_delta", 0)
                pf1 = s1.metadata.get("profit_factor_delta", 0)
                wr2 = s2.metadata.get("win_rate_delta", 0)
                pf2 = s2.metadata.get("profit_factor_delta", 0)
                # Conflict: one module improves WR while other degrades PF significantly
                if (wr1 > 0.05 and pf1 < -0.2) or (wr2 > 0.05 and pf2 < -0.2):
                    conflicts.append(ConflictEvent(
                        conflict_id=f"ECON_{s1.module_key}_{s2.module_key}_{int(time.time())}",
                        conflict_type="ECONOMIC_CONFLICT",
                        severity=SEVERITY_MEDIUM,
                        module_a=s1.module_key, signal_a=f"WR+{wr1:.1%} PF{pf1:+.2f}",
                        module_b=s2.module_key, signal_b=f"WR+{wr2:.1%} PF{pf2:+.2f}",
                        description=(
                            "Economic trade-off conflict: win rate improvement destroys "
                            "profit factor — net outcome may be negative expectancy."
                        ),
                        resolution="Evaluate net expectancy before applying parameter change",
                        block_trading=False,
                    ))
        # Also detect: single module reporting wr+ but pf-
        for s in econ_signals:
            wr = s.metadata.get("win_rate_delta", 0)
            pf = s.metadata.get("profit_factor_delta", 0)
            if wr > 0.05 and pf < -0.3:
                conflicts.append(ConflictEvent(
                    conflict_id=f"ECON_PYRRHIC_{s.module_key}_{int(time.time())}",
                    conflict_type="ECONOMIC_CONFLICT",
                    severity=SEVERITY_HIGH,
                    module_a=s.module_key, signal_a=f"WR+{wr:.1%}",
                    module_b=s.module_key, signal_b=f"PF{pf:+.2f}",
                    description=(
                        f"'{s.module_key}' reports win rate improvement of {wr:.1%} "
                        f"but profit factor degradation of {pf:.2f} — pyrrhic win."
                    ),
                    resolution="Block parameter change; net expectancy is negative",
                    block_trading=False,
                ))
        return conflicts

    def _check_strategic_conflicts(
        self, signals: Dict[str, ModuleSignal]
    ) -> List[ConflictEvent]:
        """Trend-following and mean-reversion modules signaling simultaneously."""
        strat_signals = {
            k: s for k, s in signals.items()
            if s.signal_type == "strategy"
        }
        trend_modules = [
            s for s in strat_signals.values()
            if s.signal_value in ("TREND_FOLLOW", "MOMENTUM", "BREAKOUT")
        ]
        reversion_modules = [
            s for s in strat_signals.values()
            if s.signal_value in ("MEAN_REVERT", "COUNTER_TREND", "RANGE_BOUND")
        ]
        conflicts = []
        for t in trend_modules:
            for r in reversion_modules:
                avg_conf = (t.confidence + r.confidence) / 2
                sev = SEVERITY_HIGH if avg_conf > 0.7 else SEVERITY_MEDIUM
                conflicts.append(ConflictEvent(
                    conflict_id=f"STRAT_{t.module_key}_{r.module_key}_{int(time.time())}",
                    conflict_type="STRATEGIC_CONFLICT",
                    severity=sev,
                    module_a=t.module_key, signal_a=t.signal_value,
                    module_b=r.module_key, signal_b=r.signal_value,
                    description=(
                        f"Strategic regime conflict: '{t.module_key}' ({t.signal_value}) "
                        f"conflicts with '{r.module_key}' ({r.signal_value}). "
                        "Regime is ambiguous — applying both degrades expectancy."
                    ),
                    resolution=(
                        "Use regime detector consensus to select one strategy. "
                        "If regime is ambiguous, reduce position size or wait."
                    ),
                    block_trading=sev == SEVERITY_HIGH,
                ))
        return conflicts

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _opposite_directions(a: str, b: str) -> bool:
        opposites = {("BUY", "SELL"), ("SELL", "BUY"),
                     ("LONG", "SHORT"), ("SHORT", "LONG")}
        return (a, b) in opposites or (b, a) in opposites

    @staticmethod
    def _apply_constitutional_rule(
        key_a: str, key_b: str
    ) -> Optional[dict]:
        """Return the applicable constitutional rule if one module is protected."""
        for rule in CONSTITUTIONAL_RULES:
            protected = rule["protected_modules"]
            if key_a in protected or key_b in protected:
                return rule
        return None

    @staticmethod
    def _serialise(c: ConflictEvent) -> dict:
        return {
            "conflict_id":         c.conflict_id,
            "conflict_type":       c.conflict_type,
            "severity":            c.severity,
            "module_a":            c.module_a,
            "signal_a":            c.signal_a,
            "module_b":            c.module_b,
            "signal_b":            c.signal_b,
            "description":         c.description,
            "resolution":          c.resolution,
            "block_trading":       c.block_trading,
            "constitutional_rule": c.constitutional_rule,
            "detected_at":         c.detected_at,
        }


# Singleton
conflict_engine = ConflictDetectionEngine()
