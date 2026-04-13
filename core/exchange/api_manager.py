"""
EOW Quant Engine — API Credential Manager
Bridges the VaultManager with BinanceClient.
Handles PAPER/LIVE mode selection and falls back gracefully when no
credentials are configured.
"""
from __future__ import annotations

from typing import Optional

from loguru import logger

from config import cfg
from core.exchange.binance_client import BinanceClient, ClientMode


class ApiManager:
    """
    Single point of truth for the active Binance API connection.

    On init it reads credentials from:
      1. The encrypted vault (VaultManager) — preferred
      2. Environment variables (BINANCE_API_KEY / BINANCE_API_SECRET) — fallback

    The client is always READ_ONLY in PAPER mode; TRADE mode is only
    enabled when cfg.TRADE_MODE == "LIVE" AND credentials are present.
    """

    def __init__(self):
        self._client: Optional[BinanceClient] = None
        self._connected = False

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    async def connect(self) -> bool:
        """
        Load credentials and connect to Binance.
        Returns True if the connection succeeded, False otherwise.
        The engine continues to run (paper-only) on False.
        """
        api_key, api_secret = self._load_credentials()

        if not api_key or not api_secret:
            logger.info(
                "[API-MGR] No API credentials configured — "
                "running in market-data-only mode."
            )
            self._connected = False
            return False

        mode = (
            ClientMode.TRADE
            if cfg.TRADE_MODE == "LIVE"
            else ClientMode.READ_ONLY
        )

        self._client = BinanceClient(
            api_key    = api_key,
            api_secret = api_secret,
            testnet    = cfg.BINANCE_TESTNET,
            mode       = mode,
        )
        self._connected = await self._client.connect()
        return self._connected

    async def close(self):
        if self._client:
            await self._client.close()
        self._connected = False

    # ── Public interface ──────────────────────────────────────────────────────

    @property
    def is_connected(self) -> bool:
        return self._connected

    @property
    def client(self) -> Optional[BinanceClient]:
        return self._client if self._connected else None

    async def get_balance(self, asset: str = "USDT") -> float:
        if not self._client or not self._connected:
            return 0.0
        return await self._client.get_balance(asset)

    async def ping(self) -> bool:
        if not self._client:
            return False
        return await self._client.ping()

    def summary(self) -> dict:
        if self._client and self._connected:
            return self._client.summary()
        return {
            "connected": False,
            "mode":      "NONE",
            "testnet":   cfg.BINANCE_TESTNET,
        }

    # ── Internals ─────────────────────────────────────────────────────────────

    def _load_credentials(self) -> tuple[str, str]:
        """
        Load credentials from environment variables / config.py.
        The vault (VaultManager) requires an interactive master password and
        cannot be read here at boot time — credentials must be supplied via
        BINANCE_API_KEY / BINANCE_API_SECRET environment variables or .env file.
        Returns (api_key, api_secret) — empty strings if nothing found.
        """
        key    = cfg.BINANCE_API_KEY
        secret = cfg.BINANCE_API_SECRET
        if key and secret:
            logger.debug("[API-MGR] Credentials loaded from environment.")
            return key, secret
        return "", ""


# ── Module-level singleton ────────────────────────────────────────────────────
api_manager = ApiManager()
