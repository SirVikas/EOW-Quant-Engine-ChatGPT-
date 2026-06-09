"""Long Horizon Director — manages long-horizon strategic directives (10Y+)."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional


@dataclass
class LongHorizonDirective:
    directive_id: str
    title: str
    horizon_years: int
    strategic_intent: str
    current_phase: str
    progress_pct: float  # 0-100


_COUNTER = [3]  # pre-seeded 3 directives


class LongHorizonDirector:
    def __init__(self):
        self._lock = threading.RLock()
        self._directives: List[LongHorizonDirective] = [
            LongHorizonDirective(
                directive_id="LHD-001",
                title="Achieve Full Institutional Autonomy",
                horizon_years=10,
                strategic_intent="Build a fully self-governing, self-healing trading institution",
                current_phase="Foundation",
                progress_pct=15.0,
            ),
            LongHorizonDirective(
                directive_id="LHD-002",
                title="Build Antifragile Capital Engine",
                horizon_years=7,
                strategic_intent="Create capital generation that strengthens under stress",
                current_phase="Architecture",
                progress_pct=25.0,
            ),
            LongHorizonDirective(
                directive_id="LHD-003",
                title="Establish Regulatory-Grade Transparency",
                horizon_years=5,
                strategic_intent="Achieve full audit trail and institutional-grade reporting",
                current_phase="Implementation",
                progress_pct=40.0,
            ),
        ]

    def create_directive(
        self,
        title: str,
        horizon_years: int,
        strategic_intent: str,
        current_phase: str = "Inception",
    ) -> dict:
        with self._lock:
            _COUNTER[0] += 1
            directive = LongHorizonDirective(
                directive_id=f"LHD-{_COUNTER[0]:03d}",
                title=title,
                horizon_years=horizon_years,
                strategic_intent=strategic_intent,
                current_phase=current_phase,
                progress_pct=0.0,
            )
            self._directives.append(directive)
            return asdict(directive)

    def update_progress(self, directive_id: str, pct: float) -> Optional[dict]:
        with self._lock:
            for d in self._directives:
                if d.directive_id == directive_id:
                    d.progress_pct = max(0.0, min(100.0, pct))
                    return asdict(d)
            return None

    def active_directives(self) -> List[dict]:
        with self._lock:
            return [asdict(d) for d in self._directives if d.progress_pct < 100.0]

    def horizon_outlook(self) -> dict:
        with self._lock:
            directives = self._directives
            avg_progress = sum(d.progress_pct for d in directives) / len(directives) if directives else 0
            near_term = [asdict(d) for d in directives if d.horizon_years <= 5]
            long_term = [asdict(d) for d in directives if d.horizon_years > 5]
            return {
                "total_directives": len(directives),
                "active_directives": len([d for d in directives if d.progress_pct < 100]),
                "average_progress_pct": round(avg_progress, 2),
                "near_term_directives": near_term,
                "long_term_directives": long_term,
            }


long_horizon_director = LongHorizonDirector()
