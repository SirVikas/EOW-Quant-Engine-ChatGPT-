"""Resource Governor — manages CPU/RAM/API budget allocation per system layer."""
import threading
import time
from dataclasses import dataclass, asdict
from typing import Optional


@dataclass
class ResourceBudget:
    layer_id: str
    cpu_budget_pct: float
    ram_budget_mb: int
    api_calls_per_min: int
    scan_budget: int
    scheduler_priority: int
    current_cpu_usage: float
    current_ram_usage: float
    last_updated: float


_DEFAULT_BUDGETS = {
    "PCCP":           (20, 512),
    "CTAO":           (15, 256),
    "OBSERVATORY-X":  (15, 256),
    "NEXUS":          (10, 128),
    "CORTEX":         (10, 128),
    "AEG":            (10, 128),
    "PCAO":           (10, 128),
}


class ResourceGovernor:
    def __init__(self):
        self._lock = threading.RLock()
        self._budgets: dict[str, ResourceBudget] = {}
        for layer_id, (cpu, ram) in _DEFAULT_BUDGETS.items():
            self._budgets[layer_id] = ResourceBudget(
                layer_id=layer_id,
                cpu_budget_pct=cpu,
                ram_budget_mb=ram,
                api_calls_per_min=60,
                scan_budget=10,
                scheduler_priority=5,
                current_cpu_usage=0.0,
                current_ram_usage=0.0,
                last_updated=time.time(),
            )

    def set_budget(self, layer_id: str, cpu_budget_pct: float, ram_budget_mb: int,
                   api_calls_per_min: int = 60, scan_budget: int = 10,
                   scheduler_priority: int = 5):
        with self._lock:
            existing = self._budgets.get(layer_id)
            cpu_usage = existing.current_cpu_usage if existing else 0.0
            ram_usage = existing.current_ram_usage if existing else 0.0
            self._budgets[layer_id] = ResourceBudget(
                layer_id=layer_id,
                cpu_budget_pct=cpu_budget_pct,
                ram_budget_mb=ram_budget_mb,
                api_calls_per_min=api_calls_per_min,
                scan_budget=scan_budget,
                scheduler_priority=scheduler_priority,
                current_cpu_usage=cpu_usage,
                current_ram_usage=ram_usage,
                last_updated=time.time(),
            )

    def update_usage(self, layer_id: str, cpu_usage: float, ram_usage: float):
        with self._lock:
            if layer_id not in self._budgets:
                self.set_budget(layer_id, 10, 128)
            self._budgets[layer_id].current_cpu_usage = cpu_usage
            self._budgets[layer_id].current_ram_usage = ram_usage
            self._budgets[layer_id].last_updated = time.time()

    def get_budget(self, layer_id: str) -> Optional[dict]:
        with self._lock:
            b = self._budgets.get(layer_id)
            return asdict(b) if b else None

    def all_budgets(self) -> list:
        with self._lock:
            return [asdict(b) for b in self._budgets.values()]

    def resource_health(self) -> dict:
        with self._lock:
            budgets = list(self._budgets.values())
            total_cpu = sum(b.cpu_budget_pct for b in budgets)
            total_ram = sum(b.ram_budget_mb for b in budgets)
            over_budget = [b.layer_id for b in budgets if b.current_cpu_usage > b.cpu_budget_pct * 1.2]
            # Conflicts: layers sharing cpu budget exceeding 100%
            conflicts = []
            if total_cpu > 100:
                conflicts.append("Total CPU allocation exceeds 100%")
            return {
                "total_cpu_allocated": total_cpu,
                "total_ram_allocated_mb": total_ram,
                "over_budget_layers": over_budget,
                "resource_conflicts": conflicts,
            }

    def throttle_recommendation(self, layer_id: str) -> bool:
        with self._lock:
            b = self._budgets.get(layer_id)
            if not b:
                return False
            return b.current_cpu_usage > b.cpu_budget_pct


resource_governor = ResourceGovernor()
