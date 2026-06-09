"""
Signal certifier — master signal certification engine combining precision, recall, and decay.
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class SignalCert:
    cert_id: str
    signal_name: str
    precision_pct: float
    recall_pct: float
    f1_score: float
    decay_status: str
    certified: bool
    certified_at: str


class SignalCertifier:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._certs: List[SignalCert] = []
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"SCT-{self._counter:03d}"

    def certify(
        self,
        signal_name: str,
        precision_pct: float,
        recall_pct: float,
    ) -> SignalCert:
        from core.signal_certification.signal_decay_tracker import signal_decay_tracker

        # F1 = 2 * P * R / (P + R)
        if precision_pct + recall_pct > 0:
            f1 = round(2 * precision_pct * recall_pct / (precision_pct + recall_pct), 2)
        else:
            f1 = 0.0

        # Check decay status for this signal
        decay_records = [r for r in signal_decay_tracker._records if r.signal_name == signal_name]
        decay_status = decay_records[-1].status if decay_records else "UNKNOWN"

        certified = (
            precision_pct >= 60
            and recall_pct >= 50
            and f1 >= 54
            and decay_status not in ("DEPLETED",)
        )

        with self._lock:
            cert = SignalCert(
                cert_id=self._next_id(),
                signal_name=signal_name,
                precision_pct=precision_pct,
                recall_pct=recall_pct,
                f1_score=f1,
                decay_status=decay_status,
                certified=certified,
                certified_at=datetime.utcnow().isoformat(),
            )
            self._certs.append(cert)
            return cert

    def certified_signals(self) -> List[SignalCert]:
        with self._lock:
            return [c for c in self._certs if c.certified]

    def uncertified_signals(self) -> List[SignalCert]:
        with self._lock:
            return [c for c in self._certs if not c.certified]

    def certification_report(self) -> dict:
        with self._lock:
            return {
                "total_evaluated": len(self._certs),
                "certified": sum(1 for c in self._certs if c.certified),
                "uncertified": sum(1 for c in self._certs if not c.certified),
                "certification_rate_pct": round(
                    sum(1 for c in self._certs if c.certified) / len(self._certs) * 100, 2
                ) if self._certs else 0.0,
                "signals": [
                    {
                        "signal_name": c.signal_name,
                        "precision_pct": c.precision_pct,
                        "recall_pct": c.recall_pct,
                        "f1_score": c.f1_score,
                        "certified": c.certified,
                    }
                    for c in self._certs
                ],
            }


signal_certifier = SignalCertifier()
