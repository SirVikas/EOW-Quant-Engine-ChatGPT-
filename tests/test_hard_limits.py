"""
Tests for immutable hard-limit enforcement + real partial close
(core/risk_controller.py).

MIN_EQUITY_FLOOR, MAX_LEVERAGE_CAP and the concurrent-position cap were
declared immutable in config (FTD-031C) but never enforced in any code path.
These tests pin the new enforcement so it cannot silently regress.

Run with:  python -m pytest tests/test_hard_limits.py -v
"""
import time
import uuid

import pytest

from config import cfg
from core.pnl_calculator import PurePnLCalculator
from core.risk_controller import OpenPosition, RiskController
from utils.capital_scaler import CapitalScaler


def _controller(equity: float = None) -> RiskController:
    scaler = CapitalScaler()
    if equity is not None:
        scaler.set_equity(equity)
    return RiskController(PurePnLCalculator(), scaler)


def _pos(symbol: str = "TESTUSDT", entry: float = 100.0, qty: float = 1.0,
         side: str = "LONG", sl: float = 97.0, tp: float = 106.0) -> OpenPosition:
    return OpenPosition(
        position_id=str(uuid.uuid4())[:8],
        symbol=symbol,
        side=side,
        entry_price=entry,
        qty=qty,
        stop_loss=sl,
        take_profit=tp,
        entry_ts=int(time.time() * 1000),
        strategy_id="TEST_STRAT",
        initial_risk=abs(entry - sl) * qty,
    )


class TestEquityFloor:

    def test_blocks_open_below_floor(self):
        rc = _controller(equity=cfg.INITIAL_CAPITAL * cfg.MIN_EQUITY_FLOOR * 0.99)
        assert rc.open_position(_pos()) is False
        assert rc.positions == {}

    def test_blocks_limit_order_below_floor(self):
        rc = _controller(equity=cfg.INITIAL_CAPITAL * cfg.MIN_EQUITY_FLOOR * 0.99)
        ok = rc.submit_limit_order(
            symbol="TESTUSDT", side="LONG", limit_price=100.0, qty=1.0,
            stop_loss=97.0, take_profit=106.0, strategy_id="TEST_STRAT",
            initial_risk=3.0, regime="TRENDING",
        )
        assert ok is False

    def test_allows_open_above_floor(self):
        rc = _controller(equity=cfg.INITIAL_CAPITAL)
        assert rc.open_position(_pos()) is True


class TestLeverageCap:

    def test_blocks_when_total_notional_exceeds_cap(self):
        rc = _controller(equity=1000.0)
        # Existing exposure right at the cap (3.0× equity by default)
        big_qty = (1000.0 * cfg.MAX_LEVERAGE_CAP) / 100.0
        assert rc.open_position(_pos(symbol="AUSDT", qty=big_qty)) is True
        assert rc.open_position(_pos(symbol="BUSDT", qty=1.0)) is False

    def test_pending_orders_count_toward_exposure(self):
        rc = _controller(equity=1000.0)
        big_qty = (1000.0 * cfg.MAX_LEVERAGE_CAP) / 100.0
        ok = rc.submit_limit_order(
            symbol="AUSDT", side="LONG", limit_price=100.0, qty=big_qty,
            stop_loss=97.0, take_profit=106.0, strategy_id="TEST_STRAT",
            initial_risk=3.0, regime="TRENDING",
        )
        assert ok is True
        assert rc.open_position(_pos(symbol="BUSDT", qty=1.0)) is False


class TestConcurrentCap:

    def test_blocks_at_max_concurrent(self):
        rc = _controller(equity=1_000_000.0)  # equity high enough that leverage never binds
        for i in range(cfg.TCE_MAX_CONCURRENT):
            assert rc.open_position(_pos(symbol=f"S{i}USDT", qty=0.01)) is True
        assert rc.open_position(_pos(symbol="OVERFLOWUSDT", qty=0.01)) is False
        assert len(rc.positions) == cfg.TCE_MAX_CONCURRENT


class TestPartialClose:

    def test_books_half_and_keeps_rest_running(self):
        rc = _controller(equity=1000.0)
        pos = _pos(entry=100.0, qty=2.0, sl=97.0)
        assert rc.open_position(pos) is True
        equity_before = rc.scaler.equity
        trades_before = len(rc.pnl_calc.trades)

        rec = rc.partial_close("TESTUSDT", exit_price=103.0, fraction=0.50)

        assert rec is not None
        assert rec.qty == pytest.approx(1.0)
        assert rec.gross_pnl == pytest.approx(3.0)       # (103-100) × 1.0
        assert rec.net_pnl < rec.gross_pnl                # fees deducted
        assert rec.net_pnl > 0
        assert rec.trade_id.endswith("-P")
        # Remaining position halved
        live = rc.positions["TESTUSDT"]
        assert live.qty == pytest.approx(1.0)
        assert live.initial_risk == pytest.approx(3.0)    # half of 6.0
        # Equity and trade ledger updated
        assert rc.scaler.equity == pytest.approx(equity_before + rec.net_pnl)
        assert len(rc.pnl_calc.trades) == trades_before + 1

    def test_returns_none_for_unknown_symbol(self):
        rc = _controller(equity=1000.0)
        assert rc.partial_close("MISSINGUSDT", exit_price=100.0) is None

    def test_returns_none_for_invalid_fraction(self):
        rc = _controller(equity=1000.0)
        assert rc.open_position(_pos()) is True
        assert rc.partial_close("TESTUSDT", exit_price=103.0, fraction=1.0) is None
        assert rc.partial_close("TESTUSDT", exit_price=103.0, fraction=0.0) is None


class TestLimitOrderRealism:

    def _submit(self, rc, limit_price=99.0):
        return rc.submit_limit_order(
            symbol="TESTUSDT", side="LONG", limit_price=limit_price, qty=1.0,
            stop_loss=96.0, take_profit=106.0, strategy_id="TEST_STRAT",
            initial_risk=3.0, regime="TRENDING",
        )

    def test_chased_order_fills_as_taker(self):
        rc = _controller(equity=1000.0)
        assert self._submit(rc, limit_price=99.0) is True
        # Price stays above the limit → chase triggers after PRICE_CHASE_TICKS
        for _ in range(cfg.PRICE_CHASE_TICKS):
            rc.on_price_update("TESTUSDT", 100.0)
        assert rc.pending_orders["TESTUSDT"].chased is True
        # Next tick fills at the chased (market) price — must book as MARKET
        rc.on_price_update("TESTUSDT", 100.0)
        assert "TESTUSDT" in rc.positions
        assert rc.positions["TESTUSDT"].order_type == "MARKET"

    def test_unchased_fill_stays_limit(self):
        rc = _controller(equity=1000.0)
        assert self._submit(rc, limit_price=99.0) is True
        rc.on_price_update("TESTUSDT", 98.9)   # price reaches the limit
        assert rc.positions["TESTUSDT"].order_type == "LIMIT"

    def test_stale_pending_order_expires(self):
        rc = _controller(equity=1000.0)
        assert self._submit(rc, limit_price=99.0) is True
        # Age the order past the TTL, then tick: it must be cancelled, not filled
        rc.pending_orders["TESTUSDT"].created_ts -= 200_000
        rc.on_price_update("TESTUSDT", 98.0)
        assert "TESTUSDT" not in rc.pending_orders
        assert "TESTUSDT" not in rc.positions
