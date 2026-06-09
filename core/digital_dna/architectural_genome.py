"""Architectural Genome — DNA-level architectural principles and patterns."""
import threading
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from typing import List, Optional

SEED_GENES = [
    ("PRINCIPLE", "Separation of Concerns", True),
    ("PRINCIPLE", "Single Source of Truth", True),
    ("PRINCIPLE", "Lazy Integration", True),
    ("PATTERN", "Singleton with RLock", True),
    ("PATTERN", "Lazy Import", True),
    ("PATTERN", "Evidence-First Decision", True),
    ("CONSTRAINT", "No Direct Layer Communication", True),
    ("CONSTRAINT", "Constitution Before Action", True),
    ("CONSTRAINT", "Human Approval for Critical Evolutions", True),
    ("CAPABILITY", "Institutional Memory", True),
    ("CAPABILITY", "Causal Reasoning", True),
    ("CAPABILITY", "Autonomous Improvement", True),
    ("INTERFACE", "REST API First", True),
    ("INTERFACE", "JSON Data Exchange", True),
    ("INTERFACE", "Event Bus Communication", True),
]


@dataclass
class Gene:
    gene_id: str
    gene_type: str  # PRINCIPLE/PATTERN/CONSTRAINT/CAPABILITY/INTERFACE
    expression: str
    dominant: bool
    created_at: str


class ArchitecturalGenome:
    def __init__(self):
        self._lock = threading.RLock()
        self._genes: List[Gene] = []
        now = datetime.now(timezone.utc).isoformat()
        for i, (gene_type, expression, dominant) in enumerate(SEED_GENES, 1):
            gene = Gene(
                gene_id=f"GEN-{i:03d}",
                gene_type=gene_type,
                expression=expression,
                dominant=dominant,
                created_at=now,
            )
            self._genes.append(gene)

    def express(self, gene_type: Optional[str] = None) -> List[dict]:
        with self._lock:
            genes = self._genes
            if gene_type:
                genes = [g for g in genes if g.gene_type == gene_type]
            return [asdict(g) for g in genes]

    def genome_profile(self) -> dict:
        with self._lock:
            from config import APP_VERSION
            by_type: dict[str, int] = {}
            dominant = 0
            for g in self._genes:
                by_type[g.gene_type] = by_type.get(g.gene_type, 0) + 1
                if g.dominant:
                    dominant += 1
            return {
                "total_genes": len(self._genes),
                "by_type": by_type,
                "dominant_count": dominant,
                "genome_version": APP_VERSION,
            }


architectural_genome = ArchitecturalGenome()
