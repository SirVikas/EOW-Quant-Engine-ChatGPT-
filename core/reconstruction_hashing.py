"""
FTD-UEI: Reconstruction Hashing Infrastructure.

Deterministic hash functions for bundle integrity, lineage continuity,
archive corruption detection, and replay integrity validation.

Pure module — no I/O, no side effects. Import-safe.
"""
from __future__ import annotations

import hashlib
import hmac
import json
from typing import List


HASH_ALGORITHM = "sha256"


# ── Core hash primitives ──────────────────────────────────────────────────────

def content_hash(content: str) -> str:
    """SHA-256 of a UTF-8 string. Returns 64-char hex digest."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def dict_hash(d: dict) -> str:
    """
    Deterministic SHA-256 of a dict.
    Keys are sorted, values serialized with json.dumps(default=str)
    so the result is stable across Python runs.
    """
    canonical = json.dumps(d, sort_keys=True, default=str, ensure_ascii=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


# ── Domain-specific hash functions ────────────────────────────────────────────

def bundle_hash(bundle_type: str, report_ids: List[str], generation_ts: int) -> str:
    """
    Canonical reconstruction hash for a bundle.
    Deterministic: same inputs → same hash regardless of insertion order.
    """
    payload = f"{bundle_type}|{','.join(sorted(report_ids))}|{generation_ts}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def manifest_hash(manifest_body: dict) -> str:
    """Deterministic hash of a manifest body dict."""
    return dict_hash(manifest_body)


def lineage_hash(report_id: str, app_version: str, generation_ts: int) -> str:
    """Lineage fingerprint for a single report export event."""
    payload = f"{report_id}|{app_version}|{generation_ts}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def snapshot_hash(snapshot_type: str, app_version: str, generation_ts: int,
                  trade_count: int) -> str:
    """Reconstruction hash for a snapshot record."""
    payload = f"{snapshot_type}|{app_version}|{generation_ts}|{trade_count}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ── Validation ────────────────────────────────────────────────────────────────

def validate_hash(expected: str, actual: str) -> bool:
    """Constant-time comparison of two hex digests."""
    if not expected or not actual:
        return False
    return hmac.compare_digest(expected.lower(), actual.lower())


def is_valid_sha256(h: str) -> bool:
    """True if h looks like a well-formed 64-char hex SHA-256 digest."""
    if not isinstance(h, str) or len(h) != 64:
        return False
    return all(c in "0123456789abcdef" for c in h.lower())


# ── Bundle integrity verification ─────────────────────────────────────────────

def verify_bundle_hash(bundle: dict) -> dict:
    """
    Recompute the bundle reconstruction_hash from its stored metadata
    and compare to the stored value.

    Returns {"valid": bool, "stored_hash": str, "computed_hash": str, "reason": str}.
    """
    try:
        meta        = bundle.get("metadata", {})
        stored      = meta.get("reconstruction_hash", "")
        bundle_type = meta.get("bundle_type", "")
        report_ids  = bundle.get("report_ids", [])
        gen_ts      = meta.get("generation_ts", 0)

        if not stored:
            return {"valid": False, "stored_hash": "", "computed_hash": "",
                    "reason": "missing reconstruction_hash"}
        computed = bundle_hash(bundle_type, report_ids, int(gen_ts))
        ok = validate_hash(stored, computed)
        return {
            "valid":         ok,
            "stored_hash":   stored,
            "computed_hash": computed,
            "bundle_type":   bundle_type,
            "reason":        "ok" if ok else "hash_mismatch",
        }
    except Exception as exc:
        return {"valid": False, "stored_hash": "", "computed_hash": "",
                "reason": f"exception: {exc}"}


def verify_manifest_hash(manifest: dict) -> dict:
    """Recompute manifest_hash from manifest body and compare to stored value."""
    try:
        stored = manifest.get("manifest_hash", "")
        if not stored:
            return {"valid": False, "reason": "missing manifest_hash"}
        body = {
            k: v for k, v in manifest.items()
            if k not in ("manifest_id", "manifest_hash")
        }
        computed = dict_hash(body)
        ok = validate_hash(stored, computed)
        return {
            "valid":         ok,
            "stored_hash":   stored,
            "computed_hash": computed,
            "reason":        "ok" if ok else "manifest_hash_mismatch",
        }
    except Exception as exc:
        return {"valid": False, "reason": f"exception: {exc}"}
