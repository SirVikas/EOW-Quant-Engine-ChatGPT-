"""
FTD-030B — tests/test_learning_memory.py
Unit tests for the Learning Memory Layer modules.
"""
from __future__ import annotations

import time
import tempfile
import pathlib
import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_record(
    cycle_id="c001",
    regime="BULL",
    volatility_pct=0.15,
    parameter="stop_loss_pct",
    direction="DOWN",
    score_delta=2.5,
    rollback=False,
    meta_score=78.0,
    contradiction=False,
    ai_mode="AGGRESSIVE",
):
    from core.learning_memory.memory_store import MemoryRecord
    return MemoryRecord.build(
        cycle_id=cycle_id,
        regime=regime,
        volatility_pct=volatility_pct,
        parameter=parameter,
        direction=direction,
        score_delta=score_delta,
        rollback=rollback,
        meta_score=meta_score,
        contradiction=contradiction,
        ai_mode=ai_mode,
    )


# ── MemoryStore ───────────────────────────────────────────────────────────────

class TestMemoryStore:
    def test_add_and_count(self, tmp_path):
        from core.learning_memory.memory_store import MemoryStore
        store = MemoryStore(path=tmp_path / "ms.jsonl")
        rec = _make_record()
        assert store.add(rec) is True
        assert store.count() == 1

    def test_duplicate_rejected(self, tmp_path):
        from core.learning_memory.memory_store import MemoryStore
        store = MemoryStore(path=tmp_path / "ms.jsonl")
        rec = _make_record()
        store.add(rec)
        assert store.add(rec) is False  # same record_id

    def test_persists_and_loads(self, tmp_path):
        from core.learning_memory.memory_store import MemoryStore, MemoryRecord
        p = tmp_path / "ms.jsonl"
        s1 = MemoryStore(path=p)
        s1.add(_make_record("a1"))
        s1.add(_make_record("a2"))

        s2 = MemoryStore(path=p)
        assert s2.count() == 2

    def test_all_records_returns_list(self, tmp_path):
        from core.learning_memory.memory_store import MemoryStore
        store = MemoryStore(path=tmp_path / "ms.jsonl")
        store.add(_make_record("x1"))
        records = store.all_records()
        assert isinstance(records, list)
        assert len(records) == 1


# ── PatternEngine ─────────────────────────────────────────────────────────────

class TestPatternEngine:
    def test_update_creates_pattern(self):
        from core.learning_memory.pattern_engine import PatternEngine
        engine = PatternEngine()
        rec = _make_record()
        pat = engine.update(rec)
        assert pat is not None
        assert pat.samples == 1

    def test_pattern_id_format(self):
        from core.learning_memory.pattern_engine import PatternEngine
        engine = PatternEngine()
        rec = _make_record(regime="BULL", parameter="stop_loss_pct", direction="DOWN")
        pat = engine.update(rec)
        assert "BULL" in pat.pattern_id
        assert "stop_loss_pct" in pat.pattern_id

    def test_accumulate_samples(self):
        from core.learning_memory.pattern_engine import PatternEngine
        engine = PatternEngine()
        for i in range(5):
            engine.update(_make_record(cycle_id=f"c{i}"))
        pats = engine.all_patterns()
        assert len(pats) == 1
        assert pats[0].samples == 5

    def test_valid_pattern_requires_gates(self):
        from core.learning_memory.pattern_engine import PatternEngine
        engine = PatternEngine()
        for i in range(5):
            engine.update(_make_record(cycle_id=f"c{i}"))
        valid = engine.valid_patterns()
        # < 20 samples → not valid yet
        assert len(valid) == 0

    def test_top_by_confidence(self):
        from core.learning_memory.pattern_engine import PatternEngine
        engine = PatternEngine()
        engine.update(_make_record(regime="BULL"))
        engine.update(_make_record(regime="BEAR", cycle_id="b1"))
        top = engine.top_by_confidence(10)
        assert isinstance(top, list)


# ── ConfidenceUpdater ─────────────────────────────────────────────────────────

class TestConfidenceUpdater:
    def test_compute_confidence_range(self):
        from core.learning_memory.pattern_engine import PatternEngine
        from core.learning_memory.confidence_updater import compute_confidence
        engine = PatternEngine()
        for i in range(30):
            engine.update(_make_record(cycle_id=f"c{i}", regime=["BULL","BEAR","RANGE"][i % 3]))
        for pat in engine.all_patterns():
            conf = compute_confidence(pat)
            assert 0 <= conf <= 100

    def test_rollback_penalty_reduces_confidence(self):
        from core.learning_memory.confidence_updater import apply_rollback_penalty
        reduced = apply_rollback_penalty(80.0)
        assert reduced < 80.0
        assert abs(reduced - 80.0 * 0.70) < 0.01

    def test_time_decay_reduces_confidence(self):
        from core.learning_memory.confidence_updater import apply_time_decay
        aged = apply_time_decay(80.0, 10)
        assert aged < 80.0


# ── NegativeMemory ────────────────────────────────────────────────────────────

class TestNegativeMemory:
    def test_first_rollback_blacklists(self, tmp_path):
        from core.learning_memory.negative_memory import NegativeMemory
        neg = NegativeMemory(path=tmp_path / "neg.jsonl")
        neg.record_rollback("pat123")
        assert neg.is_blacklisted("pat123") is True

    def test_three_rollbacks_permanent(self, tmp_path):
        from core.learning_memory.negative_memory import NegativeMemory
        neg = NegativeMemory(path=tmp_path / "neg.jsonl")
        for _ in range(3):
            neg.record_rollback("pat123")
        assert neg.is_permanently_banned("pat123") is True

    def test_decay_rehabilitates(self, tmp_path):
        from core.learning_memory.negative_memory import NegativeMemory
        neg = NegativeMemory(path=tmp_path / "neg.jsonl")
        neg.record_rollback("pat_temp")
        # Apply many decay cycles to reach weight ≤ 0.1
        for _ in range(30):
            neg.decay_cycle()
        assert neg.is_blacklisted("pat_temp") is False

    def test_permanent_not_decayed(self, tmp_path):
        from core.learning_memory.negative_memory import NegativeMemory
        neg = NegativeMemory(path=tmp_path / "neg.jsonl")
        for _ in range(3):
            neg.record_rollback("pat_perm")
        for _ in range(30):
            neg.decay_cycle()
        assert neg.is_permanently_banned("pat_perm") is True


# ── ForgettingEngine ──────────────────────────────────────────────────────────

class TestForgettingEngine:
    def test_run_cycle_returns_summary(self):
        from core.learning_memory.forgetting_engine import ForgettingEngine
        from core.learning_memory.pattern_engine import PatternEngine
        engine  = PatternEngine()
        forgetter = ForgettingEngine()
        engine.update(_make_record())
        result = forgetter.run_cycle(engine)
        assert "decayed" in result
        assert "removed" in result

    def test_rollback_penalty_applied(self):
        from core.learning_memory.forgetting_engine import ForgettingEngine
        from core.learning_memory.pattern_engine import PatternEngine
        engine  = PatternEngine()
        forgetter = ForgettingEngine()
        pat = engine.update(_make_record())
        old_conf = pat.confidence
        old_c, new_c = forgetter.apply_rollback_penalty(engine, pat.pattern_id)
        assert new_c < old_conf

    def test_low_confidence_pattern_removed(self):
        from core.learning_memory.forgetting_engine import ForgettingEngine
        from core.learning_memory.pattern_engine import PatternEngine
        engine    = PatternEngine()
        forgetter = ForgettingEngine()
        pat = engine.update(_make_record())
        pat.confidence = 10.0  # manually set below threshold
        result = forgetter.run_cycle(engine)
        assert len(result["removed"]) > 0


# ── MemoryGuard ───────────────────────────────────────────────────────────────

class TestMemoryGuard:
    def test_allows_valid_change(self):
        from core.learning_memory.memory_guard import MemoryGuard
        guard = MemoryGuard()
        result = guard.check(
            parameter="stop_loss_pct",
            current_value=0.02,
            proposed_value=0.022,
        )
        assert result.allowed is True

    def test_blocks_hard_limit_param(self):
        from core.learning_memory.memory_guard import MemoryGuard
        guard = MemoryGuard()
        result = guard.check(
            parameter="MAX_DRAWDOWN_HALT",
            current_value=0.15,
            proposed_value=0.10,
        )
        assert result.allowed is False

    def test_blocks_excessive_shift(self):
        from core.learning_memory.memory_guard import MemoryGuard
        guard = MemoryGuard()
        result = guard.check(
            parameter="stop_loss_pct",
            current_value=0.02,
            proposed_value=0.10,  # >30% shift from 0.02
        )
        assert result.allowed is False

    def test_blocks_duplicate_inflight(self):
        from core.learning_memory.memory_guard import MemoryGuard
        guard = MemoryGuard()
        guard.register_inflight("stop_loss_pct")
        result = guard.check(
            parameter="stop_loss_pct",
            current_value=0.02,
            proposed_value=0.022,
        )
        assert result.allowed is False
        guard.clear_inflight("stop_loss_pct")


# ── ExplainabilityEngine ──────────────────────────────────────────────────────

class TestExplainabilityEngine:
    def test_build_returns_card(self):
        from core.learning_memory.explainability_engine import ExplainabilityEngine
        from core.learning_memory.pattern_engine import PatternEngine
        eng  = PatternEngine()
        pat  = eng.update(_make_record())
        expl = ExplainabilityEngine()
        card = expl.build(
            pattern=pat,
            memory_suggest=0.025,
            live_suggest=0.022,
            final_value=0.0235,
            applied_weight=0.5,
        )
        assert card.pattern_id == pat.pattern_id
        assert card.applied_weight == 0.5

    def test_history_capped(self):
        from core.learning_memory.explainability_engine import ExplainabilityEngine
        from core.learning_memory.pattern_engine import PatternEngine
        eng  = PatternEngine()
        pat  = eng.update(_make_record())
        expl = ExplainabilityEngine(history_size=3)
        for _ in range(10):
            expl.build(pat, 0.02, 0.021, 0.0205, 0.5)
        assert len(expl._history) == 3


# ── MemoryApplier ─────────────────────────────────────────────────────────────

class TestMemoryApplier:
    def _make_valid_pattern(self, conf=75.0):
        from core.learning_memory.pattern_engine import PatternEngine
        engine = PatternEngine()
        # Build a pattern with enough samples to be valid
        for i in range(25):
            regime = ["BULL", "BEAR", "RANGE"][i % 3]
            engine.update(_make_record(cycle_id=f"m{i}", regime=regime))
        pats = engine.all_patterns()
        p = pats[0]
        p.confidence = conf
        return p

    def test_apply_all_gates_pass(self, tmp_path):
        from core.learning_memory.memory_guard import MemoryGuard
        from core.learning_memory.explainability_engine import ExplainabilityEngine
        from core.learning_memory.negative_memory import NegativeMemory
        from core.learning_memory.memory_applier import MemoryApplier
        guard    = MemoryGuard()
        explainer = ExplainabilityEngine()
        neg      = NegativeMemory(path=tmp_path / "neg.jsonl")
        applier  = MemoryApplier(guard, explainer, neg)

        pat = self._make_valid_pattern(conf=75.0)
        result = applier.apply(
            pattern=pat,
            memory_suggest=0.025,
            live_suggest=0.022,
            current_value=0.02,
            meta_score=78.0,
            ftd027_passed=True,
        )
        assert result.applied is True
        assert result.memory_weight == 0.5
        assert result.explain_card is not None

    def test_rejected_ftd027_failed(self, tmp_path):
        from core.learning_memory.memory_guard import MemoryGuard
        from core.learning_memory.explainability_engine import ExplainabilityEngine
        from core.learning_memory.negative_memory import NegativeMemory
        from core.learning_memory.memory_applier import MemoryApplier
        guard    = MemoryGuard()
        explainer = ExplainabilityEngine()
        neg      = NegativeMemory(path=tmp_path / "neg.jsonl")
        applier  = MemoryApplier(guard, explainer, neg)

        pat = self._make_valid_pattern(conf=75.0)
        result = applier.apply(
            pattern=pat,
            memory_suggest=0.025,
            live_suggest=0.022,
            current_value=0.02,
            meta_score=78.0,
            ftd027_passed=False,
        )
        assert result.applied is False
        assert "FTD027" in result.reason

    def test_low_confidence_uses_low_weight(self, tmp_path):
        from core.learning_memory.memory_guard import MemoryGuard
        from core.learning_memory.explainability_engine import ExplainabilityEngine
        from core.learning_memory.negative_memory import NegativeMemory
        from core.learning_memory.memory_applier import MemoryApplier, MIN_PATTERN_CONFIDENCE
        guard    = MemoryGuard()
        explainer = ExplainabilityEngine()
        neg      = NegativeMemory(path=tmp_path / "neg.jsonl")
        applier  = MemoryApplier(guard, explainer, neg)

        pat = self._make_valid_pattern(conf=MIN_PATTERN_CONFIDENCE - 1)
        result = applier.apply(
            pattern=pat,
            memory_suggest=0.025,
            live_suggest=0.022,
            current_value=0.02,
            meta_score=78.0,
            ftd027_passed=True,
        )
        assert result.applied is False  # conf below gate


# ── LearningMemoryEngine (integration smoke test) ─────────────────────────────

class TestLearningMemoryEngineSmoke:
    def test_check_activation_inactive_below_trades(self, tmp_path, monkeypatch):
        from core.learning_memory import memory_store, pattern_engine, forgetting_engine
        from core.learning_memory import negative_memory, memory_guard, pattern_indexer
        from core.learning_memory import explainability_engine, memory_applier
        from core.learning_memory.learning_memory_engine import LearningMemoryEngine

        # Patch storage paths to tmp
        monkeypatch.setattr("core.learning_memory.memory_store.STORE_PATH",
                            tmp_path / "ms.jsonl")
        monkeypatch.setattr("core.learning_memory.negative_memory.NEGATIVE_PATH",
                            tmp_path / "neg.jsonl")
        monkeypatch.setattr("core.learning_memory.pattern_indexer.INDEX_PATH",
                            tmp_path / "idx.json")
        monkeypatch.setattr("core.learning_memory.learning_memory_engine.REPORT_PATH",
                            tmp_path / "report.md")

        lme = LearningMemoryEngine()
        active = lme.check_activation(n_trades=10, meta_score=80.0)
        assert active is False  # 10 < 50 min trades

    def test_update_skipped_when_inactive(self, tmp_path, monkeypatch):
        from core.learning_memory.learning_memory_engine import LearningMemoryEngine
        monkeypatch.setattr("core.learning_memory.memory_store.STORE_PATH",
                            tmp_path / "ms.jsonl")
        monkeypatch.setattr("core.learning_memory.negative_memory.NEGATIVE_PATH",
                            tmp_path / "neg.jsonl")
        monkeypatch.setattr("core.learning_memory.pattern_indexer.INDEX_PATH",
                            tmp_path / "idx.json")
        monkeypatch.setattr("core.learning_memory.learning_memory_engine.REPORT_PATH",
                            tmp_path / "report.md")

        lme = LearningMemoryEngine()
        result = lme.update(
            cycle_id="test001",
            applied_changes=[{"parameter": "stop_loss_pct", "before": 0.02, "after": 0.018}],
            rollbacks=[],
            meta_score=78.0,
            contradiction=False,
            ai_mode="CONSERVATIVE",
            regime="BULL",
            volatility_pct=0.12,
        )
        assert result["action"] == "SKIPPED"

    def test_summary_structure(self, tmp_path, monkeypatch):
        from core.learning_memory.learning_memory_engine import LearningMemoryEngine
        monkeypatch.setattr("core.learning_memory.memory_store.STORE_PATH",
                            tmp_path / "ms.jsonl")
        monkeypatch.setattr("core.learning_memory.negative_memory.NEGATIVE_PATH",
                            tmp_path / "neg.jsonl")
        monkeypatch.setattr("core.learning_memory.pattern_indexer.INDEX_PATH",
                            tmp_path / "idx.json")
        monkeypatch.setattr("core.learning_memory.learning_memory_engine.REPORT_PATH",
                            tmp_path / "report.md")

        lme = LearningMemoryEngine()
        s = lme.summary()
        assert "active" in s
        assert "patterns" in s
        assert "negative_memory" in s
        assert "forgetting" in s
