from core.strategy_engine import strategy_engine


def test_strategy_quality_rejects_low_rr():
    # MIN_SIGNAL_RR=1.1 (lowered from 1.5) — use rr=0.9 to stay below threshold
    out = strategy_engine.evaluate_signal(rr=0.9, confidence=0.9, regime="TRENDING")
    assert out.ok is False
    assert "LOW_RR" in out.reason


def test_strategy_quality_rejects_low_confidence():
    # MIN_SIGNAL_CONFIDENCE=0.10 (lowered from 0.5) — use confidence=0.05
    out = strategy_engine.evaluate_signal(rr=2.0, confidence=0.05, regime="TRENDING")
    assert out.ok is False
    assert "LOW_CONFIDENCE" in out.reason


def test_strategy_quality_accepts_safe_signal():
    out = strategy_engine.evaluate_signal(rr=1.8, confidence=0.7, regime="TRENDING")
    assert out.ok is True
