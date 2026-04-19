"""
EOW Quant Engine — Sector Correlation Guard  (Phase 3)

Prevents simultaneous over-exposure to highly correlated assets.
e.g. opening BTC + ETH + SOL LONG at the same time = 3× the risk of a
single Layer-1 market crash — not 3 independent bets.

Rule: At most MAX_SECTOR_EXPOSURE (2) open positions from the same sector.
Unknown / uncategorised symbols ("OTHER") are exempt — no artificial cap.
"""
from __future__ import annotations

from typing import Dict
from loguru import logger


# ── Sector definitions ─────────────────────────────────────────────────────────
# Add new pairs here as they appear in the TOP_N universe.
SECTOR_MAP: Dict[str, str] = {
    # Layer 1 blockchains — highly correlated, move together
    "BTCUSDT":   "LAYER1", "ETHUSDT":   "LAYER1", "SOLUSDT":   "LAYER1",
    "ADAUSDT":   "LAYER1", "AVAXUSDT":  "LAYER1", "DOTUSDT":   "LAYER1",
    "BNBUSDT":   "LAYER1", "XRPUSDT":   "LAYER1", "LTCUSDT":   "LAYER1",
    "ATOMUSDT":  "LAYER1", "NEARUSDT":  "LAYER1", "APTUSDT":   "LAYER1",
    "SUIUSDT":   "LAYER1", "ALGOUSDT":  "LAYER1", "FTMUSDT":   "LAYER1",
    "HBARUSDT":  "LAYER1", "XLMUSDT":   "LAYER1", "ICPUSDT":   "LAYER1",
    "FILUSDT":   "LAYER1", "THETAUSDT": "LAYER1", "VETUSDT":   "LAYER1",
    # Layer 2 / Scaling solutions
    "MATICUSDT": "LAYER2", "ARBUSDT":   "LAYER2", "OPUSDT":    "LAYER2",
    "IMXUSDT":   "LAYER2", "STRKUSDT":  "LAYER2", "ZKUSDT":    "LAYER2",
    # DeFi protocols
    "UNIUSDT":   "DEFI",   "AAVEUSDT":  "DEFI",   "CRVUSDT":   "DEFI",
    "MKRUSDT":   "DEFI",   "COMPUSDT":  "DEFI",   "SUSHIUSDT": "DEFI",
    "DYDXUSDT":  "DEFI",   "SNXUSDT":   "DEFI",
    # AI / Data tokens
    "FETUSDT":   "AI",     "AGIXUSDT":  "AI",     "RENDERUSDT":"AI",
    "WLDUSDT":   "AI",     "OCEANUSDT": "AI",
    # Meme coins
    "DOGEUSDT":  "MEME",   "SHIBUSDT":  "MEME",   "PEPEUSDT":  "MEME",
    "BONKUSDT":  "MEME",   "FLOKIUSDT": "MEME",
    # Oracle / Infrastructure
    "LINKUSDT":  "ORACLE", "BANDUSDT":  "ORACLE", "APIUSDT":   "ORACLE",
    # Gaming / Metaverse
    "AXSUSDT":   "GAMING", "SANDUSDT":  "GAMING", "MANAUSDT":  "GAMING",
    "GALAUSDT":  "GAMING", "ENJUSDT":   "GAMING",
}

MAX_SECTOR_EXPOSURE = 2   # max open positions in the same sector simultaneously


def get_sector(symbol: str) -> str:
    return SECTOR_MAP.get(symbol, "OTHER")


class SectorGuard:
    """
    Stateless guard — reads the live open_positions dict on every check.
    No state to maintain; simply count same-sector open positions.
    """

    def check(self, symbol: str, open_positions: dict) -> tuple[bool, str]:
        """
        Returns (allowed, reason).
          allowed=True  → within sector exposure limit, proceed.
          allowed=False → sector at capacity, skip signal.
        """
        sector = get_sector(symbol)
        if sector == "OTHER":
            return True, ""   # unknown sector — no cap applied

        same_sector = [
            sym for sym in open_positions
            if sym != symbol and get_sector(sym) == sector
        ]

        if len(same_sector) >= MAX_SECTOR_EXPOSURE:
            reason = (
                f"SECTOR_LIMIT({sector}:"
                f"{','.join(same_sector[:MAX_SECTOR_EXPOSURE])}"
                f"_already_open,max={MAX_SECTOR_EXPOSURE})"
            )
            logger.debug(f"[SECTOR] {symbol} blocked — {reason}")
            return False, reason
        return True, ""


# ── Module-level singleton ─────────────────────────────────────────────────────
sector_guard = SectorGuard()
