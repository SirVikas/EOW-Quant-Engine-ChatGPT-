"""
Certification archive — immutable history of every certification issued
by the pipeline, queryable by period.
"""
import threading
from datetime import datetime
from typing import List


class CertificationArchive:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._records: List[dict] = []
        self._counter = 0

    def archive(self, record: dict) -> str:
        with self._lock:
            self._counter += 1
            archive_id = f"CPA-{self._counter:03d}"
            self._records.append({
                "archive_id": archive_id,
                "archived_at": datetime.utcnow().isoformat(),
                **record,
            })
            return archive_id

    def latest(self, period: str = None) -> dict:
        with self._lock:
            for record in reversed(self._records):
                if period is None or record.get("period") == period:
                    return record
            return {}

    def archive_summary(self) -> dict:
        with self._lock:
            records = list(self._records)
            by_verdict: dict = {}
            for r in records:
                verdict = r.get("verdict", "UNKNOWN")
                by_verdict[verdict] = by_verdict.get(verdict, 0) + 1
            return {
                "total": len(records),
                "by_verdict": by_verdict,
                "recent": records[-10:],
            }


certification_archive = CertificationArchive()
