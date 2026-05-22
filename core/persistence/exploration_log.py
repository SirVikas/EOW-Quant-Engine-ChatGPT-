"""
FTD-EXPLORE-OBSERVABILITY — Persistent Exploration Event Log

Append-only JSONL that survives engine restarts, providing lifetime exploration
attribution so the LIO can distinguish "Rule 4 never fired" from "Rule 4 fired
before the last restart."

Schema per line (one JSON object):
  utc_ts   : int   — epoch seconds at grant time
  session  : str   — RL session label, e.g. "NY"
  context  : str   — full RL context key "REGIME|SESSION|STRATEGY"
  pipeline : str   — "PAPER_SPEED" | "PRIMARY_STRATEGY" | "UNKNOWN"
  q_value  : float — Q-value at grant time
  visits   : int   — n_visits at grant time
  rule     : str   — "RULE1_MIN_EXPLORE" | "RULE4_FLOOR_EXPLORE"
  decision : str   — always "ALLOW"

Guarantees:
  • append-only (never truncated by this module)
  • thread-safe (threading.Lock around every write AND read)
  • fail-open (all exceptions silently swallowed — never blocks execution)
  • bounded: prune() trims oldest lines when file exceeds MAX_LINES
"""
from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Dict, List

_DEFAULT_PATH = Path("data/exploration_events.jsonl")
MAX_LINES     = 50_000   # soft retention cap; oldest lines pruned at this bound


class ExplorationEventLog:

    MODULE = "EXPLORATION_EVENT_LOG"

    def __init__(self, path: Path = _DEFAULT_PATH):
        self._path = Path(path)
        self._lock = threading.Lock()
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass   # fail-open — if we can't create dir, every write will also fail silently

    # ── Public write API ──────────────────────────────────────────────────────

    def record(
        self,
        *,
        session:  str,
        context:  str,
        pipeline: str,
        q_value:  float,
        visits:   int,
        rule:     str,
    ) -> None:
        """Append one exploration event. Fail-open — never raises."""
        try:
            event = {
                "utc_ts":   int(time.time()),
                "session":  session,
                "context":  context,
                "pipeline": pipeline,
                "q_value":  round(float(q_value), 5),
                "visits":   int(visits),
                "rule":     rule,
                "decision": "ALLOW",
            }
            line = json.dumps(event) + "\n"
            with self._lock:
                with self._path.open("a", encoding="utf-8") as fh:
                    fh.write(line)
        except Exception:
            pass   # fail-open: never interrupt trading

    # ── Public read API ───────────────────────────────────────────────────────

    def read_all(self) -> List[Dict]:
        """
        Return all persisted exploration events as a list of dicts.
        Fail-open — returns [] on any I/O or parse error.
        Corrupted lines are silently skipped.
        """
        try:
            if not self._path.exists():
                return []
            events: List[Dict] = []
            with self._lock:
                with self._path.open("r", encoding="utf-8") as fh:
                    for line in fh:
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError:
                            pass
            return events
        except Exception:
            return []

    def lifetime_count(self) -> int:
        """Total exploration events ever recorded (across restarts)."""
        return len(self.read_all())

    def lifetime_count_by_rule(self) -> Dict[str, int]:
        """Per-rule lifetime counts: {"RULE1_MIN_EXPLORE": n, "RULE4_FLOOR_EXPLORE": n}."""
        counts: Dict[str, int] = {}
        for ev in self.read_all():
            rule = ev.get("rule", "UNKNOWN")
            counts[rule] = counts.get(rule, 0) + 1
        return counts

    def summary(self) -> Dict:
        """
        Compact summary for the LIO diagnostics endpoint.
        Returns lifetime counts, session breakdown, pipeline breakdown,
        context breakdown, and Q-band distribution.
        """
        events = self.read_all()
        if not events:
            return {
                "total_events": 0,
                "rule_breakdown": {},
                "session_breakdown": {},
                "pipeline_breakdown": {},
                "context_breakdown": [],
                "q_band_distribution": {},
            }

        rule_counts:     Dict[str, int] = {}
        session_counts:  Dict[str, int] = {}
        pipeline_counts: Dict[str, int] = {}
        context_counts:  Dict[str, int] = {}
        q_bands:         Dict[str, int] = {
            "(-0.15, -0.10)": 0,
            "(-0.10, -0.05)": 0,
            "(-0.05,  0.00)": 0,
            "zero_or_pos":    0,
            "other":          0,
        }

        for ev in events:
            rule_counts[ev.get("rule", "UNKNOWN")]    = rule_counts.get(ev.get("rule", "UNKNOWN"), 0) + 1
            sess = ev.get("session", "UNKNOWN")
            session_counts[sess]                       = session_counts.get(sess, 0) + 1
            pipe = ev.get("pipeline", "UNKNOWN")
            pipeline_counts[pipe]                      = pipeline_counts.get(pipe, 0) + 1
            ctx  = ev.get("context", "UNKNOWN")
            context_counts[ctx]                        = context_counts.get(ctx, 0) + 1

            q = ev.get("q_value", 0.0)
            if q >= 0:
                q_bands["zero_or_pos"]    += 1
            elif q > -0.05:
                q_bands["(-0.05,  0.00)"] += 1
            elif q > -0.10:
                q_bands["(-0.10, -0.05)"] += 1
            elif q > -0.15:
                q_bands["(-0.15, -0.10)"] += 1
            else:
                q_bands["other"]          += 1

        context_breakdown = sorted(
            [{"context": k, "count": v} for k, v in context_counts.items()],
            key=lambda x: -x["count"],
        )

        return {
            "total_events":        len(events),
            "rule_breakdown":      rule_counts,
            "session_breakdown":   session_counts,
            "pipeline_breakdown":  pipeline_counts,
            "context_breakdown":   context_breakdown[:20],
            "q_band_distribution": q_bands,
        }

    # ── Maintenance ───────────────────────────────────────────────────────────

    def prune(self, max_lines: int = MAX_LINES) -> int:
        """
        Trim the log to at most `max_lines` by discarding the oldest entries.
        Returns the number of lines removed.  Fail-open.
        """
        try:
            events = self.read_all()
            if len(events) <= max_lines:
                return 0
            keep = events[-max_lines:]
            with self._lock:
                with self._path.open("w", encoding="utf-8") as fh:
                    for ev in keep:
                        fh.write(json.dumps(ev) + "\n")
            return len(events) - max_lines
        except Exception:
            return 0


# ── Module-level singleton ────────────────────────────────────────────────────
# Shared by rl_engine.py (writer) and main.py LIO endpoint (reader).
exploration_event_log = ExplorationEventLog()
