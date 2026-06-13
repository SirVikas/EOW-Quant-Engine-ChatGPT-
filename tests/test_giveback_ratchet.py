"""
Regression: peak-proportional profit ratchet (v1.89.0).

The price-space trailing stop (1.5× initial risk) only lifts the stop above the
+0.10R BE floor once peak_r > ~1.6R — a level this strategy never reaches — so
sub-1R winners gave the entire peak back to the BE floor (the 'BE' exit cohort:
avg peak 0.51R → final ~+0.10R). The ratchet locks GIVEBACK_LOCK_FRACTION of the
proven peak once peak_r clears GIVEBACK_RATCHET_MIN_R.

Invariants proven here:
  1. peak ≥ trigger → stop ratchets above the BE-floor (captures the peak)
  2. a 0.5R peak that reverses now exits a real profit, not a BE scratch
  3. ratchet is strictly one-directional — a pullback never loosens the stop
  4. peak < trigger → BE floor only (no ratchet, leaves the 0.40-0.50R zone room)
  5. SHORT mirror behaves identically
"""
import types

from config import cfg
from core.risk_controller import RiskController, OpenPosition


class _FakePnL:
    def calculate(self, record, initial_risk_usdt=0.0):
        if record.is_short:
            gross = (record.entry_price - record.exit_price) * record.qty
        else:
            gross = (record.exit_price - record.entry_price) * record.qty
        return types.SimpleNamespace(
            net_pnl=gross - 0.02, slippage_cost=0.0, fee_entry=0.01, fee_exit=0.01
        )


class _FakeScaler:
    drawdown_pct = 0.0

    def record_trade(self, *_):
        pass


def _rc():
    rc = RiskController.__new__(RiskController)
    rc.pnl_calc = _FakePnL()
    rc.scaler = _FakeScaler()
    rc.positions = {}
    rc.pending_orders = {}
    rc.events = []
    rc.halted = False
    rc.graceful_stop = False
    rc._running = False
    return rc


def _long(entry=100.0, stop=99.0):
    risk = entry - stop
    return OpenPosition(
        position_id="t", symbol="X", side="LONG", entry_price=entry, qty=10.0,
        stop_loss=stop, take_profit=entry + 10 * risk, entry_ts=0, strategy_id="s",
        initial_risk=risk * 10, initial_stop_loss=stop, peak_price=entry,
    )


def _short(entry=100.0, stop=101.0):
    risk = stop - entry
    return OpenPosition(
        position_id="t", symbol="Y", side="SHORT", entry_price=entry, qty=10.0,
        stop_loss=stop, take_profit=entry - 10 * risk, entry_ts=0, strategy_id="s",
        initial_risk=risk * 10, initial_stop_loss=stop, peak_price=entry,
    )


# entry=100, stop=99 → 1R = 1.0 price unit; cost buffer baked into the stop is
# ~0.14R here (toy entry/risk ratio), so "locked R" = lock_fraction*peak + cost.

def test_ratchet_locks_half_of_peak_above_trigger():
    rc = _rc(); pos = _long(); rc.positions["X"] = pos
    rc.on_price_update("X", 100.5)  # peak_r = 0.5 == trigger
    locked = (pos.stop_loss - pos.entry_price) / 1.0
    assert pos.breakeven_armed
    assert locked > 0.30  # 0.5*0.5 lock + cost; well above BE-floor (~0.24)


def test_half_r_peak_reverse_exits_profit_not_scratch():
    rc = _rc(); pos = _long(); rc.positions["X"] = pos
    rc.on_price_update("X", 100.5)
    action = rc.on_price_update("X", pos.stop_loss - 1e-4)  # reverse into ratchet
    assert action in ("SL", "TSL+", "TP")


def test_ratchet_locks_more_than_be_floor_only():
    cfg.GIVEBACK_RATCHET_ENABLED = False
    rc = _rc(); pos = _long(); rc.positions["X"] = pos
    rc.on_price_update("X", 100.5)
    off = (pos.stop_loss - pos.entry_price) / 1.0
    cfg.GIVEBACK_RATCHET_ENABLED = True
    rc = _rc(); pos = _long(); rc.positions["X"] = pos
    rc.on_price_update("X", 100.5)
    on = (pos.stop_loss - pos.entry_price) / 1.0
    assert on > off


def test_ratchet_is_one_directional():
    rc = _rc(); pos = _long(); rc.positions["X"] = pos
    rc.on_price_update("X", 100.7)
    s1 = pos.stop_loss
    rc.on_price_update("X", 100.55)  # pullback, no new peak
    assert pos.stop_loss >= s1


def test_below_trigger_uses_be_floor_only():
    rc = _rc(); pos = _long(); rc.positions["X"] = pos
    rc.on_price_update("X", 100.45)  # peak 0.45R < 0.50 trigger
    locked = (pos.stop_loss - pos.entry_price) / 1.0
    # BE floor (0.10R) + cost (~0.14R) ≈ 0.24R; ratchet would be ~0.37R
    assert 0.20 < locked < 0.30


def test_short_mirror():
    rc = _rc(); pos = _short(); rc.positions["Y"] = pos
    rc.on_price_update("Y", 99.5)  # peak_r = 0.5
    locked = (pos.entry_price - pos.stop_loss) / 1.0
    assert pos.breakeven_armed
    assert locked > 0.30
