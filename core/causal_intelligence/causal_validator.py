"""Causal validator — validates causal claims from intervention evidence."""
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Optional


@dataclass
class CausalClaim:
    claim_id: str
    cause: str
    effect: str
    evidence_for: list
    evidence_against: list
    strength: str
    confidence: float
    validated_at: str


class CausalValidator:
    def __init__(self):
        self._lock = threading.RLock()
        self._claims: list = []
        self._counter = 0

    def validate_claim(self, cause: str, effect: str) -> dict:
        from core.causal_intelligence.intervention_tracker import intervention_tracker
        interventions = intervention_tracker.interventions_for(cause)
        evidence_for = []
        evidence_against = []
        for i in interventions:
            if i["effect_candidate"] == effect:
                eff = i.get("effect_observed", {})
                confirmed = eff.get("confirmed", True)
                if confirmed:
                    evidence_for.append(i["intervention_id"])
                else:
                    evidence_against.append(i["intervention_id"])

        conf = len(evidence_for) / max(1, len(evidence_for) + len(evidence_against))
        if len(evidence_for) >= 5 and conf >= 0.8:
            strength = "STRONG"
        elif len(evidence_for) >= 3 and conf >= 0.6:
            strength = "MODERATE"
        elif len(evidence_for) >= 1:
            strength = "WEAK"
        else:
            strength = "UNPROVEN"

        with self._lock:
            self._counter += 1
            c = CausalClaim(
                claim_id=f"CLM-{self._counter:04d}",
                cause=cause,
                effect=effect,
                evidence_for=evidence_for,
                evidence_against=evidence_against,
                strength=strength,
                confidence=conf,
                validated_at=datetime.utcnow().isoformat(),
            )
            self._claims.append(c)
            return asdict(c)

    def all_claims(self, strength_filter: Optional[str] = None) -> list:
        with self._lock:
            if strength_filter:
                return [asdict(c) for c in self._claims if c.strength == strength_filter]
            return [asdict(c) for c in self._claims]

    def causal_map(self) -> dict:
        with self._lock:
            m: dict = {}
            for c in self._claims:
                m.setdefault(c.cause, {})[c.effect] = c.strength
            return m


causal_validator = CausalValidator()
