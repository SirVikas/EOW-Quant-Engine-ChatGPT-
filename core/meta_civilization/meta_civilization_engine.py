"""Meta Civilization Engine — master meta-civilization."""
import threading


class MetaCivilizationEngine:
    def __init__(self):
        self._lock = threading.RLock()

    def meta_status(self) -> dict:
        from core.meta_civilization.supervisory_council import supervisory_council
        from core.meta_civilization.cross_civilization_alignment import cross_civilization_alignment
        from core.meta_civilization.universal_governance_framework import universal_governance_framework

        members = supervisory_council.council_members()
        matrix = cross_civilization_alignment.alignment_matrix()
        principles = universal_governance_framework.all_principles()

        # count distinct civilizations
        civs = len({m["civilization_id"] for m in members})

        # alignment summary
        avg_alignment = 0.0
        if matrix:
            avg_alignment = round(sum(a["alignment_score"] for a in matrix) / len(matrix), 1)

        if civs >= 3 and avg_alignment >= 70 and len(principles) >= 5:
            maturity = "ADVANCED"
        elif civs >= 2 or avg_alignment >= 50:
            maturity = "ESTABLISHED"
        else:
            maturity = "EMERGING"

        return {
            "council_size": len(members),
            "civilization_count": civs,
            "alignment_summary": {"avg_alignment_score": avg_alignment, "assessments": len(matrix)},
            "universal_principles_count": len(principles),
            "governance_maturity": maturity,
        }

    def one_liner(self) -> str:
        status = self.meta_status()
        return (f"MetaCiv: maturity={status['governance_maturity']} | "
                f"civs={status['civilization_count']} | "
                f"principles={status['universal_principles_count']}")


meta_civilization_engine = MetaCivilizationEngine()
