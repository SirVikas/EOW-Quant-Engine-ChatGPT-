"""PCCP — Layer Registry: tracks all PHOENIX layers, their health, versions, dependencies."""
import threading
import time
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional


@dataclass
class LayerRecord:
    layer_id: str
    name: str
    version: str
    owner: str
    status: str = "UNKNOWN"
    dependencies: List[str] = field(default_factory=list)
    last_health_check: float = 0.0
    health_detail: str = ""


class LayerRegistry:
    def __init__(self):
        self._lock = threading.RLock()
        self._layers: Dict[str, LayerRecord] = {}
        self._auto_register_phoenix_layers()

    def register(self, layer_id: str, name: str, version: str, owner: str, dependencies: List[str] = None):
        with self._lock:
            rec = LayerRecord(
                layer_id=layer_id,
                name=name,
                version=version,
                owner=owner,
                dependencies=dependencies or [],
                last_health_check=time.time(),
            )
            self._layers[layer_id] = rec
            return asdict(rec)

    def update_health(self, layer_id: str, status: str, detail: str = ""):
        with self._lock:
            if layer_id not in self._layers:
                return {"error": f"Layer {layer_id} not found"}
            self._layers[layer_id].status = status
            self._layers[layer_id].health_detail = detail
            self._layers[layer_id].last_health_check = time.time()
            return {"updated": layer_id, "status": status}

    def get_layer(self, layer_id: str) -> Optional[dict]:
        with self._lock:
            rec = self._layers.get(layer_id)
            return asdict(rec) if rec else None

    def all_layers(self) -> List[dict]:
        with self._lock:
            return [asdict(r) for r in self._layers.values()]

    def system_health_summary(self) -> dict:
        with self._lock:
            layers = list(self._layers.values())
            total = len(layers)
            counts = {"HEALTHY": 0, "WARNING": 0, "DEGRADED": 0, "CRITICAL": 0, "UNKNOWN": 0}
            for l in layers:
                counts[l.status] = counts.get(l.status, 0) + 1
            if counts["CRITICAL"] > 0:
                overall = "CRITICAL"
            elif counts["DEGRADED"] > 0:
                overall = "DEGRADED"
            elif counts["WARNING"] > 0:
                overall = "WARNING"
            else:
                overall = "HEALTHY"
            return {
                "total": total,
                "healthy": counts["HEALTHY"],
                "warning": counts["WARNING"],
                "degraded": counts["DEGRADED"],
                "critical": counts["CRITICAL"],
                "overall_status": overall,
                "layers": [asdict(l) for l in layers],
            }

    def _auto_register_phoenix_layers(self):
        known = [
            ("NEXUS",         "PHOENIX NEXUS",           "3.2.0", "NEXUS",         []),
            ("OBSERVATORY-X", "Observatory-X",           "1.5.0", "OBSX",          ["NEXUS"]),
            ("CORTEX",        "CORTEX Governance",       "1.5.0", "CORTEX",        ["NEXUS"]),
            ("PTP",           "PHOENIX TRUST PROGRAM",   "1.6.0", "NEXUS",         ["OBSERVATORY-X", "CORTEX"]),
            ("AEG",           "AEG Pipeline",            "1.3.0", "AEG",           ["NEXUS", "OBSERVATORY-X"]),
            ("PCAO",          "PCAO",                    "0.5.0", "PCAO",          ["AEG"]),
            ("DIGITAL_TWIN",  "Digital Twin",            "1.0.0", "SYSTEM",        []),
            ("TRUST_ENGINE",  "Truth/Trust Engine",      "1.0.0", "SYSTEM",        ["PTP"]),
            ("RISK_ENGINE",   "Risk Engine",             "1.0.0", "SYSTEM",        []),
            ("REPORTING",     "Reporting Layer",         "1.0.0", "SYSTEM",        ["NEXUS"]),
        ]
        for layer_id, name, version, owner, deps in known:
            self.register(layer_id, name, version, owner, deps)


layer_registry = LayerRegistry()
