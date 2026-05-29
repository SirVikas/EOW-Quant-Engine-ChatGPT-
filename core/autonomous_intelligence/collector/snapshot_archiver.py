"""
FTD-AIL-001: Snapshot Archiver — saves compressed JSON snapshots to disk.
"""
from __future__ import annotations
import gzip
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path


_ARCHIVE_ROOT = Path(__file__).parents[3] / "data" / "ail" / "archive"


def save_snapshot(label: str, data: dict) -> str:
    """
    Save a compressed JSON snapshot for the given label.
    Returns a lineage_id string in format AIL-{ts}-{hash16}.
    """
    ts_ms  = int(time.time() * 1000)
    ts_str = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S") + f"{ts_ms % 1000:03d}"
    date_dir = datetime.now(timezone.utc).strftime("%Y%m%d")

    payload = json.dumps(data, default=str)
    hash16  = hashlib.sha256(payload.encode()).hexdigest()[:16]
    lineage_id = f"AIL-{ts_str}-{hash16}"

    safe_label = label.replace(" ", "_").replace("/", "_")
    dir_path = _ARCHIVE_ROOT / date_dir
    dir_path.mkdir(parents=True, exist_ok=True)
    file_path = dir_path / f"{safe_label}_{ts_str}.json.gz"

    with gzip.open(file_path, "wb") as f:
        f.write(payload.encode())

    return lineage_id


def load_snapshot(file_path: str) -> dict:
    """Load a compressed snapshot from disk."""
    with gzip.open(file_path, "rb") as f:
        return json.loads(f.read())
