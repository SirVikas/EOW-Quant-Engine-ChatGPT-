#!/usr/bin/env python3
"""
Risk-of-Ruin forensic helper.

Usage:
  python scripts/ror_forensics.py --base-url http://127.0.0.1:8000
"""
from __future__ import annotations

import argparse
import json
import sys
from urllib.error import URLError
from urllib.request import urlopen


def _get_json(url: str) -> dict:
    with urlopen(url, timeout=5) as r:  # nosec B310 - local dev helper
        return json.loads(r.read().decode("utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description="RoR forensic investigation helper")
    parser.add_argument("--base-url", default="http://127.0.0.1:8000", help="API base URL")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    try:
        analytics = _get_json(f"{base}/api/analytics")
        pnl = _get_json(f"{base}/api/pnl")
    except URLError as exc:
        print(f"[ERROR] Could not reach API: {exc}")
        return 2
    except Exception as exc:
        print(f"[ERROR] Unexpected error: {exc}")
        return 3

    ror = analytics.get("risk_of_ruin_pct", 0.0)
    dbg = analytics.get("risk_of_ruin_debug", {})
    print("=== Risk of Ruin Forensics ===")
    print(f"RoR: {ror:.2f}%")
    print(f"RoR status: {dbg.get('status', 'UNKNOWN')}")
    print(f"RoR reason: {dbg.get('reason', 'UNKNOWN')}")
    print(f"Valid R count: {dbg.get('valid_r_count', 'n/a')}")
    print(f"Wins/Losses: {dbg.get('wins_count', 'n/a')}/{dbg.get('losses_count', 'n/a')}")
    if dbg.get("status") == "ACTIVE":
        print(f"Win rate (valid-R): {dbg.get('win_rate', 0.0):.2%}")
        print(f"Avg R win / loss: {dbg.get('avg_r_win', 0.0)} / {dbg.get('avg_r_loss', 0.0)}")
    print("---")
    print(f"Session trades: {pnl.get('total_trades', 0)}")
    print(f"Session win-rate: {pnl.get('win_rate', 0.0)}%")
    print("Tip: if RoR status is WARMUP, metric is intentionally held at 0% until sample quality is sufficient.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
