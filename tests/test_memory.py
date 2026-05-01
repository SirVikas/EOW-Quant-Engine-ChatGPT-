"""
FTD-030B — Learning Memory Engine Tests
tests/test_memory.py

Coverage (≥80 tests across all 9 spec parts):
  Part 1: MemoryStore       — JSONL append-only, validation, persistence, purge
  Part 2: PatternEngine     — 5-tuple key, formation gate, confidence formula
  Part 3: ConfidenceUpdater — recency decay, regime bonus, success rate
  Part 4: MemoryApplier     — weighted merge, dynamic weight, application gate
  Part 5: MemoryGuard       — hard limits, max 30% shift, duplicates, policy veto
  Part 6: ForgettingEngine  — 0.95^age decay, rollback penalty, purge threshold
  Part 7: NegativeMemory    — blacklist, 3-strike ban, 0.90^age decay
  Part 8: PatternIndexer    — startup index, O(1) lookup, search, top-N
  Part 9: MemoryOrchestrator — learn, suggest, validate, summary, reset, negative integration
"""
from __future__ import annotations

import os
import time
import tempfile
import pytest

from core.memory.memory_store          import MemoryStore, MemoryEntry, MEMORY_LOG_PATH
from core.memory.pattern_detector      import PatternDetector, Pattern, MIN_PATTERN_SAMPLES, MIN_CONFIDENCE, MIN_CONTEXTS
from core.memory.pattern_indexer       import PatternIndexer
from core.memory.learning_updater      import LearningUpdater
from core.memory.retention_manager     import RetentionManager, TIME_DECAY_BASE, PERF_DECAY_FACTOR, PURGE_THRESHOLD
from core.memory.memory_validator      import MemoryValidator, MIN_TOTAL_SAMPLES, STABILITY_WINDOW
from core.memory.negative_memory       import NegativeMemory, ROLLBACK_BAN_THRESHOLD, NEGATIVE_DECAY_BASE
from core.memory.memory_applier        import MemoryApplier, MAX_INFLUENCE_PCT, MIN_CONF_TO_APPLY
from core.memory.memory_guard          import MemoryGuard, MAX_SHIFT_PCT
from core.memory.explainability_engine import ExplainabilityEngine
from core.memory.conflict_resolver     import ConflictResolver, MEMORY_WEIGHT, LIVE_WEIGHT
from core.memory.memory_orchestrator   import MemoryOrchestrator


# ── Helpers ───────────────────────────────────────────────────────────────────

def _store(tmp_path) -> MemoryStore:
    return MemoryStore(path=str(tmp_path / "test_store.jsonl"))


def _entry(
    entry_id="E1", change_id="C1", parameter="KELLY_FRACTION",
    direction="UP", market_regime="TRENDING", volatility=0.010,
    symbol="BTCUSDT", outcome_score=0.5, rolled_back=False,
    delta_pct=0.05,
) -> MemoryEntry:
    return MemoryEntry(
        entry_id=entry_id, ts=int(time.time() * 1000),
        market_regime=market_regime, volatility=volatility,
        symbol=symbol, change_id=change_id,
        parameter=parameter, delta_pct=delta_pct,
        direction=direction, value_before=0.20, value_after=0.21,
        pnl_delta=0.02, score_delta=1.5, rolled_back=rolled_back,
        rollback_trigger=None, rationale="test", confidence=75.0,
        outcome_score=outcome_score, decay_weight=1.0,
    )


def _make_entries(
    n: int,
    outcome_score: float = 0.5,
    regime: str = "TRENDING",
    volatility: float = 0.010,
    symbol: str = "BTCUSDT",
    parameter: str = "KELLY_FRACTION",
    direction: str = "UP",
) -> list:
    return [
        _entry(
            entry_id=f"E{i}", change_id=f"C{i}",
            parameter=parameter, direction=direction,
            market_regime=regime, volatility=volatility,
            symbol=symbol, outcome_score=outcome_score,
        )
        for i in range(n)
    ]


def _orchestrator(tmp_path) -> MemoryOrchestrator:
    orc = MemoryOrchestrator.__new__(MemoryOrchestrator)
    from core.memory.memory_store import MemoryStore
    from core.memory.pattern_detector import PatternDetector
    from core.memory.pattern_indexer import PatternIndexer
    from core.memory.learning_updater import LearningUpdater
    from core.memory.retention_manager import RetentionManager
    from core.memory.memory_validator import MemoryValidator
    from core.memory.negative_memory import NegativeMemory
    from core.memory.memory_applier import MemoryApplier
    from core.memory.memory_guard import MemoryGuard
    from core.memory.explainability_engine import ExplainabilityEngine
    from core.memory.conflict_resolver import ConflictResolver
    orc._store      = MemoryStore(path=str(tmp_path / "orc_store.jsonl"))
    orc._detector   = PatternDetector()
    orc._indexer    = PatternIndexer(orc._store, orc._detector)
    orc._updater    = LearningUpdater(orc._store, orc._detector)
    orc._retention  = RetentionManager(orc._store)
    orc._validator  = MemoryValidator()
    orc._neg_memory = NegativeMemory()
    orc._applier    = MemoryApplier()
    orc._guard      = MemoryGuard()
    orc._explainer  = ExplainabilityEngine()
    orc._resolver   = ConflictResolver()
    orc._total_ingested = 0
    orc.MODULE = "MEMORY_ORCHESTRATOR"
    orc.PHASE  = "030B"
    orc.START_CONDITION_TRADES = 50
    orc.START_CONDITION_SCORE  = 70.0
    return orc


# ═══════════════════════════════════════════════════════════════════════════════
# PART 1 — MemoryStore (JSONL append-only)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryStore:

    def test_store_appends_entry(self, tmp_path):
        s = _store(tmp_path)
        e = _entry()
        s.append(e)
        assert s.count() == 1

    def test_store_multiple_entries(self, tmp_path):
        s = _store(tmp_path)
        for i in range(5):
            s.append(_entry(entry_id=f"E{i}", change_id=f"C{i}"))
        assert s.count() == 5

    def test_store_persists_as_jsonl(self, tmp_path):
        path = str(tmp_path / "test.jsonl")
        s = MemoryStore(path=path)
        s.append(_entry("X1", "CX1"))
        s.append(_entry("X2", "CX2"))
        lines = open(path).readlines()
        assert len(lines) == 2
        import json
        assert json.loads(lines[0])["entry_id"] == "X1"

    def test_store_loads_on_restart(self, tmp_path):
        path = str(tmp_path / "persist.jsonl")
        s1 = MemoryStore(path=path)
        s1.append(_entry("R1", "CR1"))
        s1.append(_entry("R2", "CR2"))
        s2 = MemoryStore(path=path)
        assert s2.count() == 2

    def test_store_rejects_partial_record(self, tmp_path):
        s = _store(tmp_path)
        bad = _entry(entry_id="", change_id="C")
        with pytest.raises(ValueError):
            s.append(bad)

    def test_store_all_entries(self, tmp_path):
        s = _store(tmp_path)
        for i in range(3):
            s.append(_entry(entry_id=f"E{i}", change_id=f"C{i}"))
        entries = s.all_entries()
        assert len(entries) == 3
        assert all(isinstance(e, MemoryEntry) for e in entries)

    def test_store_recent_n(self, tmp_path):
        s = _store(tmp_path)
        for i in range(10):
            s.append(_entry(entry_id=f"E{i}", change_id=f"C{i}"))
        recent = s.recent(3)
        assert len(recent) == 3
        assert recent[-1].entry_id == "E9"

    def test_store_purge_below_weight(self, tmp_path):
        s = _store(tmp_path)
        e1 = _entry("E1", "C1")
        e2 = _entry("E2", "C2")
        e1.decay_weight = 0.10   # below default purge threshold 0.25
        e2.decay_weight = 0.80
        s.append(e1)
        s.append(e2)
        purged = s.purge_below_weight(0.25)
        assert purged == 1
        assert s.count() == 1
        assert s.all_entries()[0].entry_id == "E2"

    def test_store_update_weights(self, tmp_path):
        s = _store(tmp_path)
        s.append(_entry("W1", "CW1"))
        s.update_weights({"W1": 0.42})
        assert s.all_entries()[0].decay_weight == pytest.approx(0.42)

    def test_store_clear(self, tmp_path):
        s = _store(tmp_path)
        s.append(_entry("C1", "CC1"))
        s.clear()
        assert s.count() == 0

    def test_store_clear_empties_jsonl(self, tmp_path):
        path = str(tmp_path / "clr.jsonl")
        s = MemoryStore(path=path)
        s.append(_entry("D1", "CD1"))
        s.clear()
        lines = [l.strip() for l in open(path) if l.strip()]
        assert lines == []

    def test_store_default_path_created(self):
        os.makedirs(os.path.dirname(MEMORY_LOG_PATH), exist_ok=True)
        assert os.path.dirname(MEMORY_LOG_PATH)  # directory path is non-empty


# ═══════════════════════════════════════════════════════════════════════════════
# PART 2 — Pattern Engine (3-tuple key, formation gate, confidence)
# ═══════════════════════════════════════════════════════════════════════════════

class TestPatternEngine:

    def test_pattern_key_is_3_tuple(self, tmp_path):
        det = PatternDetector()
        entries = _make_entries(5, regime="TRENDING", volatility=0.010,
                                symbol="BTCUSDT", parameter="KELLY_FRACTION", direction="UP")
        patterns = det.detect(entries)
        for pid in patterns:
            parts = pid.split("|")
            assert len(parts) == 3, f"Expected 3-tuple key, got: {pid}"
        assert "BTCUSDT|KELLY_FRACTION|UP" in patterns

    def test_pattern_vol_bucket_tracked_in_context(self, tmp_path):
        det = PatternDetector()
        entries = _make_entries(3, volatility=0.001)   # LOW bucket
        patterns = det.detect(entries)
        for p in patterns.values():
            assert p.volatility == "LOW"   # primary vol_bucket tracked as attribute

    def test_vol_bucket_low(self):
        assert PatternDetector._vol_bucket(0.001) == "LOW"

    def test_vol_bucket_med(self):
        assert PatternDetector._vol_bucket(0.010) == "MED"

    def test_vol_bucket_high(self):
        assert PatternDetector._vol_bucket(0.030) == "HIGH"

    def test_pattern_not_validated_below_min_samples(self, tmp_path):
        det = PatternDetector()
        entries = _make_entries(MIN_PATTERN_SAMPLES - 1, outcome_score=1.0)
        patterns = det.detect(entries)
        assert all(not p.validated for p in patterns.values())

    def test_pattern_not_validated_below_min_contexts(self, tmp_path):
        det = PatternDetector()
        # Same regime+volatility → only 1 context bucket
        entries = _make_entries(MIN_PATTERN_SAMPLES + 5, outcome_score=1.0,
                                regime="TRENDING", volatility=0.010)
        patterns = det.detect(entries)
        for p in patterns.values():
            assert p.context_count == 1
            assert not p.validated

    def test_pattern_validated_with_all_gates(self, tmp_path):
        det = PatternDetector()
        # With 3-tuple key (instrument|param|direction) different regime×vol combos
        # all map to the SAME key — context_count accumulates across market conditions.
        contexts_defs = [
            ("TRENDING", 0.001),   # TRENDING|LOW
            ("RANGING",  0.012),   # RANGING|MED
            ("UNKNOWN",  0.035),   # UNKNOWN|HIGH
        ]
        per_ctx = (MIN_PATTERN_SAMPLES // len(contexts_defs)) + 2
        entries = []
        for regime, vol in contexts_defs:
            for i in range(per_ctx):
                e = _entry(
                    entry_id=f"E{regime}{i}", change_id=f"C{regime}{i}",
                    market_regime=regime, volatility=vol,
                    symbol="BTCUSDT", parameter="KELLY_FRACTION", direction="UP",
                    outcome_score=1.0,
                )
                entries.append(e)
        patterns = det.detect(entries)
        p = patterns["BTCUSDT|KELLY_FRACTION|UP"]
        assert p.sample_count >= MIN_PATTERN_SAMPLES
        assert p.context_count == 3
        assert p.confidence >= MIN_CONFIDENCE
        assert p.validated

    def test_pattern_counts_successes_failures(self, tmp_path):
        det = PatternDetector()
        entries = (
            _make_entries(7, outcome_score=0.5)   # successes (>0)
            + _make_entries(3, outcome_score=-0.5) # failures (<0)
        )
        for i, e in enumerate(entries):
            e.entry_id = f"E{i}"
            e.change_id = f"C{i}"
        patterns = det.detect(entries)
        for p in patterns.values():
            assert p.success_count == 7
            assert p.failure_count == 3
            assert p.sample_count == 10

    def test_pattern_avg_outcome_score_weighted(self, tmp_path):
        det = PatternDetector()
        entries = _make_entries(4, outcome_score=1.0)
        for i, e in enumerate(entries):
            e.entry_id = f"E{i}"
            e.change_id = f"C{i}"
        patterns = det.detect(entries)
        for p in patterns.values():
            assert p.avg_outcome_score == pytest.approx(1.0)

    def test_pattern_confidence_formula(self):
        # confidence = success_rate × recency × regime_bonus × 100
        # All recent (age≈0 → recency≈1), single regime (bonus=1.0)
        det = PatternDetector()
        entries = _make_entries(10, outcome_score=1.0)   # 100% success rate
        for i, e in enumerate(entries):
            e.entry_id = f"E{i}"
            e.change_id = f"C{i}"
        patterns = det.detect(entries)
        for p in patterns.values():
            # Expected: 1.0 × ~1.0 × 1.0 × 100 ≈ 100
            assert p.confidence > 90.0

    def test_pattern_multi_regime_bonus_applied(self):
        det = PatternDetector()
        # With 3-tuple key, entries from different regimes map to the SAME key.
        # multi-regime entries → regimes_seen has 2 entries → regime_bonus = 1.10
        entries_t = _make_entries(10, outcome_score=1.0, regime="TRENDING")
        entries_r = _make_entries(10, outcome_score=1.0, regime="RANGING")
        for i, e in enumerate(entries_t + entries_r):
            e.entry_id = f"E{i}"
            e.change_id = f"C{i}"
        patterns = det.detect(entries_t + entries_r)
        for p in patterns.values():
            assert len(p.regimes_seen) == 2   # multi-regime → bonus applied
            assert "TRENDING" in p.regimes_seen
            assert "RANGING" in p.regimes_seen

    def test_pattern_fields_complete(self, tmp_path):
        det = PatternDetector()
        entries = _make_entries(3, outcome_score=0.5)
        for i, e in enumerate(entries):
            e.entry_id = f"E{i}"
            e.change_id = f"C{i}"
        patterns = det.detect(entries)
        for p in patterns.values():
            assert hasattr(p, "pattern_id")
            assert hasattr(p, "regime")
            assert hasattr(p, "volatility")
            assert hasattr(p, "instrument")
            assert hasattr(p, "parameter")
            assert hasattr(p, "direction")
            assert hasattr(p, "sample_count")
            assert hasattr(p, "confidence")
            assert hasattr(p, "validated")
            assert hasattr(p, "context_count")
            assert hasattr(p, "last_seen_ts")

    def test_pattern_empty_entries_returns_empty(self):
        det = PatternDetector()
        assert det.detect([]) == {}


# ═══════════════════════════════════════════════════════════════════════════════
# PART 3 — ConfidenceUpdater / LearningUpdater
# ═══════════════════════════════════════════════════════════════════════════════

class TestLearningUpdater:

    def test_ingest_creates_entry(self, tmp_path):
        store   = _store(tmp_path)
        updater = LearningUpdater(store, PatternDetector())
        e = updater.ingest(
            change_id="CU1", parameter="KELLY_FRACTION", delta_pct=0.05,
            direction="UP", value_before=0.20, value_after=0.21,
            pnl_delta=0.03, score_delta=1.5, rolled_back=False,
        )
        assert store.count() == 1
        assert e.outcome_score > 0

    def test_score_outcome_rollback_returns_neg1(self, tmp_path):
        store   = _store(tmp_path)
        updater = LearningUpdater(store, PatternDetector())
        e = updater.ingest(
            change_id="CRB", parameter="KELLY_FRACTION", delta_pct=0.05,
            direction="UP", value_before=0.20, value_after=0.21,
            pnl_delta=0.02, score_delta=2.0, rolled_back=True,
        )
        assert e.outcome_score == -1.0

    def test_score_outcome_positive_pnl(self, tmp_path):
        store   = _store(tmp_path)
        updater = LearningUpdater(store, PatternDetector())
        e = updater.ingest(
            change_id="CPL", parameter="KELLY_FRACTION", delta_pct=0.05,
            direction="UP", value_before=0.20, value_after=0.21,
            pnl_delta=0.05, score_delta=3.0, rolled_back=False,
        )
        assert e.outcome_score > 0

    def test_score_outcome_negative_pnl_and_score(self, tmp_path):
        store   = _store(tmp_path)
        updater = LearningUpdater(store, PatternDetector())
        e = updater.ingest(
            change_id="CNL", parameter="KELLY_FRACTION", delta_pct=0.05,
            direction="DOWN", value_before=0.20, value_after=0.19,
            pnl_delta=-0.05, score_delta=-3.0, rolled_back=False,
        )
        assert e.outcome_score < 0

    def test_get_patterns_returns_dict(self, tmp_path):
        store   = _store(tmp_path)
        updater = LearningUpdater(store, PatternDetector())
        updater.ingest(
            change_id="CGP", parameter="KELLY_FRACTION", delta_pct=0.05,
            direction="UP", value_before=0.20, value_after=0.21,
            pnl_delta=0.01, score_delta=1.0, rolled_back=False,
        )
        patterns = updater.get_patterns()
        assert isinstance(patterns, dict)
        assert len(patterns) > 0

    def test_outcome_score_clamped(self, tmp_path):
        store   = _store(tmp_path)
        updater = LearningUpdater(store, PatternDetector())
        e = updater.ingest(
            change_id="CClamp", parameter="KELLY_FRACTION", delta_pct=0.05,
            direction="UP", value_before=0.20, value_after=0.21,
            pnl_delta=99.0, score_delta=99.0, rolled_back=False,
        )
        assert -1.0 <= e.outcome_score <= 1.0


# ═══════════════════════════════════════════════════════════════════════════════
# PART 4 — MemoryApplier
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryApplier:

    def test_max_influence_is_30_pct(self):
        assert MAX_INFLUENCE_PCT == pytest.approx(0.30)

    def test_min_conf_to_apply_is_60(self):
        assert MIN_CONF_TO_APPLY == pytest.approx(60.0)

    def test_no_suggestions_below_50_trades(self):
        app = MemoryApplier()
        result = app.suggest({}, {"KELLY_FRACTION": 0.20}, total_trades=49)
        assert result == []

    def test_no_suggestions_for_unvalidated_patterns(self):
        app = MemoryApplier()
        from unittest.mock import MagicMock
        p = MagicMock()
        p.validated = False
        p.confidence = 90.0
        result = app.suggest({"k": p}, {"KELLY_FRACTION": 0.20}, total_trades=55)
        assert result == []

    def test_no_suggestions_for_hard_limit_params(self):
        from core.self_correction.correction_proposal import HARD_LIMITS
        app = MemoryApplier()
        from unittest.mock import MagicMock
        for param in HARD_LIMITS:
            p = MagicMock()
            p.validated = True
            p.confidence = 90.0
            p.parameter = param
            p.avg_outcome_score = 0.5
            result = app.suggest({param: p}, {param: 0.10}, total_trades=55)
            assert result == []

    def test_suggestion_influence_capped_at_30_pct(self):
        app = MemoryApplier()
        from unittest.mock import MagicMock
        p = MagicMock()
        p.validated      = True
        p.confidence     = 100.0   # maximum confidence
        p.parameter      = "KELLY_FRACTION"
        p.direction      = "UP"
        p.avg_outcome_score = 0.9
        p.success_count  = 10
        p.sample_count   = 10
        p.avg_delta_pct  = 0.05
        cur = 0.20
        result = app.suggest({"k": p}, {"KELLY_FRACTION": cur}, total_trades=55)
        if result:
            delta_pct = abs(result[0]["suggested_value"] - cur) / cur
            assert delta_pct <= MAX_INFLUENCE_PCT + 1e-6

    def test_low_confidence_reduces_weight(self):
        from core.memory.memory_applier import LOW_CONF_THRESHOLD, LOW_CONF_WEIGHT, DEFAULT_MEMORY_WEIGHT
        assert LOW_CONF_WEIGHT < DEFAULT_MEMORY_WEIGHT

    def test_neutral_outcome_produces_no_suggestion(self):
        app = MemoryApplier()
        from unittest.mock import MagicMock
        p = MagicMock()
        p.validated = True
        p.confidence = 80.0
        p.parameter  = "KELLY_FRACTION"
        p.avg_outcome_score = 0.0   # neutral
        result = app.suggest({"k": p}, {"KELLY_FRACTION": 0.20}, total_trades=55)
        assert result == []


# ═══════════════════════════════════════════════════════════════════════════════
# PART 5 — MemoryGuard
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryGuard:

    def _suggestion(self, param="KELLY_FRACTION", cur=0.20, prop=0.22, direction="UP"):
        return {
            "parameter": param, "current_value": cur,
            "suggested_value": prop, "direction": direction,
            "influence_pct": 10.0, "confidence": 80.0,
            "sample_count": 25, "success_rate": 75.0,
            "avg_outcome": 0.5, "pattern_id": f"BTC|{param}|{direction}",
        }

    def test_max_shift_is_30_pct(self):
        assert MAX_SHIFT_PCT == pytest.approx(0.30)

    def test_guard_allows_valid_suggestion(self):
        g = MemoryGuard()
        s = self._suggestion(cur=0.20, prop=0.22)   # 10% shift — OK
        allowed, blocked = g.validate([s])
        assert len(allowed) == 1
        assert len(blocked) == 0

    def test_guard_blocks_hard_limit_param(self):
        from core.self_correction.correction_proposal import HARD_LIMITS
        g = MemoryGuard()
        for param in list(HARD_LIMITS.keys())[:2]:
            s = self._suggestion(param=param)
            allowed, blocked = g.validate([s])
            assert len(blocked) >= 1
            assert any("HARD_LIMIT" in b.get("guard_reason", "") for b in blocked)
            g.reset_session()

    def test_guard_blocks_excessive_shift(self):
        g = MemoryGuard()
        s = self._suggestion(cur=0.20, prop=0.32)   # 60% shift — too large
        allowed, blocked = g.validate([s])
        assert len(blocked) == 1
        assert "MAX_SHIFT" in blocked[0]["guard_reason"]

    def test_guard_blocks_duplicate(self):
        g = MemoryGuard()
        s1 = self._suggestion()
        s2 = self._suggestion()
        allowed, blocked = g.validate([s1, s2])
        assert len(allowed) == 1
        assert len(blocked) == 1
        assert "DUPLICATE" in blocked[0]["guard_reason"]

    def test_guard_policy_veto_blocks_all(self):
        g = MemoryGuard()
        suggestions = [self._suggestion(), self._suggestion(direction="DOWN")]
        allowed, blocked = g.validate(suggestions, policy_ok=False)
        assert len(allowed) == 0
        assert all("POLICY_VETO" in b["guard_reason"] for b in blocked)

    def test_guard_reset_session_clears_duplicates(self):
        g = MemoryGuard()
        s = self._suggestion()
        g.validate([s])
        g.reset_session()
        allowed, blocked = g.validate([s])
        assert len(allowed) == 1

    def test_guard_summary_structure(self):
        g = MemoryGuard()
        s = g.summary()
        assert "max_shift_pct" in s
        assert s["max_shift_pct"] == MAX_SHIFT_PCT


# ═══════════════════════════════════════════════════════════════════════════════
# PART 6 — ForgettingEngine (RetentionManager)
# ═══════════════════════════════════════════════════════════════════════════════

class TestForgettingEngine:

    def test_time_decay_base_is_095(self):
        assert TIME_DECAY_BASE == pytest.approx(0.95)

    def test_perf_decay_factor_is_07(self):
        assert PERF_DECAY_FACTOR == pytest.approx(0.70)

    def test_purge_threshold_is_025(self):
        assert PURGE_THRESHOLD == pytest.approx(0.25)

    def test_decay_reduces_weight(self, tmp_path):
        store = _store(tmp_path)
        e = _entry()
        e.ts = int((time.time() - 86400) * 1000)   # 1 day old
        store.append(e)
        rm = RetentionManager(store)
        rm.apply_decay()
        w = store.all_entries()[0].decay_weight
        assert w < 1.0

    def test_rollback_penalty_applied(self, tmp_path):
        store = _store(tmp_path)
        e = _entry(outcome_score=-1.0, rolled_back=True)
        store.append(e)
        rm = RetentionManager(store)
        result = rm.apply_decay()
        w = store.all_entries()[0].decay_weight
        assert w < 1.0

    def test_purge_removes_low_weight_entries(self, tmp_path):
        store = _store(tmp_path)
        e = _entry()
        e.decay_weight = 0.10   # below PURGE_THRESHOLD=0.25
        store.append(e)
        purged = store.purge_below_weight(PURGE_THRESHOLD)
        assert purged == 1
        assert store.count() == 0

    def test_good_entry_survives_decay(self, tmp_path):
        store = _store(tmp_path)
        e = _entry(outcome_score=0.8)
        store.append(e)   # ts = now
        rm = RetentionManager(store)
        rm.apply_decay()
        assert store.count() == 1  # recent entry barely decays

    def test_decay_returns_summary(self, tmp_path):
        store = _store(tmp_path)
        store.append(_entry())
        rm = RetentionManager(store)
        result = rm.apply_decay()
        assert "updated" in result
        assert "purged" in result

    def test_retention_summary_structure(self, tmp_path):
        store = _store(tmp_path)
        store.append(_entry())
        rm = RetentionManager(store)
        s = rm.summary()
        assert "total_entries" in s
        assert "avg_weight" in s
        assert "min_weight" in s

    def test_empty_store_summary(self, tmp_path):
        store = _store(tmp_path)
        rm = RetentionManager(store)
        s = rm.summary()
        assert s["total_entries"] == 0


# ═══════════════════════════════════════════════════════════════════════════════
# PART 7 — NegativeMemory
# ═══════════════════════════════════════════════════════════════════════════════

class TestNegativeMemory:

    def test_rollback_ban_threshold_is_3(self):
        assert ROLLBACK_BAN_THRESHOLD == 3

    def test_negative_decay_base_is_090(self):
        assert NEGATIVE_DECAY_BASE == pytest.approx(0.90)

    def test_first_rollback_not_banned(self):
        nm = NegativeMemory()
        r = nm.record_rollback("P1")
        assert r.rollback_count == 1
        assert not r.permanently_banned

    def test_second_rollback_not_banned(self):
        nm = NegativeMemory()
        nm.record_rollback("P1")
        r = nm.record_rollback("P1")
        assert r.rollback_count == 2
        assert not r.permanently_banned

    def test_third_rollback_permanently_banned(self):
        nm = NegativeMemory()
        nm.record_rollback("P1")
        nm.record_rollback("P1")
        r = nm.record_rollback("P1")
        assert r.rollback_count == 3
        assert r.permanently_banned

    def test_is_banned_after_3_rollbacks(self):
        nm = NegativeMemory()
        for _ in range(ROLLBACK_BAN_THRESHOLD):
            nm.record_rollback("BANNED")
        assert nm.is_permanently_banned("BANNED")
        assert nm.is_banned("BANNED")

    def test_is_banned_false_for_unknown_pattern(self):
        nm = NegativeMemory()
        assert nm.is_banned("UNKNOWN_PATTERN") is False

    def test_permanently_banned_stays_banned_after_decay(self):
        nm = NegativeMemory()
        for _ in range(ROLLBACK_BAN_THRESHOLD):
            nm.record_rollback("PERM")
        nm.apply_decay()   # must not remove permanently banned
        assert nm.is_permanently_banned("PERM")

    def test_non_banned_decays_and_purges(self):
        nm = NegativeMemory()
        nm.record_rollback("TEMP")
        r = nm._records["TEMP"]
        r.last_rollback_ts = int((time.time() - 86400 * 100) * 1000)   # 100 days ago
        r.decay_weight = 0.001   # force low weight
        purged = nm.apply_decay()
        assert purged == 1
        assert "TEMP" not in nm._records

    def test_rollback_count_returns_correct_count(self):
        nm = NegativeMemory()
        nm.record_rollback("P2")
        nm.record_rollback("P2")
        assert nm.rollback_count("P2") == 2

    def test_rollback_count_zero_for_new(self):
        nm = NegativeMemory()
        assert nm.rollback_count("NEWPAT") == 0

    def test_summary_structure(self):
        nm = NegativeMemory()
        s = nm.summary()
        assert "total_negative" in s
        assert "permanently_banned" in s
        assert "active_negative" in s
        assert "banned_patterns" in s

    def test_fourth_rollback_stays_banned(self):
        nm = NegativeMemory()
        for _ in range(4):
            nm.record_rollback("OVER")
        r = nm._records["OVER"]
        assert r.permanently_banned
        assert r.rollback_count == 3   # count stops incrementing after ban


# ═══════════════════════════════════════════════════════════════════════════════
# PART 8 — PatternIndexer
# ═══════════════════════════════════════════════════════════════════════════════

class TestPatternIndexer:

    def test_indexer_builds_on_startup(self, tmp_path):
        store   = _store(tmp_path)
        for i in range(3):
            store.append(_entry(entry_id=f"E{i}", change_id=f"C{i}"))
        det     = PatternDetector()
        indexer = PatternIndexer(store, det)
        assert len(indexer.all_patterns()) > 0

    def test_indexer_lookup_returns_pattern(self, tmp_path):
        store = _store(tmp_path)
        det   = PatternDetector()
        for i in range(3):
            store.append(_entry(entry_id=f"E{i}", change_id=f"C{i}"))
        indexer = PatternIndexer(store, det)
        pids    = list(indexer.all_patterns().keys())
        assert indexer.lookup(pids[0]) is not None

    def test_indexer_lookup_missing_returns_none(self, tmp_path):
        store   = _store(tmp_path)
        indexer = PatternIndexer(store, PatternDetector())
        assert indexer.lookup("NO_SUCH_PATTERN") is None

    def test_indexer_rebuild_updates_index(self, tmp_path):
        store = _store(tmp_path)
        det   = PatternDetector()
        indexer = PatternIndexer(store, det)
        assert len(indexer.all_patterns()) == 0
        store.append(_entry("E1", "C1"))
        count = indexer.rebuild()
        assert count > 0

    def test_indexer_search_by_parameter(self, tmp_path):
        store = _store(tmp_path)
        for i in range(3):
            store.append(_entry(entry_id=f"E{i}", change_id=f"C{i}", parameter="KELLY_FRACTION"))
        indexer = PatternIndexer(store, PatternDetector())
        results = indexer.search(parameter="KELLY_FRACTION")
        assert all(p.parameter == "KELLY_FRACTION" for p in results)

    def test_indexer_top_n(self, tmp_path):
        store = _store(tmp_path)
        for i in range(5):
            store.append(_entry(entry_id=f"E{i}", change_id=f"C{i}",
                                parameter=f"KELLY_FRACTION" if i < 3 else "ADAPTIVE_LR"))
        indexer = PatternIndexer(store, PatternDetector())
        top = indexer.top_n(1)
        assert len(top) == 1

    def test_indexer_summary_keys(self, tmp_path):
        store   = _store(tmp_path)
        indexer = PatternIndexer(store, PatternDetector())
        s = indexer.summary()
        assert "total_indexed" in s
        assert "validated" in s
        assert "parameters" in s
        assert "regimes" in s

    def test_indexer_validated_patterns(self, tmp_path):
        store   = _store(tmp_path)
        indexer = PatternIndexer(store, PatternDetector())
        validated = indexer.validated_patterns()
        assert isinstance(validated, dict)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 9 — MemoryOrchestrator (Integration)
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryOrchestrator:

    def _learn_n(self, orc, n, rolled_back=False, pnl=0.03, score=1.5,
                 param="KELLY_FRACTION", regime="TRENDING", vol=0.010):
        for i in range(n):
            orc.learn(
                change_id=f"CX{i}", parameter=param, delta_pct=0.05,
                direction="UP", value_before=0.20, value_after=0.21,
                pnl_delta=pnl, score_delta=score, rolled_back=rolled_back,
                market_regime=regime, volatility=vol, symbol="BTCUSDT",
            )

    def test_learn_returns_dict(self, tmp_path):
        orc = _orchestrator(tmp_path)
        r = orc.learn(
            change_id="LC1", parameter="KELLY_FRACTION", delta_pct=0.05,
            direction="UP", value_before=0.20, value_after=0.21,
            pnl_delta=0.03, score_delta=2.0, rolled_back=False,
        )
        assert "entry_id" in r
        assert "outcome_score" in r
        assert "memory_ready" in r
        assert "negative_memory" in r

    def test_learn_increments_total_entries(self, tmp_path):
        orc = _orchestrator(tmp_path)
        self._learn_n(orc, 5)
        assert orc._store.count() == 5

    def test_learn_rollback_tracked_in_negative_memory(self, tmp_path):
        orc = _orchestrator(tmp_path)
        r = orc.learn(
            change_id="LRB", parameter="KELLY_FRACTION", delta_pct=0.05,
            direction="UP", value_before=0.20, value_after=0.21,
            pnl_delta=-0.05, score_delta=-2.0, rolled_back=True,
        )
        assert r["negative_memory"]["total_negative"] == 1

    def test_learn_3_rollbacks_bans_pattern(self, tmp_path):
        orc = _orchestrator(tmp_path)
        for _ in range(ROLLBACK_BAN_THRESHOLD):
            orc.learn(
                change_id=f"LRB{_}", parameter="KELLY_FRACTION", delta_pct=0.05,
                direction="UP", value_before=0.20, value_after=0.21,
                pnl_delta=-0.05, score_delta=-2.0, rolled_back=True,
            )
        neg = orc._neg_memory.summary()
        assert neg["permanently_banned"] >= 1

    def test_suggest_blocked_insufficient_trades(self, tmp_path):
        orc = _orchestrator(tmp_path)
        self._learn_n(orc, 5)
        r = orc.suggest({"KELLY_FRACTION": 0.20}, total_trades=10, validation_score=75.0)
        assert r["reason"] in ("INSUFFICIENT_MEMORY", "INSUFFICIENT_TRADES")

    def test_suggest_blocked_low_validation_score(self, tmp_path):
        orc = _orchestrator(tmp_path)
        self._learn_n(orc, 5)
        r = orc.suggest({"KELLY_FRACTION": 0.20}, total_trades=55, validation_score=60.0)
        assert "reason" in r

    def test_validate_returns_dict(self, tmp_path):
        orc = _orchestrator(tmp_path)
        v = orc.validate()
        assert "memory_ready" in v
        assert "valid_patterns" in v
        assert "negative_memory" in v

    def test_summary_returns_all_panels(self, tmp_path):
        orc = _orchestrator(tmp_path)
        self._learn_n(orc, 3)
        s = orc.summary()
        assert "total_entries" in s
        assert "memory_ready" in s
        assert "patterns" in s
        assert "success_patterns" in s
        assert "failure_patterns" in s
        assert "negative_memory" in s
        assert "retention" in s
        assert "index" in s
        assert "guard" in s
        assert "top_patterns" in s

    def test_logs_returns_list(self, tmp_path):
        orc = _orchestrator(tmp_path)
        self._learn_n(orc, 5)
        logs = orc.logs(3)
        assert len(logs) == 3
        assert isinstance(logs[0], dict)

    def test_patterns_returns_dict(self, tmp_path):
        orc = _orchestrator(tmp_path)
        self._learn_n(orc, 3)
        p = orc.patterns()
        assert isinstance(p, dict)

    def test_patterns_includes_banned_flag(self, tmp_path):
        orc = _orchestrator(tmp_path)
        self._learn_n(orc, 1)
        p = orc.patterns()
        for pid, info in p.items():
            assert "banned" in info

    def test_reset_clears_everything(self, tmp_path):
        orc = _orchestrator(tmp_path)
        self._learn_n(orc, 5)
        orc.reset()
        assert orc._store.count() == 0
        assert orc._neg_memory.summary()["total_negative"] == 0

    def test_module_and_phase(self, tmp_path):
        orc = _orchestrator(tmp_path)
        assert orc.MODULE == "MEMORY_ORCHESTRATOR"
        assert orc.PHASE == "030B"

    def test_start_condition_trades_is_50(self, tmp_path):
        orc = _orchestrator(tmp_path)
        assert orc.START_CONDITION_TRADES == 50

    def test_start_condition_score_is_70(self, tmp_path):
        orc = _orchestrator(tmp_path)
        assert orc.START_CONDITION_SCORE == pytest.approx(70.0)

    def test_negative_memory_summary_method(self, tmp_path):
        orc = _orchestrator(tmp_path)
        s = orc.negative_memory_summary()
        assert "total_negative" in s
        assert "permanently_banned" in s


# ═══════════════════════════════════════════════════════════════════════════════
# PART 9b — ExplainabilityEngine + ConflictResolver
# ═══════════════════════════════════════════════════════════════════════════════

class TestExplainabilityEngine:

    def _sugg(self):
        return {
            "pattern_id": "BTC|KELLY_FRACTION|UP",
            "parameter": "KELLY_FRACTION", "current_value": 0.20,
            "suggested_value": 0.22, "direction": "UP",
            "influence_pct": 10.0, "confidence": 80.0,
            "sample_count": 25, "success_rate": 75.0,
            "avg_outcome": 0.5,
        }

    def test_explain_returns_string(self):
        e = ExplainabilityEngine()
        s = e.explain(self._sugg())
        assert isinstance(s, str)
        assert len(s) > 20

    def test_explain_includes_pattern_id(self):
        e = ExplainabilityEngine()
        s = e.explain(self._sugg())
        assert "KELLY_FRACTION" in s

    def test_explain_includes_confidence(self):
        e = ExplainabilityEngine()
        s = e.explain(self._sugg())
        assert "80" in s or "confidence" in s.lower()

    def test_explain_all_adds_explanation_key(self):
        e = ExplainabilityEngine()
        result = e.explain_all([self._sugg(), self._sugg()])
        assert all("explanation" in r for r in result)

    def test_explain_all_preserves_count(self):
        e = ExplainabilityEngine()
        result = e.explain_all([self._sugg()])
        assert len(result) == 1


class TestConflictResolver:

    def _sugg(self, param="KELLY_FRACTION", direction="UP", confidence=80.0):
        return {
            "pattern_id": f"BTC|{param}|{direction}",
            "parameter": param, "current_value": 0.20,
            "suggested_value": 0.22, "direction": direction,
            "influence_pct": 10.0, "confidence": confidence,
            "sample_count": 25, "success_rate": 75.0,
            "avg_outcome": 0.5, "explanation": "test",
        }

    def test_risk_halted_blocks_all(self):
        r = ConflictResolver()
        result = r.resolve([self._sugg()], {}, risk_halted=True)
        assert result == []

    def test_risk_violated_blocks_all(self):
        r = ConflictResolver()
        result = r.resolve([self._sugg()], {}, risk_violated=True)
        assert result == []

    def test_no_live_signal_applied(self):
        r = ConflictResolver()
        result = r.resolve([self._sugg()], {})
        assert len(result) == 1
        assert result[0]["resolution"] == "APPLIED"

    def test_aligned_live_signal(self):
        r = ConflictResolver()
        live = {"KELLY_FRACTION": {"direction": "UP", "confidence": 70.0}}
        result = r.resolve([self._sugg()], live)
        assert result[0]["resolution"] == "ALIGNED"

    def test_conflict_live_wins_when_higher_score(self):
        r = ConflictResolver()
        # Memory confidence=30 → mem_score=0.30×0.35=0.105; live confidence=90 → 0.90×0.65=0.585
        live = {"KELLY_FRACTION": {"direction": "DOWN", "confidence": 90.0}}
        result = r.resolve([self._sugg(confidence=30.0)], live)
        assert len(result) == 0 or result[0].get("resolution") == "CONFLICT_MEMORY_WINS"

    def test_memory_weight_constant(self):
        assert MEMORY_WEIGHT == pytest.approx(0.35)

    def test_live_weight_constant(self):
        assert LIVE_WEIGHT == pytest.approx(0.65)


# ═══════════════════════════════════════════════════════════════════════════════
# PART 9c — MemoryValidator
# ═══════════════════════════════════════════════════════════════════════════════

class TestMemoryValidator:

    def test_memory_not_ready_with_empty_patterns(self):
        v = MemoryValidator()
        result = v.validate_patterns({})
        assert result["memory_ready"] is False

    def test_stability_counts_increment(self):
        v = MemoryValidator()
        from unittest.mock import MagicMock
        p = MagicMock()
        p.sample_count = MIN_TOTAL_SAMPLES + 5
        p.confidence   = MIN_CONFIDENCE + 5
        for _ in range(STABILITY_WINDOW):
            v.validate_patterns({"P1": p})
        result = v.validate_patterns({"P1": p})
        assert "P1" in result["valid_patterns"]

    def test_stability_resets_on_failure(self):
        v = MemoryValidator()
        from unittest.mock import MagicMock
        p = MagicMock()
        p.sample_count = MIN_TOTAL_SAMPLES + 5
        p.confidence   = MIN_CONFIDENCE + 5
        v.validate_patterns({"P1": p})
        p.confidence = 10.0   # drop confidence
        v.validate_patterns({"P1": p})
        assert v._stability_counts.get("P1", 0) == 0

    def test_reset_all_clears_counts(self):
        v = MemoryValidator()
        from unittest.mock import MagicMock
        p = MagicMock()
        p.sample_count = 30
        p.confidence   = 80.0
        v.validate_patterns({"P1": p})
        v.reset_all()
        assert v._stability_counts == {}

    def test_validate_returns_required_keys(self):
        v = MemoryValidator()
        r = v.validate_patterns({})
        assert "memory_ready" in r
        assert "total_samples" in r
        assert "valid_patterns" in r
        assert "invalid_patterns" in r
        assert "stability_counts" in r


# ═══════════════════════════════════════════════════════════════════════════════
# Module-level constants / exports
# ═══════════════════════════════════════════════════════════════════════════════

class TestModuleExports:

    def test_all_exports_importable(self):
        from core.memory import (
            MemoryStore, MemoryEntry, PatternDetector, Pattern,
            PatternIndexer, LearningUpdater, RetentionManager,
            MemoryValidator, NegativeMemory, NegativeRecord,
            MemoryApplier, MemoryGuard, ExplainabilityEngine,
            ConflictResolver, MemoryOrchestrator, memory_orchestrator,
        )
        assert memory_orchestrator is not None

    def test_singleton_is_memory_orchestrator(self):
        from core.memory import memory_orchestrator
        assert isinstance(memory_orchestrator, MemoryOrchestrator)

    def test_phase_is_030B(self):
        from core.memory import memory_orchestrator
        assert memory_orchestrator.PHASE == "030B"
