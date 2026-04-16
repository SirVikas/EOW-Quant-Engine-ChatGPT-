from core.strategy_engine import strategy_engine


def test_strategy_quality_rejects_low_rr():
    out = strategy_engine.evaluate_signal(rr=1.2, confidence=0.9, regime="TRENDING")
    assert out.ok is False
    assert "LOW_RR" in out.reason


def test_strategy_quality_rejects_low_confidence():
    out = strategy_engine.evaluate_signal(rr=2.0, confidence=0.3, regime="TRENDING")
    assert out.ok is False
    assert "LOW_CONFIDENCE" in out.reason


def test_strategy_quality_accepts_safe_signal():
    out = strategy_engine.evaluate_signal(rr=1.8, confidence=0.7, regime="TRENDING")
    assert out.ok is True
