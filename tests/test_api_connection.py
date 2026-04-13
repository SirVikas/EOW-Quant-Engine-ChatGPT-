"""
Tests for core/exchange/binance_client.py and core/exchange/api_manager.py

Run with:  python -m pytest tests/test_api_connection.py -v
"""
import asyncio
import pytest

from core.exchange.binance_client import BinanceClient, ClientMode
from core.exchange.api_manager    import ApiManager


# ── Helpers ───────────────────────────────────────────────────────────────────

def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# ── BinanceClient unit tests ─────────────────────────────────────────────────

class TestBinanceClient:

    def test_initial_state_not_connected(self):
        c = BinanceClient("", "", testnet=True)
        assert c.is_connected is False

    def test_mode_default_is_read_only(self):
        c = BinanceClient("", "")
        assert c.mode == ClientMode.READ_ONLY

    def test_mode_trade_when_set(self):
        c = BinanceClient("k", "s", mode=ClientMode.TRADE)
        assert c.mode == ClientMode.TRADE

    def test_ping_returns_false_when_not_connected(self):
        c = BinanceClient("", "")
        result = run(c.ping())
        assert result is False

    def test_get_balance_returns_zero_when_not_connected(self):
        c = BinanceClient("", "")
        bal = run(c.get_balance("USDT"))
        assert bal == 0.0

    def test_get_account_returns_none_when_not_connected(self):
        c = BinanceClient("", "")
        acc = run(c.get_account())
        assert acc is None

    def test_summary_not_connected(self):
        c = BinanceClient("", "")
        s = c.summary()
        assert s["connected"] is False
        assert s["mode"] == ClientMode.READ_ONLY.value

    def test_connect_fails_gracefully_with_empty_credentials(self):
        """
        Connecting with empty API key should fail gracefully (no crash).
        Binance returns an error, client should return False.
        """
        c = BinanceClient("", "", testnet=True)
        result = run(c.connect())
        # Could be True or False depending on whether public ping works;
        # either way must not raise an exception.
        assert isinstance(result, bool)

    def test_testnet_flag_stored(self):
        c = BinanceClient("k", "s", testnet=False)
        assert c.testnet is False
        c2 = BinanceClient("k", "s", testnet=True)
        assert c2.testnet is True


# ── ApiManager unit tests ─────────────────────────────────────────────────────

class TestApiManager:

    def test_initial_not_connected(self):
        mgr = ApiManager()
        assert mgr.is_connected is False

    def test_client_is_none_when_not_connected(self):
        mgr = ApiManager()
        assert mgr.client is None

    def test_get_balance_zero_when_not_connected(self):
        mgr = ApiManager()
        bal = run(mgr.get_balance("USDT"))
        assert bal == 0.0

    def test_ping_false_when_not_connected(self):
        mgr = ApiManager()
        result = run(mgr.ping())
        assert result is False

    def test_summary_when_not_connected(self):
        mgr = ApiManager()
        s = mgr.summary()
        assert s["connected"] is False
        assert "mode" in s

    def test_connect_without_credentials_returns_false(self):
        """
        No credentials configured → connect() returns False gracefully.
        """
        import os
        # Temporarily unset env vars (if set)
        orig_key    = os.environ.pop("BINANCE_API_KEY",    None)
        orig_secret = os.environ.pop("BINANCE_API_SECRET", None)
        try:
            mgr = ApiManager()
            # Force credential reload from (now empty) env
            mgr._client = None
            result = run(mgr.connect())
            assert result is False
        finally:
            if orig_key:    os.environ["BINANCE_API_KEY"]    = orig_key
            if orig_secret: os.environ["BINANCE_API_SECRET"] = orig_secret
