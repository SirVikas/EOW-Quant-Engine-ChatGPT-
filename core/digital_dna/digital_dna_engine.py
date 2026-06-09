"""Digital DNA Engine — comprehensive PHOENIX identity and doctrine integrity check."""
import threading
from datetime import datetime, timezone


class DigitalDNAEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def dna_profile(self) -> dict:
        with self._lock:
            from core.digital_dna.identity_registry import identity_registry
            from core.digital_dna.doctrine_registry import doctrine_registry
            from core.digital_dna.architectural_genome import architectural_genome

            identity_card = identity_registry.identity_card()
            doctrine_stats = doctrine_registry.doctrine_stats()
            genome_profile = architectural_genome.genome_profile()

            immutable_doctrines = [d for d in doctrine_registry.all_doctrines() if d["immutable"]]
            dna_integrity_score = 100 if len(immutable_doctrines) == doctrine_stats["immutable"] else 80

            return {
                "identity": identity_card,
                "core_doctrines": immutable_doctrines,
                "genome_summary": genome_profile,
                "dna_integrity_score": dna_integrity_score,
                "generated_at": datetime.now(timezone.utc).isoformat(),
            }

    def constitutional_dna_check(self, action: str) -> dict:
        with self._lock:
            from core.digital_dna.doctrine_registry import doctrine_registry

            const_verdict = {"allowed": True, "reason": "No constitutional engine available"}
            try:
                from core.constitution.constitution_engine import constitution_engine
                const_verdict = constitution_engine.check(action)
            except Exception:
                pass

            doctrine_conflicts = []
            for doctrine in doctrine_registry.all_doctrines():
                if doctrine["immutable"]:
                    # Simple keyword check: if action mentions ignoring a core principle
                    keywords = ["bypass", "ignore", "skip", "override", "disable"]
                    action_lower = action.lower()
                    for kw in keywords:
                        if kw in action_lower and any(
                            word in action_lower for word in ["capital", "truth", "audit", "governance"]
                        ):
                            doctrine_conflicts.append(doctrine["title"])
                            break

            allowed = const_verdict.get("allowed", True) and len(doctrine_conflicts) == 0
            return {
                "action": action,
                "constitutional_verdict": const_verdict,
                "doctrine_conflicts": doctrine_conflicts,
                "unified_verdict": "ALLOWED" if allowed else "BLOCKED",
                "checked_at": datetime.now(timezone.utc).isoformat(),
            }


digital_dna_engine = DigitalDNAEngine()
