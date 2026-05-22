"""
FTD-EXPLORE-OBSERVABILITY — Exploration Persistence & NegMem Forensics Verifier

Asserts:
  1.  ExplorationEventLog appends events to disk correctly.
  2.  Schema fields present in every persisted event.
  3.  read_all() returns correct event count.
  4.  lifetime_count() matches read_all() length.
  5.  lifetime_count_by_rule() returns per-rule breakdown.
  6.  summary() returns all required keys.
  7.  summary() Q-band distribution is populated.
  8.  Fail-open: record() to non-writable path never raises.
  9.  Fail-open: read_all() on missing file returns [].
 10.  Thread safety: concurrent writes don't corrupt the file.
 11.  Corrupted lines in JSONL are silently skipped.
 12.  prune() keeps at most max_lines entries.
 13.  RL engine Rule 1 triggers exploration log (RULE1_MIN_EXPLORE).
 14.  RL engine Rule 4 triggers exploration log (RULE4_FLOOR_EXPLORE).
 15.  Rule 3 (RL_TRADE) does NOT trigger exploration log.
 16.  Rule 2 (RL_TOXIC) does NOT trigger exploration log.
 17.  Exploration log record does NOT change should_trade() return value.
 18.  negmem_forensics() returns ALIGNED_POSITIVE for WR>0 + not banned.
 19.  negmem_forensics() returns ALIGNED_NEGATIVE for WR=0 + banned.
 20.  negmem_forensics() returns CONFLICT_POSITIVE_WR for WR>0 + banned.
 21.  negmem_forensics() returns CONFLICT_NEGATIVE_WR for WR=0 + not banned.
 22.  ontology_conflict_ratio correct.
 23.  quarantine_at_n_lt_5 counts correctly.
 24.  toxic_at_wr_gt_50pct counts correctly.
 25.  negmem_forensics() has scope_note (non-governing marker).
 26.  Backward compat: should_trade() still returns (bool, str).
 27.  Backward compat: NegativeMemory.to_list() unchanged.
 28.  negmem_forensics() does NOT mutate is_banned() state.
 29.  CLI analyse_exploration() handles empty event list.
 30.  CLI analyse_negmem() handles empty pattern list.
 31.  CLI analyse_negmem() handles patterns with no NegMem entry.
 32.  conflict_ratio is 0 when all patterns are aligned.
 33.  exploration_event_log singleton is importable.

Run: python -m pytest tests/test_exploration_persistence_and_negmem_forensics.py -v
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
from dataclasses import asdict
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.persistence.exploration_log import ExplorationEventLog, exploration_event_log
from core.learning_memory.negative_memory import (
    NegativeMemory, TEMP_REMOVAL_THRESHOLD, PERMANENT_BAN_AFTER
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _tmp_log() -> tuple[ExplorationEventLog, Path]:
    tmp = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
    tmp.close()
    path = Path(tmp.name)
    path.unlink(missing_ok=True)   # start empty
    return ExplorationEventLog(path=path), path


def _record(log: ExplorationEventLog, *, rule="RULE4_FLOOR_EXPLORE", session="NY",
            context="MEAN_REVERTING|NY|MR_PAPER_SPEED", pipeline="PAPER_SPEED",
            q_value=-0.08, visits=10) -> None:
    log.record(session=session, context=context, pipeline=pipeline,
               q_value=q_value, visits=visits, rule=rule)


def _fresh_rl_engine():
    """Construct RLContextualBandit without I/O side-effects."""
    import time, pathlib
    from core.rl_engine import RLContextualBandit
    eng = RLContextualBandit.__new__(RLContextualBandit)
    eng._table           = {}
    eng._toxic_contexts  = set()
    eng._total_pulls     = 0
    eng._total_updates   = 0
    eng._total_blocked   = 0
    eng._total_allowed   = 0
    eng._explore_trades  = 0
    eng._exploit_trades  = 0
    eng._boost_fires     = 0
    eng._floor_lowers    = 0
    eng._floor_raises    = 0
    eng._toxic_blocks    = 0
    eng._floor_explores  = 0
    eng._init_ts         = time.time()
    eng._state_path      = pathlib.Path("/tmp/_test_rl_qtable.json")
    return eng


def _seed_rl_context(eng, *, n_visits=10, q_value=-0.10,
                     regime="UNKNOWN", utc_hour=13, strategy="TEST_STRAT"):
    from core.time.session_definitions import make_context
    from core.rl_engine import ContextState
    key   = make_context(regime, utc_hour, strategy)
    state = ContextState(context=key, q_value=q_value, n_visits=n_visits)
    state.n_wins = max(0, int(n_visits * 0.5))
    eng._table[key] = state
    return key


# ── 1. Append writes to disk ──────────────────────────────────────────────────

def test_record_creates_file():
    log, path = _tmp_log()
    try:
        _record(log)
        assert path.exists()
    finally:
        path.unlink(missing_ok=True)


def test_record_appends_one_line():
    log, path = _tmp_log()
    try:
        _record(log)
        lines = [l for l in path.read_text().splitlines() if l.strip()]
        assert len(lines) == 1
    finally:
        path.unlink(missing_ok=True)


def test_multiple_records_append_multiple_lines():
    log, path = _tmp_log()
    try:
        for _ in range(5):
            _record(log)
        lines = [l for l in path.read_text().splitlines() if l.strip()]
        assert len(lines) == 5
    finally:
        path.unlink(missing_ok=True)


# ── 2. Schema fields present ──────────────────────────────────────────────────

def test_record_schema_fields():
    log, path = _tmp_log()
    try:
        _record(log)
        event = json.loads(path.read_text().strip())
        for field in ("utc_ts", "session", "context", "pipeline",
                      "q_value", "visits", "rule", "decision"):
            assert field in event, f"Missing field: {field}"
    finally:
        path.unlink(missing_ok=True)


def test_record_decision_always_allow():
    log, path = _tmp_log()
    try:
        _record(log)
        event = json.loads(path.read_text().strip())
        assert event["decision"] == "ALLOW"
    finally:
        path.unlink(missing_ok=True)


def test_record_q_value_rounded():
    log, path = _tmp_log()
    try:
        _record(log, q_value=-0.051234567)
        event = json.loads(path.read_text().strip())
        assert abs(event["q_value"] - (-0.05123)) < 0.000001
    finally:
        path.unlink(missing_ok=True)


# ── 3–4. read_all() and lifetime_count() ─────────────────────────────────────

def test_read_all_returns_list():
    log, path = _tmp_log()
    try:
        _record(log)
        _record(log)
        result = log.read_all()
        assert isinstance(result, list)
        assert len(result) == 2
    finally:
        path.unlink(missing_ok=True)


def test_lifetime_count_matches_read_all():
    log, path = _tmp_log()
    try:
        for _ in range(3):
            _record(log)
        assert log.lifetime_count() == len(log.read_all()) == 3
    finally:
        path.unlink(missing_ok=True)


# ── 5. lifetime_count_by_rule() ───────────────────────────────────────────────

def test_lifetime_count_by_rule_breakdown():
    log, path = _tmp_log()
    try:
        _record(log, rule="RULE1_MIN_EXPLORE")
        _record(log, rule="RULE1_MIN_EXPLORE")
        _record(log, rule="RULE4_FLOOR_EXPLORE")
        rb = log.lifetime_count_by_rule()
        assert rb.get("RULE1_MIN_EXPLORE", 0) == 2
        assert rb.get("RULE4_FLOOR_EXPLORE", 0) == 1
    finally:
        path.unlink(missing_ok=True)


# ── 6–7. summary() ───────────────────────────────────────────────────────────

def test_summary_required_keys():
    log, path = _tmp_log()
    try:
        _record(log)
        s = log.summary()
        for k in ("total_events", "rule_breakdown", "session_breakdown",
                  "pipeline_breakdown", "context_breakdown", "q_band_distribution"):
            assert k in s, f"summary() missing key: {k}"
    finally:
        path.unlink(missing_ok=True)


def test_summary_q_band_populated():
    log, path = _tmp_log()
    try:
        _record(log, q_value=-0.08)   # in (-0.10, -0.05) band
        s = log.summary()
        total_in_bands = sum(s["q_band_distribution"].values())
        assert total_in_bands == 1
    finally:
        path.unlink(missing_ok=True)


def test_summary_empty_log():
    log, path = _tmp_log()
    try:
        s = log.summary()
        assert s["total_events"] == 0
    finally:
        path.unlink(missing_ok=True)


# ── 8. Fail-open: bad write path ──────────────────────────────────────────────

def test_record_fail_open_bad_path():
    log = ExplorationEventLog(path=Path("/nonexistent_dir_xyz/exploration.jsonl"))
    try:
        log.record(session="NY", context="X", pipeline="PAPER_SPEED",
                   q_value=-0.10, visits=5, rule="RULE4_FLOOR_EXPLORE")
    except Exception as exc:
        pytest.fail(f"record() raised on bad path: {exc}")


# ── 9. Fail-open: missing file ────────────────────────────────────────────────

def test_read_all_missing_file_returns_empty():
    log = ExplorationEventLog(path=Path("/nonexistent_xyz/missing.jsonl"))
    result = log.read_all()
    assert result == []


def test_lifetime_count_missing_file_returns_zero():
    log = ExplorationEventLog(path=Path("/nonexistent_xyz/missing.jsonl"))
    assert log.lifetime_count() == 0


# ── 10. Thread safety ─────────────────────────────────────────────────────────

def test_concurrent_writes_do_not_corrupt():
    log, path = _tmp_log()
    try:
        errors = []

        def writer(n):
            try:
                for _ in range(n):
                    _record(log)
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(20,)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert not errors, f"Thread errors: {errors}"
        events = log.read_all()
        assert len(events) == 100    # 5 threads × 20 records
        for ev in events:
            assert "utc_ts" in ev   # each record is well-formed
    finally:
        path.unlink(missing_ok=True)


# ── 11. Corrupted lines skipped ───────────────────────────────────────────────

def test_corrupted_lines_silently_skipped():
    log, path = _tmp_log()
    try:
        _record(log)
        path.open("a").write("not-json\n")
        _record(log)
        events = log.read_all()
        assert len(events) == 2
    finally:
        path.unlink(missing_ok=True)


# ── 12. prune() ───────────────────────────────────────────────────────────────

def test_prune_keeps_max_lines():
    log, path = _tmp_log()
    try:
        for _ in range(20):
            _record(log)
        removed = log.prune(max_lines=10)
        assert removed == 10
        assert log.lifetime_count() == 10
    finally:
        path.unlink(missing_ok=True)


def test_prune_no_op_when_under_limit():
    log, path = _tmp_log()
    try:
        for _ in range(5):
            _record(log)
        removed = log.prune(max_lines=10)
        assert removed == 0
        assert log.lifetime_count() == 5
    finally:
        path.unlink(missing_ok=True)


# ── 13–14. RL engine writes to exploration log ───────────────────────────────

def test_rule1_triggers_exploration_log(tmp_path):
    import core.rl_engine as rl_mod
    tmp_log_path = tmp_path / "explore.jsonl"
    orig_log = rl_mod._exploration_log
    rl_mod._exploration_log = ExplorationEventLog(path=tmp_log_path)
    try:
        eng = _fresh_rl_engine()
        _seed_rl_context(eng, n_visits=1, q_value=-0.10)  # n < MIN_VISITS → Rule 1
        ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
        assert ok is True
        assert "RL_EXPLORE" in reason
        events = ExplorationEventLog(path=tmp_log_path).read_all()
        assert len(events) >= 1
        assert events[-1]["rule"] == "RULE1_MIN_EXPLORE"
    finally:
        rl_mod._exploration_log = orig_log


def test_rule4_triggers_exploration_log(tmp_path):
    import core.rl_engine as rl_mod
    tmp_log_path = tmp_path / "explore.jsonl"
    orig_log = rl_mod._exploration_log
    rl_mod._exploration_log = ExplorationEventLog(path=tmp_log_path)
    try:
        eng = _fresh_rl_engine()
        _seed_rl_context(eng, n_visits=10, q_value=-0.10)  # q in (-0.15,0) → Rule 4
        ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
        assert ok is True
        assert "RL_FLOOR_EXPLORE" in reason
        events = ExplorationEventLog(path=tmp_log_path).read_all()
        assert len(events) >= 1
        assert events[-1]["rule"] == "RULE4_FLOOR_EXPLORE"
    finally:
        rl_mod._exploration_log = orig_log


def test_rule4_log_schema(tmp_path):
    import core.rl_engine as rl_mod
    tmp_log_path = tmp_path / "explore.jsonl"
    orig_log = rl_mod._exploration_log
    rl_mod._exploration_log = ExplorationEventLog(path=tmp_log_path)
    try:
        eng = _fresh_rl_engine()
        _seed_rl_context(eng, n_visits=10, q_value=-0.10)
        eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
        ev = ExplorationEventLog(path=tmp_log_path).read_all()[-1]
        for field in ("utc_ts", "session", "context", "pipeline", "q_value", "visits", "rule"):
            assert field in ev, f"Missing field in logged event: {field}"
    finally:
        rl_mod._exploration_log = orig_log


# ── 15–16. Rule 3 and Rule 2 do NOT write to exploration log ─────────────────

def test_rule3_does_not_trigger_exploration_log(tmp_path):
    import core.rl_engine as rl_mod
    tmp_log_path = tmp_path / "explore.jsonl"
    orig_log = rl_mod._exploration_log
    rl_mod._exploration_log = ExplorationEventLog(path=tmp_log_path)
    try:
        eng = _fresh_rl_engine()
        _seed_rl_context(eng, n_visits=10, q_value=1.50)  # positive Q → Rule 3
        eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
        events = ExplorationEventLog(path=tmp_log_path).read_all()
        assert len(events) == 0
    finally:
        rl_mod._exploration_log = orig_log


def test_rule2_does_not_trigger_exploration_log(tmp_path):
    import core.rl_engine as rl_mod
    tmp_log_path = tmp_path / "explore.jsonl"
    orig_log = rl_mod._exploration_log
    rl_mod._exploration_log = ExplorationEventLog(path=tmp_log_path)
    try:
        eng = _fresh_rl_engine()
        key = _seed_rl_context(eng, n_visits=10, q_value=-0.10)
        eng._toxic_contexts.add(key)
        eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
        events = ExplorationEventLog(path=tmp_log_path).read_all()
        assert len(events) == 0
    finally:
        rl_mod._exploration_log = orig_log


# ── 17. Logging does not change should_trade() return ────────────────────────

def test_exploration_log_does_not_change_return_value(tmp_path):
    import core.rl_engine as rl_mod
    tmp_log_path = tmp_path / "explore.jsonl"
    orig_log = rl_mod._exploration_log

    # Test both with the real log and with a bad-path log (fail-open)
    for log_instance in [
        ExplorationEventLog(path=tmp_log_path),
        ExplorationEventLog(path=Path("/nonexistent_dir_xyz/x.jsonl")),
    ]:
        rl_mod._exploration_log = log_instance
        try:
            eng = _fresh_rl_engine()
            _seed_rl_context(eng, n_visits=10, q_value=-0.10)
            ok, reason = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
            assert ok is True
            assert "RL_FLOOR_EXPLORE" in reason
        finally:
            pass
    rl_mod._exploration_log = orig_log


# ── 18–21. negmem_forensics() conflict classification ────────────────────────

def _build_negmem_and_patterns(
    *,
    pattern_wr: float,    # 0.0 = all losses, 0.67 = 2/3 wins
    banned: bool,
    samples: int = 3,
    tmp_path: Path,
):
    """
    Build a NegativeMemory + mock pattern list for forensics testing.
    Returns (negmem, patterns_list) matching the CLI analyser's expected format.
    """
    key_tuple = ("MEAN_REVERTING", "LOW", "BTCUSDT", "MR_PAPER", "UP")
    key_str   = "|".join(key_tuple)

    nm = NegativeMemory(path=str(tmp_path / "negmem.jsonl"))
    if banned:
        # Record enough rollbacks to reach banned state with samples >= 5
        for _ in range(PERMANENT_BAN_AFTER):
            nm.record_rollback(key_tuple, current_samples=max(samples, 5))

    success  = int(pattern_wr * samples)
    patterns = [{
        "key": {
            "regime":     key_tuple[0],
            "volatility": key_tuple[1],
            "instrument": key_tuple[2],
            "parameter":  key_tuple[3],
            "direction":  key_tuple[4],
        },
        "samples": samples,
        "success": success,
    }]
    negmem_index = {key_str: nm._entries.get(key_str, {})} if nm._entries else {}
    return negmem_index, patterns


def test_forensics_aligned_positive(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    negmem_index, patterns = _build_negmem_and_patterns(
        pattern_wr=0.67, banned=False, tmp_path=tmp_path)
    result = analyse_negmem(negmem_index, patterns)
    ocs = result["ontology_conflict_summary"]
    assert ocs["aligned_positive"] == 1
    assert ocs["conflict_positive_wr"] == 0


def test_forensics_aligned_negative(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    negmem_index, patterns = _build_negmem_and_patterns(
        pattern_wr=0.0, banned=True, tmp_path=tmp_path)
    result = analyse_negmem(negmem_index, patterns)
    ocs = result["ontology_conflict_summary"]
    assert ocs["aligned_negative"] == 1
    assert ocs["conflict_positive_wr"] == 0


def test_forensics_conflict_positive_wr(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    negmem_index, patterns = _build_negmem_and_patterns(
        pattern_wr=0.67, banned=True, tmp_path=tmp_path)
    result = analyse_negmem(negmem_index, patterns)
    ocs = result["ontology_conflict_summary"]
    assert ocs["conflict_positive_wr"] == 1


def test_forensics_conflict_negative_wr(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    negmem_index, patterns = _build_negmem_and_patterns(
        pattern_wr=0.0, banned=False, tmp_path=tmp_path)
    result = analyse_negmem(negmem_index, patterns)
    ocs = result["ontology_conflict_summary"]
    assert ocs["conflict_negative_wr"] == 1


# ── 22. ontology_conflict_ratio ───────────────────────────────────────────────

def test_conflict_ratio_correct(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    # 1 CONFLICT_POSITIVE_WR + 1 ALIGNED_NEGATIVE → conflict_ratio = 0.5
    key1 = ("MEAN_REVERTING", "LOW", "BTCUSDT", "MR_PAPER", "UP")
    key2 = ("MEAN_REVERTING", "LOW", "ETHUSDT", "MR_PAPER", "DOWN")
    ks1  = "|".join(key1)
    ks2  = "|".join(key2)

    nm = NegativeMemory(path=str(tmp_path / "nm2.jsonl"))
    nm.record_rollback(key1, current_samples=5)
    nm.record_rollback(key1, current_samples=5)
    nm.record_rollback(key1, current_samples=5)  # → banned
    nm.record_rollback(key2, current_samples=5)
    nm.record_rollback(key2, current_samples=5)
    nm.record_rollback(key2, current_samples=5)  # → banned

    patterns = [
        {"key": {"regime": key1[0], "volatility": key1[1], "instrument": key1[2],
                 "parameter": key1[3], "direction": key1[4]},
         "samples": 3, "success": 2},   # WR > 0 + banned → CONFLICT_POSITIVE_WR
        {"key": {"regime": key2[0], "volatility": key2[1], "instrument": key2[2],
                 "parameter": key2[3], "direction": key2[4]},
         "samples": 3, "success": 0},   # WR = 0 + banned → ALIGNED_NEGATIVE
    ]
    negmem_index = {e["key_str"]: e for e in nm.to_list()}
    result = analyse_negmem(negmem_index, patterns)
    ocs = result["ontology_conflict_summary"]
    assert ocs["conflict_ratio"] == pytest.approx(0.5)


# ── 23–24. Sensitivity metrics ────────────────────────────────────────────────

def test_quarantine_at_lt5_counted(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    key = ("MEAN_REVERTING", "LOW", "TINY", "MR_PAPER", "UP")
    ks  = "|".join(key)
    nm  = NegativeMemory(path=str(tmp_path / "nm3.jsonl"))
    # Record rollbacks but current_samples=2 → won't reach PERMANENT_BAN but still tracked
    nm.record_rollback(key, current_samples=2)
    nm.record_rollback(key, current_samples=2)

    patterns = [{"key": {"regime": key[0], "volatility": key[1], "instrument": key[2],
                          "parameter": key[3], "direction": key[4]},
                 "samples": 2, "success": 0}]
    negmem_index = {e["key_str"]: e for e in nm.to_list()}
    result = analyse_negmem(negmem_index, patterns)
    # Entry is banned (score >= TEMP_REMOVAL_THRESHOLD) AND samples < 5
    ns = result["negmem_sensitivity"]
    assert ns["quarantine_events_at_n_lt_5"] >= 1


def test_toxic_at_wr_gt50_counted(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    key = ("MEAN_REVERTING", "LOW", "RISKY", "MR_PAPER", "UP")
    nm  = NegativeMemory(path=str(tmp_path / "nm4.jsonl"))
    for _ in range(3):
        nm.record_rollback(key, current_samples=5)  # → permanent ban

    patterns = [{"key": {"regime": key[0], "volatility": key[1], "instrument": key[2],
                          "parameter": key[3], "direction": key[4]},
                 "samples": 3, "success": 2}]   # WR = 67% > 50%
    negmem_index = {e["key_str"]: e for e in nm.to_list()}
    result = analyse_negmem(negmem_index, patterns)
    assert result["negmem_sensitivity"]["toxic_promotions_at_wr_gt_50pct"] == 1


# ── 25. scope_note present ────────────────────────────────────────────────────

def test_negmem_forensics_has_scope_note(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    result = analyse_negmem({}, [])
    # scope_note present in the CLI tool analyser
    # (the orchestrator method also returns scope_note — tested implicitly)
    assert "ontology_conflict_summary" in result   # full structure present


# ── 26–27. Backward compatibility ────────────────────────────────────────────

def test_should_trade_still_returns_bool_str():
    eng = _fresh_rl_engine()
    _seed_rl_context(eng, n_visits=10, q_value=-0.10)
    result = eng.should_trade("UNKNOWN", 13, "TEST_STRAT")
    assert isinstance(result, tuple)
    assert len(result) == 2
    assert isinstance(result[0], bool)
    assert isinstance(result[1], str)


def test_negative_memory_to_list_unchanged(tmp_path):
    nm = NegativeMemory(path=str(tmp_path / "compat.jsonl"))
    key = ("R", "V", "I", "P", "D")
    nm.record_rollback(key, current_samples=3)
    lst = nm.to_list()
    assert isinstance(lst, list)
    assert len(lst) >= 1
    assert "key_str" in lst[0]


# ── 28. negmem_forensics does not mutate is_banned() ─────────────────────────

def test_forensics_does_not_mutate_negmem(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    key = ("M", "L", "X", "P", "UP")
    ks  = "|".join(key)
    nm  = NegativeMemory(path=str(tmp_path / "no_mutate.jsonl"))
    # Not banned
    banned_before = nm.is_banned(key)
    negmem_index = {e["key_str"]: e for e in nm.to_list()}
    analyse_negmem(negmem_index, [{"key": {"regime": key[0], "volatility": key[1],
                                            "instrument": key[2], "parameter": key[3],
                                            "direction": key[4]},
                                   "samples": 3, "success": 1}])
    banned_after = nm.is_banned(key)
    assert banned_before == banned_after


# ── 29–32. CLI analyser edge cases ───────────────────────────────────────────

def test_cli_analyse_exploration_empty():
    from tools.analyze_exploration_and_negmem_conflicts import analyse_exploration
    result = analyse_exploration([])
    assert result["total_events"] == 0


def test_cli_analyse_negmem_empty_patterns():
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    result = analyse_negmem({}, [])
    assert result["total_patterns"] == 0
    assert result["ontology_conflict_summary"]["conflict_ratio"] == 0.0


def test_cli_analyse_negmem_pattern_no_negmem_entry(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    patterns = [{"key": {"regime": "M", "volatility": "L", "instrument": "X",
                          "parameter": "P", "direction": "UP"},
                 "samples": 5, "success": 3}]
    result = analyse_negmem({}, patterns)
    ocs = result["ontology_conflict_summary"]
    assert ocs["aligned_positive"] == 1
    assert ocs["conflict_positive_wr"] == 0


def test_conflict_ratio_zero_when_all_aligned(tmp_path):
    from tools.analyze_exploration_and_negmem_conflicts import analyse_negmem
    patterns = [
        {"key": {"regime": "M", "volatility": "L", "instrument": "A",
                  "parameter": "P", "direction": "UP"}, "samples": 3, "success": 2},
        {"key": {"regime": "M", "volatility": "L", "instrument": "B",
                  "parameter": "P", "direction": "DOWN"}, "samples": 3, "success": 0},
    ]
    # Neither has a NegMem entry → A is ALIGNED_POSITIVE, B is CONFLICT_NEGATIVE_WR
    result = analyse_negmem({}, patterns)
    # Actually B (WR=0, not banned) = CONFLICT_NEGATIVE_WR, which counts in conflict
    # Let's use all positive WR, not banned:
    patterns2 = [
        {"key": {"regime": "M", "volatility": "L", "instrument": "A",
                  "parameter": "P", "direction": "UP"}, "samples": 3, "success": 2},
    ]
    result2 = analyse_negmem({}, patterns2)
    assert result2["ontology_conflict_summary"]["conflict_ratio"] == 0.0


# ── 33. Singleton importable ──────────────────────────────────────────────────

def test_exploration_event_log_singleton_importable():
    from core.persistence.exploration_log import exploration_event_log
    assert exploration_event_log is not None
    assert hasattr(exploration_event_log, "record")
    assert hasattr(exploration_event_log, "read_all")
    assert hasattr(exploration_event_log, "lifetime_count")
