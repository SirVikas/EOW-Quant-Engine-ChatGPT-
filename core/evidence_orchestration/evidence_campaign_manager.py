"""
Evidence campaign manager — tracks targeted evidence accumulation campaigns
(e.g. "collect 500 validation evidence items for ETE Phase-2 calibration").
"""
import threading
from dataclasses import dataclass
from datetime import datetime
from typing import Dict


@dataclass
class EvidenceCampaign:
    campaign_id: str
    name: str
    evidence_type: str
    target_count: int
    collected_count: int
    status: str        # OPEN / COMPLETE
    opened_at: str
    completed_at: str


class EvidenceCampaignManager:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._campaigns: Dict[str, EvidenceCampaign] = {}
        self._counter = 0

    def _next_id(self) -> str:
        self._counter += 1
        return f"EOC-{self._counter:03d}"

    def open_campaign(self, name: str, evidence_type: str = "VALIDATION",
                      target_count: int = 100) -> EvidenceCampaign:
        with self._lock:
            campaign = EvidenceCampaign(
                campaign_id=self._next_id(),
                name=name,
                evidence_type=evidence_type,
                target_count=max(1, target_count),
                collected_count=0,
                status="OPEN",
                opened_at=datetime.utcnow().isoformat(),
                completed_at="",
            )
            self._campaigns[campaign.campaign_id] = campaign
            return campaign

    def record_progress(self, campaign_id: str, collected: int = 1) -> dict:
        with self._lock:
            campaign = self._campaigns.get(campaign_id)
            if not campaign:
                return {"error": f"unknown campaign {campaign_id}"}
            if campaign.status == "OPEN":
                campaign.collected_count += max(0, collected)
                if campaign.collected_count >= campaign.target_count:
                    campaign.status = "COMPLETE"
                    campaign.completed_at = datetime.utcnow().isoformat()
            return vars(campaign)

    def sync_from_warehouse(self) -> int:
        """Refresh OPEN campaign counters from current warehouse totals."""
        try:
            from core.evidence_warehouse.evidence_registry import evidence_registry
            by_type = evidence_registry.registry_stats().get("by_type", {})
        except Exception:
            return 0
        updated = 0
        with self._lock:
            for campaign in self._campaigns.values():
                if campaign.status != "OPEN":
                    continue
                total = by_type.get(campaign.evidence_type, 0)
                if total > campaign.collected_count:
                    campaign.collected_count = total
                    updated += 1
                if campaign.collected_count >= campaign.target_count:
                    campaign.status = "COMPLETE"
                    campaign.completed_at = datetime.utcnow().isoformat()
        return updated

    def campaign_summary(self) -> dict:
        with self._lock:
            campaigns = list(self._campaigns.values())
            return {
                "total": len(campaigns),
                "open": sum(1 for c in campaigns if c.status == "OPEN"),
                "complete": sum(1 for c in campaigns if c.status == "COMPLETE"),
                "campaigns": [vars(c) for c in campaigns],
            }


evidence_campaign_manager = EvidenceCampaignManager()
