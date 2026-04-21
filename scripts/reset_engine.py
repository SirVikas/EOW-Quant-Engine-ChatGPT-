"""
scripts/reset_engine.py — EOW Quant Engine clean-slate reset tool.

Clears only the `trades` table so equity/PnL state is reset to initial capital.
Preserves market data (candles, ticks, funding) which takes time to accumulate.

Usage:
    python scripts/reset_engine.py            # preview — shows row count, no change
    python scripts/reset_engine.py --confirm  # actually deletes trades rows

Safety:
    Refusing to run while the engine process is alive is not implemented here;
    stop the engine before running this script.
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

DB_PATH = Path("data/datalake.db")


def _row_counts(conn: sqlite3.Connection) -> dict:
    counts = {}
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for (table,) in cursor.fetchall():
        (n,) = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
        counts[table] = n
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Reset engine trade history")
    parser.add_argument(
        "--confirm", action="store_true",
        help="Actually delete rows (dry-run without this flag)",
    )
    args = parser.parse_args()

    if not DB_PATH.exists():
        print(f"[RESET] Database not found at {DB_PATH} — nothing to do.")
        sys.exit(0)

    with sqlite3.connect(DB_PATH) as conn:
        before = _row_counts(conn)
        print("[RESET] Current row counts:")
        for table, n in sorted(before.items()):
            print(f"  {table:<20} {n:>8} rows")

        trades_n = before.get("trades", 0)
        if trades_n == 0:
            print("[RESET] trades table already empty — nothing to do.")
            sys.exit(0)

        if not args.confirm:
            print(
                f"\n[RESET] DRY RUN — would delete {trades_n} rows from 'trades'.\n"
                f"        Re-run with --confirm to apply."
            )
            sys.exit(0)

        conn.execute("DELETE FROM trades")
        conn.commit()
        after = _row_counts(conn)
        print(f"\n[RESET] Deleted {trades_n} rows from 'trades'.")
        print("[RESET] Row counts after reset:")
        for table, n in sorted(after.items()):
            print(f"  {table:<20} {n:>8} rows")
        print("\n[RESET] Done. Start the engine with BOOT_MODE=FRESH (default).")


if __name__ == "__main__":
    main()
