"""
EOW Quant Engine — Binance Client Wrapper
Thin async wrapper around python-binance (python-binance==1.0.19).

Supports two modes:
  READ_ONLY — only account info / balance queries (no order placement)
  TRADE     — full order placement (used only in LIVE mode)

Usage:
    client = BinanceClient(api_key, api_secret, testnet=True)
    await client.connect()
    bal = await client.get_balance("USDT")
    await client.close()
"""
from __future__ import annotations

from enum import Enum
from typing import Dict, Optional

from binance import AsyncClient
from loguru import logger


class ClientMode(str, Enum):
    READ_ONLY = "READ_ONLY"
    TRADE     = "TRADE"


class BinanceClient:
    """
    Async Binance client with explicit READ_ONLY / TRADE mode enforcement.
    All methods are coroutines — await them inside an async context.
    """

    def __init__(
        self,
        api_key:    str,
        api_secret: str,
        testnet:    bool = True,
        mode:       ClientMode = ClientMode.READ_ONLY,
    ):
        self._api_key    = api_key
        self._api_secret = api_secret
        self._testnet    = testnet
        self._mode       = mode
        self._client: Optional[AsyncClient] = None

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """
        Create the underlying AsyncClient and verify connectivity via ping().
        Returns True on success, False on any error.
        """
        try:
            self._client = await AsyncClient.create(
                api_key    = self._api_key,
                api_secret = self._api_secret,
                testnet    = self._testnet,
            )
            await self._client.ping()
            logger.info(
                f"[BINANCE] Connected "
                f"({'TESTNET' if self._testnet else 'LIVE'} | {self._mode.value})"
            )
            return True
        except Exception as exc:
            logger.warning(f"[BINANCE] connect() failed: {exc}")
            self._client = None
            return False

    async def close(self):
        if self._client:
            try:
                await self._client.close_connection()
            except Exception:
                pass
            self._client = None

    # ── Connectivity ──────────────────────────────────────────────────────────

    async def ping(self) -> bool:
        """Return True if Binance API responds to a ping."""
        if not self._client:
            return False
        try:
            await self._client.ping()
            return True
        except Exception:
            return False

    # ── Account (READ_ONLY safe) ──────────────────────────────────────────────

    async def get_account(self) -> Optional[dict]:
        """Return full account info dict, or None on error."""
        if not self._client:
            return None
        try:
            return await self._client.get_account()
        except Exception as exc:
            logger.debug(f"[BINANCE] get_account error: {exc}")
            return None

    async def get_balance(self, asset: str = "USDT") -> float:
        """Return free balance for *asset*, or 0.0 on error."""
        account = await self.get_account()
        if not account:
            return 0.0
        for b in account.get("balances", []):
            if b.get("asset") == asset:
                return float(b.get("free", 0.0))
        return 0.0

    # ── Properties ────────────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._client is not None

    @property
    def mode(self) -> ClientMode:
        return self._mode

    @property
    def testnet(self) -> bool:
        return self._testnet

    def summary(self) -> dict:
        return {
            "connected": self.is_connected,
            "mode":      self._mode.value,
            "testnet":   self._testnet,
        }
