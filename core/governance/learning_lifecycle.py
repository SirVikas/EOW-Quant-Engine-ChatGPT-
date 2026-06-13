"""
Learning Lifecycle Governance — FTD-094A round-2 (GAP-H1 + GAP-D1/D2/D3)

The connective tissue the audit flagged as missing: a single formal ladder every
learning advisor (XTE, ETE, Truth, future AMIL) must climb, with explicit
criteria per stage, campaign/completion tracking, and a promotion framework.

    OBSERVE → VALIDATE → APPROVE → ADVISE → GATE → AUTHORITY

It GOVERNS but never ACTS. Advancement through the NON-acting stages
(OBSERVE→VALIDATE→APPROVE) is automatic on evidence criteria. Advancement into
the ACTING stages (ADVISE / GATE / AUTHORITY) is NEVER automatic — it requires an
explicit recorded human approval. The framework reports eligibility; it never
wires an advisor into the live decision path itself. That step remains a
deliberate, ADR-gated human action.

Safety: read-only over advisor evidence (e.g. XTE archive + verdict). No
execution influence. State persists to reports/governance/learning_lifecycle.json.
"""
from __future__ import annotations

import json
import os
import threading
import time
from typing import Any, Dict, List, Optional

from loguru import logger

STAGES = ["OBSERVE", "VALIDATE", "APPROVE", "ADVISE", "GATE", "AUTHORITY"]
ACTING_STAGES = {"ADVISE", "GATE", "AUTHORITY"}   # require human approval
_STATE_PATH = "reports/governance/learning_lifecycle.json"


class LearningLifecycle:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._advisors: Dict[str, dict] = {}
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────
    def _load(self) -> None:
        try:
            if os.path.exists(_STATE_PATH):
                with open(_STATE_PATH, "r", encoding="utf-8") as fh:
                    self._advisors = json.load(fh)
        except Exception as e:
            logger.warning(f"[LIFECYCLE] load failed: {e}")
            self._advisors = {}

    def _save(self) -> None:
        try:
            d = os.path.dirname(_STATE_PATH)
            if d:
                os.makedirs(d, exist_ok=True)
            with open(_STATE_PATH, "w", encoding="utf-8") as fh:
                json.dump(self._advisors, fh, indent=2)
        except Exception as e:
            logger.warning(f"[LIFECYCLE] save failed: {e}")

    # ── Registration ──────────────────────────────────────────────────────────
    def register(self, name: str, sample_target: int = 500, source: str = "") -> dict:
        with self._lock:
            if name not in self._advisors:
                self._advisors[name] = {
                    "stage": "OBSERVE",
                    "sample_target": sample_target,
                    "source": source,
                    "approvals": [],
                    "manual_samples": 0,
                    "manual_verdict": None,
                    "campaign_complete": False,
                    "campaign_complete_ts": None,
                    "created_ts": int(time.time() * 1000),
                }
                self._save()
            return self._advisors[name]

    # ── Live metrics (read-only) ────────────────────────────────────────────────
    def _metrics(self, name: str) -> dict:
        if name == "XTE":
            try:
                from core.truth.xte_observer import xte_observer
                from core.truth import xte_validation as xv
                samples = xte_observer.summary().get("archive_samples", 0)
                return {"samples": samples, "verdict_status": xv.verdict().get("status")}
            except Exception:
                pass
        a = self._advisors.get(name, {})
        return {"samples": a.get("manual_samples", 0), "verdict_status": a.get("manual_verdict")}

    def record_metrics(self, name: str, samples: Optional[int] = None,
                       verdict_status: Optional[str] = None) -> None:
        # For advisors that do not self-report (non-XTE). XTE pulls live.
        with self._lock:
            a = self._advisors.setdefault(name, {})
            if samples is not None:
                a["manual_samples"] = samples
            if verdict_status is not None:
                a["manual_verdict"] = verdict_status
            self._save()

    # ── Criteria ────────────────────────────────────────────────────────────────
    def _criteria(self, nxt: str, a: dict, m: dict) -> tuple:
        if nxt == "VALIDATE":
            ok = m["samples"] >= a["sample_target"]
            return ok, f"samples {m['samples']}/{a['sample_target']}", False
        if nxt == "APPROVE":
            ok = m["verdict_status"] == "CANDIDATE"
            return ok, f"verdict={m['verdict_status']} (need CANDIDATE)", False
        # ACTING stages — explicit human approval only
        approved = any(ap.get("to_stage") == nxt for ap in a.get("approvals", []))
        return approved, ("approved" if approved else f"requires human approval to enter {nxt}"), True

    def eligibility(self, name: str) -> dict:
        a = self._advisors[name]
        cur = a["stage"]
        idx = STAGES.index(cur)
        m = self._metrics(name)
        if idx >= len(STAGES) - 1:
            return {"current_stage": cur, "next_stage": None, "criteria_met": False,
                    "reason": "at top of ladder", "requires_approval": False, "metrics": m}
        nxt = STAGES[idx + 1]
        met, reason, requires_approval = self._criteria(nxt, a, m)
        return {"current_stage": cur, "next_stage": nxt, "criteria_met": met,
                "reason": reason, "requires_approval": requires_approval, "metrics": m}

    # ── Advancement ──────────────────────────────────────────────────────────────
    def advance(self, name: str) -> List[str]:
        """Auto-advance through NON-acting gates only (OBSERVE→VALIDATE→APPROVE).
        Never auto-enters an acting stage."""
        changed: List[str] = []
        with self._lock:
            while True:
                e = self.eligibility(name)
                nxt = e["next_stage"]
                if nxt is None or e["requires_approval"] or not e["criteria_met"]:
                    break
                self._advisors[name]["stage"] = nxt
                changed.append(nxt)
            if changed:
                self._save()
                logger.info(f"[LIFECYCLE] {name} auto-advanced → {changed[-1]}")
        return changed

    def approve(self, name: str, to_stage: str, approver: str, note: str = "") -> dict:
        """Record an explicit human approval to enter an ACTING stage. The advisor
        only moves if it is the adjacent next stage AND non-approval criteria allow."""
        if to_stage not in STAGES:
            raise ValueError(f"unknown stage {to_stage}")
        with self._lock:
            a = self._advisors[name]
            a.setdefault("approvals", []).append({
                "to_stage": to_stage, "approver": approver, "note": note,
                "ts": int(time.time() * 1000),
            })
            self._save()
            e = self.eligibility(name)
            if e["next_stage"] == to_stage and e["criteria_met"]:
                a["stage"] = to_stage
                self._save()
                logger.info(f"[LIFECYCLE] {name} promoted → {to_stage} (approver={approver})")
            return {"stage": a["stage"], "eligibility": self.eligibility(name)}

    # ── Campaign (D1) + completion trigger (D2) ─────────────────────────────────
    def campaign_status(self, name: str) -> dict:
        with self._lock:
            a = self._advisors[name]
            m = self._metrics(name)
            samples, target = m["samples"], a["sample_target"]
            complete = samples >= target
            if complete and not a.get("campaign_complete"):
                a["campaign_complete"] = True
                a["campaign_complete_ts"] = int(time.time() * 1000)
                self._save()
                logger.info(f"[LIFECYCLE] {name} CAMPAIGN COMPLETE {samples}/{target} "
                            f"— validation review triggered")
            return {
                "samples": samples, "target": target,
                "progress_pct": round(min(100.0, samples / target * 100), 1) if target else 0.0,
                "complete": complete,
                "completion_ts": a.get("campaign_complete_ts"),
            }

    # ── Reporting ────────────────────────────────────────────────────────────────
    def summary(self) -> dict:
        with self._lock:
            out = {}
            for name in self._advisors:
                self.advance(name)  # keep non-acting stages current
                out[name] = {
                    "stage": self._advisors[name]["stage"],
                    "eligibility": self.eligibility(name),
                    "campaign": self.campaign_status(name),
                    "approvals": self._advisors[name].get("approvals", []),
                }
            return {"stages": STAGES, "acting_stages": sorted(ACTING_STAGES), "advisors": out}

    def reset(self) -> None:
        with self._lock:
            self._advisors = {}


# Module-level singleton + default advisor registration
learning_lifecycle = LearningLifecycle()
learning_lifecycle.register("XTE", sample_target=500, source="core/truth/xte_observer.py")
