"""FTD-AIL-001: Archive Store — compressed raw report archive."""
from __future__ import annotations
import asyncio
from core.autonomous_intelligence.collector.snapshot_archiver import save_snapshot, load_snapshot


async def archive(label: str, data: dict) -> str:
    """Save snapshot asynchronously, return lineage_id."""
    return await asyncio.to_thread(save_snapshot, label, data)


async def load(file_path: str) -> dict:
    return await asyncio.to_thread(load_snapshot, file_path)
