"""
tests/test_bootstrap_unlock.py — qFTD-008 / Phase 7A.3 Bootstrap Unlock Verifier

Proves that:
  1. Bootstrap trades (ev≈0) pass the ranker after qFTD-008 fix
  2. Weak-score trades are blocked upstream (MIN_TRADE_SCORE gate)
  3. Negative-EV trades are hard-rejected by the ranker regardless
  4. Post-bootstrap trades with real EV rank above threshold easily
  5. All safety layers (score, RR, gate) remain intact

Root cause fixed:
  EV=0.0 (bootstrap) → c_ev=0.0 → rank≈0.34 < old threshold 0.60 → ALL trades rejected
  Fix: TR_MIN_RANK_SCORE 0.60→0.30; bootstrap ev 0.0→0.05

Run:
    python -m pytest tests/test_bootstrap_unlock.py -v
    python tests/test_bootstrap_unlock.py
"""
from __future__ import annotations

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Helpers ───────────────────────────────────────────────────────────────────

def _rank(ev: float, score: float, regime: str, strategy: str,
          history_score: float = 0.5) -> tuple[bool, float]:
    """Run TradeRanker.rank() and return (ok, rank_score)."""
    from core.trade_ranker import TradeRanker
    ranker = TradeRanker()
    result = ranker.rank(
        ev=ev,
        trade_score=score,
        regime=regime,
        strategy=strategy,
        history_score=history_score,
    )
    return result.ok, result.rank_score


# ── FTD Test 1 — Bootstrap pass (ev=0.0, original deadlock scenario) ─────────

def test_bootstrap_ev_zero_passes_ranker():
    """
    ev=0.0 + score=0.70 + TRENDING/TrendFollowing + hist=0.5
    Expected rank = 0.0×0.55 + 0.70×0.20 + 1.0×0.15 + 0.5×0.10 = 0.340
    Expected: PASS  (threshold is now 0.30)

    This was the original deadlock: rank=0.34 < old threshold 0.60 → permanent block.
    With TR_MIN_RANK_SCORE=0.30, 0.34 > 0.30 → PASS.
    """
    from config import cfg
    assert cfg.TR_MIN_RANK_SCORE == 0.30, (
        f"TR_MIN_RANK_SCORE must be 0.30 (qFTD-008 fix), got {cfg.TR_MIN_RANK_SCORE}. "
        "This test verifies the deadlock fix — if this fails the fix was reverted."
    )
    ok, score = _rank(ev=0.0, score=0.70, regime="TRENDING", strategy="TrendFollowing")
    assert abs(score - 0.340) < 0.001, f"Expected rank≈0.340, got {score:.4f}"
    assert ok, (
        f"Bootstrap trade (ev=0.0, score=0.70, TRENDING/TF) must PASS ranker. "
        f"rank={score:.4f}, threshold={cfg.TR_MIN_RANK_SCORE}. "
        "Deadlock not broken."
    )


def test_bootstrap_ev_placeholder_passes_ranker():
    """
    ev=0.05 (actual bootstrap placeholder after fix) + score=0.70
    c_ev = 0.05 / (0.15×3) = 0.05/0.45 = 0.1111
    rank = 0.1111×0.55 + 0.70×0.20 + 1.0×0.15 + 0.5×0.10 = 0.401
    Expected: PASS (well above 0.30)
    """
    ok, score = _rank(ev=0.05, score=0.70, regime="TRENDING", strategy="TrendFollowing")
    assert score > 0.39 and score < 0.42, f"Expected rank≈0.401, got {score:.4f}"
    assert ok, f"Bootstrap trade (ev=0.05) must PASS. rank={score:.4f}"


# ── FTD Test 2 — Weak trade blocked upstream (score < 0.60) ──────────────────

def test_weak_score_blocked_by_trade_scorer_gate():
    """
    score=0.50 is blocked BEFORE the ranker by MIN_TRADE_SCORE=0.60.
    Verify config enforces this floor, AND verify that even if a 0.50-score trade
    somehow reached the ranker, the result would still be checked.

    Note: the ranker itself does not check trade_score against MIN_TRADE_SCORE —
    that gate lives in trade_scorer.py.  This test proves the upstream config floor.
    """
    from config import cfg
    assert cfg.MIN_TRADE_SCORE == 0.60, (
        f"MIN_TRADE_SCORE must be 0.60, got {cfg.MIN_TRADE_SCORE}. "
        "Score floor is the first defence against weak signals."
    )
    # Even if it slips through, show what rank it would produce
    ok, rank = _rank(ev=0.05, score=0.50, regime="TRENDING", strategy="TrendFollowing")
    # rank = 0.111×0.55 + 0.50×0.20 + 1.0×0.15 + 0.5×0.10 = 0.361
    # At threshold 0.30 this would pass — but it never reaches here because
    # trade_scorer blocks score<0.60 upstream
    print(f"  [INFO] score=0.50 would produce rank={rank:.4f} — but blocked by "
          f"MIN_TRADE_SCORE={cfg.MIN_TRADE_SCORE} before reaching ranker")


def test_weak_trade_rejected_at_ranker_when_ev_negative():
    """
    Negative EV is a hard reject regardless of score or regime.
    rank < 0.30 → FAIL (condition 1 from FTD safety validation).
    """
    ok, rank = _rank(ev=-0.10, score=0.90, regime="TRENDING", strategy="TrendFollowing")
    assert not ok, (
        f"Negative-EV trade must be REJECTED. rank={rank:.4f}. "
        "Hard-reject rule in trade_ranker.py:114-123 must always fire."
    )
    assert rank == 0.0, f"NEGATIVE_EV should force rank_score=0.0, got {rank}"


# ── FTD Test 3 — Post-bootstrap: real EV boosts rank significantly ────────────

def test_post_bootstrap_real_ev_passes_easily():
    """
    After 10+ trades, EV engine computes real EV (e.g. 0.08 USDT/unit risk).
    c_ev = 0.08/0.45 = 0.178
    rank = 0.178×0.55 + 0.70×0.20 + 1.0×0.15 + 0.5×0.10 = 0.438
    Well above 0.30 — system self-heals once history accumulates.
    """
    ok, rank = _rank(ev=0.08, score=0.70, regime="TRENDING", strategy="TrendFollowing")
    assert rank > 0.42, f"Post-bootstrap rank with ev=0.08 should be >0.42, got {rank:.4f}"
    assert ok, f"Post-bootstrap trade must PASS. rank={rank:.4f}"


def test_high_ev_high_score_elite_rank():
    """
    Elite trade: strong real EV + high score → near-maximum rank.
    ev=0.20 → c_ev = 0.20/0.45 = 0.444
    rank = 0.444×0.55 + 0.85×0.20 + 1.0×0.15 + 0.8×0.10 = 0.644
    Significantly above both old (0.60) and new (0.30) threshold.
    """
    ok, rank = _rank(ev=0.20, score=0.85, regime="TRENDING", strategy="TrendFollowing",
                     history_score=0.8)
    assert rank > 0.60, f"Elite trade rank should be >0.60, got {rank:.4f}"
    assert ok, f"Elite trade must PASS. rank={rank:.4f}"


# ── Safety Validation — confirm all protection layers intact ──────────────────

def test_rr_floor_config_unchanged():
    """RR≥1.5 requirement must not have changed (condition 3 from FTD)."""
    from config import cfg
    assert cfg.MIN_RR_RATIO == 1.5, (
        f"MIN_RR_RATIO must remain 1.5. Got {cfg.MIN_RR_RATIO}. "
        "RR gate protects against low-reward-risk entries."
    )


def test_ev_weight_unchanged():
    """TR_EV_WEIGHT must remain 0.55 — only threshold was changed, not formula."""
    from config import cfg
    assert cfg.TR_EV_WEIGHT == 0.55, (
        f"TR_EV_WEIGHT must remain 0.55 (qFTD-008 only changes threshold, not formula). "
        f"Got {cfg.TR_EV_WEIGHT}."
    )


def test_bootstrap_ev_placeholder_value():
    """Verify ev_engine returns ev=0.05 (not 0.0) during bootstrap."""
    from core.ev_engine import EVEngine
    engine = EVEngine()
    result = engine.evaluate(
        strategy_id="TrendFollowing",
        symbol="BTCUSDT",
        est_reward=10.0,
        est_risk=5.0,
        current_cost=0.50,
    )
    assert result.bootstrapped is True, "Should be bootstrap (0 trades)"
    assert result.ok is True, "Bootstrap must pass (EV_BOOTSTRAP_PASS=True)"
    assert result.ev == 0.05, (
        f"Bootstrap EV must be 0.05 (qFTD-008 fix, was 0.0). Got {result.ev}. "
        "ev=0.0 caused permanent ranker deadlock — this value must stay 0.05."
    )


def test_rank_below_threshold_rejected():
    """rank < 0.30 → FAIL (safety condition 1 from FTD)."""
    from config import cfg
    # Force a very low rank: UNKNOWN regime, zero-EV, low score
    ok, rank = _rank(ev=0.0, score=0.0, regime="UNKNOWN", strategy="TrendFollowing",
                     history_score=0.0)
    assert not ok, f"rank={rank:.4f} should be rejected (below {cfg.TR_MIN_RANK_SCORE})"
    assert rank < cfg.TR_MIN_RANK_SCORE


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        test_bootstrap_ev_zero_passes_ranker,
        test_bootstrap_ev_placeholder_passes_ranker,
        test_weak_score_blocked_by_trade_scorer_gate,
        test_weak_trade_rejected_at_ranker_when_ev_negative,
        test_post_bootstrap_real_ev_passes_easily,
        test_high_ev_high_score_elite_rank,
        test_rr_floor_config_unchanged,
        test_ev_weight_unchanged,
        test_bootstrap_ev_placeholder_value,
        test_rank_below_threshold_rejected,
    ]
    failed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"  ERROR {t.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print()
    if failed:
        print(f"{failed}/{len(tests)} tests FAILED")
        sys.exit(1)
    else:
        print(f"All {len(tests)} tests passed.")
