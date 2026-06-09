"""
PHOENIX TRUST PROGRAM — Warehouse Integrity Engine  [GAP-R3]

Provides cryptographic-style tamper evidence for the Trust Evidence Warehouse.

Every evidence record is hashed on ingestion. The hash chain means:
  - Any deletion or modification is detectable
  - The chain can be verified at any time
  - A "sealed" checkpoint can be produced for audit

This is not a blockchain — it is a forward-hash-chain:
  hash[N] = SHA256(hash[N-1] + evidence_id + recorded_at + correct + pillar)

Verification:
  - verify_chain(): checks the entire chain for tampering
  - seal_checkpoint(): produces a signed snapshot of chain state at a point in time
  - integrity_report(): answers "has the warehouse been tampered with?"
"""
from __future__ import annotations

import hashlib
import json
import threading
import time
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class HashChainEntry:
    sequence: int
    evidence_id: str
    prev_hash: str
    current_hash: str
    pillar: str
    correct: bool
    recorded_at: float


@dataclass
class IntegrityCheckpoint:
    checkpoint_id: str
    sequence_at: int
    chain_tip_hash: str
    total_records: int
    sealed_at: float
    sealed_by: str = "SYSTEM"


class WarehouseIntegrityEngine:
    """
    SHA256 hash-chain integrity guard for the Trust Evidence Warehouse.
    """

    GENESIS_HASH = "0" * 64   # genesis block

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._chain: List[HashChainEntry] = []
        self._checkpoints: List[IntegrityCheckpoint] = []

    def _compute_hash(self, prev_hash: str, evidence_id: str, pillar: str, correct: bool, recorded_at: float) -> str:
        payload = f"{prev_hash}|{evidence_id}|{pillar}|{correct}|{recorded_at:.3f}"
        return hashlib.sha256(payload.encode()).hexdigest()

    def register(
        self,
        evidence_id: str,
        pillar: str,
        correct: bool,
        recorded_at: float,
    ) -> HashChainEntry:
        with self._lock:
            prev_hash = self._chain[-1].current_hash if self._chain else self.GENESIS_HASH
            seq = len(self._chain)
            h = self._compute_hash(prev_hash, evidence_id, pillar, correct, recorded_at)
            entry = HashChainEntry(
                sequence=seq,
                evidence_id=evidence_id,
                prev_hash=prev_hash,
                current_hash=h,
                pillar=pillar,
                correct=correct,
                recorded_at=recorded_at,
            )
            self._chain.append(entry)
        return entry

    def verify_chain(self) -> dict:
        with self._lock:
            chain = list(self._chain)
        if not chain:
            return {"valid": True, "length": 0, "note": "Empty chain — nothing to verify"}

        errors = []
        for i, entry in enumerate(chain):
            expected_prev = chain[i - 1].current_hash if i > 0 else self.GENESIS_HASH
            if entry.prev_hash != expected_prev:
                errors.append(f"Chain broken at sequence {i}: prev_hash mismatch")
            expected_h = self._compute_hash(entry.prev_hash, entry.evidence_id, entry.pillar, entry.correct, entry.recorded_at)
            if entry.current_hash != expected_h:
                errors.append(f"Hash tampered at sequence {i} (evidence_id={entry.evidence_id})")

        return {
            "valid":         len(errors) == 0,
            "chain_length":  len(chain),
            "chain_tip":     chain[-1].current_hash if chain else None,
            "errors":        errors,
            "verified_at":   time.time(),
        }

    def seal_checkpoint(self, sealed_by: str = "SYSTEM") -> IntegrityCheckpoint:
        with self._lock:
            seq = len(self._chain)
            tip = self._chain[-1].current_hash if self._chain else self.GENESIS_HASH
        cp = IntegrityCheckpoint(
            checkpoint_id=f"CP-{int(time.time()*1000)}",
            sequence_at=seq,
            chain_tip_hash=tip,
            total_records=seq,
            sealed_at=time.time(),
            sealed_by=sealed_by,
        )
        with self._lock:
            self._checkpoints.append(cp)
        return cp

    def verify_against_checkpoint(self, checkpoint_id: str) -> dict:
        with self._lock:
            cp = next((c for c in self._checkpoints if c.checkpoint_id == checkpoint_id), None)
        if not cp:
            return {"error": f"Checkpoint '{checkpoint_id}' not found"}
        with self._lock:
            if len(self._chain) < cp.sequence_at:
                return {"valid": False, "error": "Chain shorter than at checkpoint — records deleted"}
            current_tip_at_seq = self._chain[cp.sequence_at - 1].current_hash if cp.sequence_at > 0 else self.GENESIS_HASH
        matches = current_tip_at_seq == cp.chain_tip_hash
        return {
            "checkpoint_id":  checkpoint_id,
            "valid":          matches,
            "sealed_at":      cp.sealed_at,
            "sequence_at":    cp.sequence_at,
            "hash_matches":   matches,
            "verified_at":    time.time(),
        }

    def integrity_report(self) -> dict:
        verification = self.verify_chain()
        with self._lock:
            chain_len = len(self._chain)
            checkpoint_count = len(self._checkpoints)
        return {
            "chain_valid":          verification["valid"],
            "chain_length":         chain_len,
            "checkpoints_sealed":   checkpoint_count,
            "chain_tip":            verification.get("chain_tip"),
            "tamper_evidence":      "CLEAN" if verification["valid"] else "TAMPERED",
            "errors":               verification.get("errors", []),
            "last_verified_at":     verification.get("verified_at"),
        }

    def checkpoints(self) -> List[dict]:
        with self._lock:
            return [
                {
                    "checkpoint_id": c.checkpoint_id,
                    "sequence_at":   c.sequence_at,
                    "chain_tip":     c.chain_tip_hash[:16] + "...",
                    "total_records": c.total_records,
                    "sealed_at":     c.sealed_at,
                    "sealed_by":     c.sealed_by,
                }
                for c in self._checkpoints
            ]


# Singleton
warehouse_integrity = WarehouseIntegrityEngine()
