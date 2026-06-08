"""
PHOENIX CORTEX — Constitutional Governance Registry

A Constitution is not a list of rules.
A Constitution is a set of immutable principles that govern how rules are made.

The Constitutional Articles Registry is the highest authority in PHOENIX.
It defines what CORTEX is allowed to do, what it must never do, and
who has final authority over any governance decision.

Constitutional Articles
───────────────────────
  Each Article carries:
    - article_id       : immutable identifier (ARTICLE-001, etc.)
    - principle        : the governing principle (one sentence)
    - enforcement      : HARD_BLOCK | SOFT_BLOCK | ADVISORY | AUDIT_ONLY
    - override_authority : who can override (HUMAN_ONLY | NEVER | BOARD)
    - rationale        : why this principle exists

Enforcement levels:
  HARD_BLOCK    System cannot proceed without compliance. No override allowed.
  SOFT_BLOCK    System proceeds with warning. Human can approve within 5 min.
  ADVISORY      System logs the concern but does not block.
  AUDIT_ONLY    System records the event for audit review only.

The Registry also maintains a Constitutional Violation Log —
every time a module action violates an Article, the violation is recorded
with the module, the article, the action attempted, and the resolution.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ── Data Models ───────────────────────────────────────────────────────────────

@dataclass
class ConstitutionalArticle:
    article_id: str
    title: str
    principle: str
    enforcement: str          # HARD_BLOCK | SOFT_BLOCK | ADVISORY | AUDIT_ONLY
    override_authority: str   # HUMAN_ONLY | BOARD | NEVER
    rationale: str
    protected_modules: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    enacted_at: float = field(default_factory=time.time)


@dataclass
class ConstitutionalViolation:
    violation_id: str
    article_id: str
    violating_module: str
    action_attempted: str
    enforcement_applied: str
    resolved_by: str          # "system_blocked" | "human_approved" | "auto_denied"
    description: str
    timestamp: float = field(default_factory=time.time)
    approved: bool = False


# ── Registry ──────────────────────────────────────────────────────────────────

class ConstitutionRegistry:
    """
    The PHOENIX Constitutional Governance Registry.
    Immutable at runtime — Articles can only be added, never removed or modified.
    """

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._articles: Dict[str, ConstitutionalArticle] = {}
        self._violations: List[ConstitutionalViolation] = []
        self._enact_founding_articles()

    # ── Articles ──────────────────────────────────────────────────────────────

    def enact(self, article: ConstitutionalArticle) -> None:
        """Enact a new constitutional article. Existing articles are immutable."""
        with self._lock:
            if article.article_id in self._articles:
                raise ValueError(
                    f"Article {article.article_id} is already enacted. "
                    "Constitutional Articles are immutable."
                )
            self._articles[article.article_id] = article

    def get_article(self, article_id: str) -> Optional[ConstitutionalArticle]:
        with self._lock:
            return self._articles.get(article_id)

    def all_articles(self) -> List[ConstitutionalArticle]:
        with self._lock:
            return list(self._articles.values())

    def articles_for_module(self, module_key: str) -> List[ConstitutionalArticle]:
        """Return all articles that protect or apply to a specific module."""
        with self._lock:
            return [
                a for a in self._articles.values()
                if not a.protected_modules or module_key in a.protected_modules
            ]

    # ── Compliance Check ──────────────────────────────────────────────────────

    def check_action(
        self,
        module_key: str,
        action: str,
        action_type: str = "parameter_change",
    ) -> dict:
        """
        Check whether a proposed module action is constitutionally compliant.
        Returns compliance status and applicable articles.
        """
        applicable: List[ConstitutionalArticle] = []
        with self._lock:
            for art in self._articles.values():
                if art.protected_modules and module_key in art.protected_modules:
                    applicable.append(art)

        if not applicable:
            return {
                "compliant": True,
                "enforcement": "NONE",
                "applicable_articles": [],
                "message": "No constitutional constraints apply to this action.",
            }

        hardest = max(
            applicable,
            key=lambda a: {"HARD_BLOCK": 3, "SOFT_BLOCK": 2, "ADVISORY": 1, "AUDIT_ONLY": 0}
                          .get(a.enforcement, 0)
        )

        blocked = hardest.enforcement == "HARD_BLOCK"
        soft    = hardest.enforcement == "SOFT_BLOCK"

        return {
            "compliant":   not blocked and not soft,
            "hard_blocked": blocked,
            "soft_blocked": soft,
            "enforcement":  hardest.enforcement,
            "blocking_article": hardest.article_id,
            "override_authority": hardest.override_authority,
            "applicable_articles": [a.article_id for a in applicable],
            "message": (
                f"HARD BLOCK: {hardest.principle}" if blocked else
                f"SOFT BLOCK (human approval required): {hardest.principle}" if soft else
                f"ADVISORY: {hardest.principle}"
            ),
        }

    # ── Violation Recording ───────────────────────────────────────────────────

    def record_violation(
        self,
        article_id: str,
        violating_module: str,
        action_attempted: str,
        enforcement_applied: str,
        description: str,
        resolved_by: str = "system_blocked",
        approved: bool = False,
    ) -> ConstitutionalViolation:
        v = ConstitutionalViolation(
            violation_id=f"VIO_{article_id}_{int(time.time())}",
            article_id=article_id,
            violating_module=violating_module,
            action_attempted=action_attempted,
            enforcement_applied=enforcement_applied,
            resolved_by=resolved_by,
            description=description,
            approved=approved,
        )
        with self._lock:
            self._violations.append(v)
            if len(self._violations) > 1000:
                self._violations = self._violations[-1000:]
        # Record in IMRAF
        try:
            from core.observatory.nexus_bridge import _imraf
            im = _imraf()
            if im:
                im.record_incident(
                    title=f"[CONSTITUTION] Violation: {article_id} by {violating_module}",
                    description=description,
                    severity="high" if enforcement_applied == "HARD_BLOCK" else "medium",
                    component="constitution_registry",
                    resolution=f"Override authority: {v.violation_id}",
                    metadata={"article_id": article_id, "module": violating_module},
                )
        except Exception:
            pass
        return v

    def violation_log(self, limit: int = 50) -> List[dict]:
        with self._lock:
            items = list(reversed(self._violations))[:limit]
        return [
            {
                "violation_id":       v.violation_id,
                "article_id":         v.article_id,
                "violating_module":   v.violating_module,
                "action_attempted":   v.action_attempted,
                "enforcement_applied": v.enforcement_applied,
                "resolved_by":        v.resolved_by,
                "description":        v.description,
                "timestamp":          v.timestamp,
                "approved":           v.approved,
            }
            for v in items
        ]

    def summary(self) -> dict:
        with self._lock:
            total_arts = len(self._articles)
            total_viols = len(self._violations)
            by_enforcement: Dict[str, int] = {}
            for a in self._articles.values():
                by_enforcement[a.enforcement] = by_enforcement.get(a.enforcement, 0) + 1
        return {
            "total_articles":     total_arts,
            "total_violations":   total_viols,
            "by_enforcement":     by_enforcement,
            "articles":           [self._serialise_article(a) for a in self._articles.values()],
        }

    @staticmethod
    def _serialise_article(a: ConstitutionalArticle) -> dict:
        return {
            "article_id":          a.article_id,
            "title":               a.title,
            "principle":           a.principle,
            "enforcement":         a.enforcement,
            "override_authority":  a.override_authority,
            "rationale":           a.rationale,
            "protected_modules":   a.protected_modules,
            "examples":            a.examples,
            "enacted_at":          a.enacted_at,
        }

    # ── Founding Articles ─────────────────────────────────────────────────────
    # These are the immutable founding articles of the PHOENIX Constitution.

    def _enact_founding_articles(self) -> None:
        _FOUNDING: List[ConstitutionalArticle] = [
            ConstitutionalArticle(
                article_id="ARTICLE-001",
                title="Risk Supremacy",
                principle=(
                    "No signal module, learning module, or intelligence module may "
                    "override the Risk Engine or Risk Controller under any circumstance."
                ),
                enforcement="HARD_BLOCK",
                override_authority="NEVER",
                rationale=(
                    "Capital preservation is the first law of trading. "
                    "Risk modules exist precisely to prevent losses that other modules "
                    "might not detect. Overriding risk creates unlimited downside."
                ),
                protected_modules=["risk_engine", "risk_controller"],
                examples=[
                    "RL engine cannot increase position beyond risk engine limit",
                    "Genome evolution cannot reduce risk parameters below minimum",
                    "Auto-intelligence cannot disable risk engine gates",
                ],
            ),
            ConstitutionalArticle(
                article_id="ARTICLE-002",
                title="Evidence Before Change",
                principle=(
                    "No automated system may modify a trading parameter or module weight "
                    "without a completed InvestigationReport with confidence ≥ 0.6 "
                    "and a TruthRecord in EXPLAINED or VERIFIED state."
                ),
                enforcement="HARD_BLOCK",
                override_authority="HUMAN_ONLY",
                rationale=(
                    "Parameter changes based on insufficient evidence cause more harm "
                    "than the original problem. The cost of a bad change often exceeds "
                    "the cost of the original defect."
                ),
                examples=[
                    "CORTEX influence weight change requires evidence-backed investigation",
                    "Session blacklisting requires investigation with ≥60% confidence",
                    "Threshold changes require verified improvement data",
                ],
            ),
            ConstitutionalArticle(
                article_id="ARTICLE-003",
                title="Human Final Authority",
                principle=(
                    "All changes that affect live trading parameters, module weights, "
                    "or Constitutional Rules require explicit human approval. "
                    "Automated systems may recommend but never auto-apply."
                ),
                enforcement="HARD_BLOCK",
                override_authority="HUMAN_ONLY",
                rationale=(
                    "Automated systems optimize for measurable metrics and can create "
                    "dangerous fragility when they self-modify without human oversight. "
                    "Human judgment is the final safety layer."
                ),
                examples=[
                    "CORTEX cannot auto-apply influence weight changes",
                    "Observatory-X cannot auto-disable modules",
                    "AEG Sandbox recommendations require human approval",
                ],
            ),
            ConstitutionalArticle(
                article_id="ARTICLE-004",
                title="Drawdown Supremacy",
                principle=(
                    "When active drawdown exceeds the configured limit, "
                    "no module may approve new entries regardless of signal confidence."
                ),
                enforcement="HARD_BLOCK",
                override_authority="HUMAN_ONLY",
                rationale=(
                    "Drawdown is a compounding risk. Every additional loss during "
                    "a drawdown period increases recovery difficulty exponentially. "
                    "The Drawdown Controller must be the final gate."
                ),
                protected_modules=["drawdown_controller"],
                examples=[
                    "High-confidence signals cannot override drawdown halt",
                    "RL module cannot increase size when in drawdown",
                ],
            ),
            ConstitutionalArticle(
                article_id="ARTICLE-005",
                title="Safe Mode Supremacy",
                principle=(
                    "When Safe Mode Engine activates, all Tier-B modules are subordinated. "
                    "Only human intervention can deactivate Safe Mode."
                ),
                enforcement="HARD_BLOCK",
                override_authority="HUMAN_ONLY",
                rationale=(
                    "Safe Mode exists precisely because automated systems have failed. "
                    "Allowing automated systems to deactivate Safe Mode creates a "
                    "circular failure mode."
                ),
                protected_modules=["safe_mode_engine"],
            ),
            ConstitutionalArticle(
                article_id="ARTICLE-006",
                title="Trust Validation Required",
                principle=(
                    "Recommendations with trust score below 50 (MODERATE) "
                    "must not be presented as actionable without explicit LOW_TRUST label. "
                    "Recommendations with trust below 30 (LOW) require human review."
                ),
                enforcement="ADVISORY",
                override_authority="HUMAN_ONLY",
                rationale=(
                    "Untrusted recommendations are hypotheses, not evidence-based advice. "
                    "Labeling them clearly prevents premature application and "
                    "preserves the integrity of the evidence chain."
                ),
                examples=[
                    "New recommendation types start with LOW trust",
                    "Recommendations without outcome tracking are hypothesis-level",
                ],
            ),
            ConstitutionalArticle(
                article_id="ARTICLE-007",
                title="Institutional Memory Continuity",
                principle=(
                    "Every governance event — defect, investigation, recommendation, "
                    "blame attribution, and constitutional violation — must be recorded "
                    "in IMRAF within 60 seconds of occurrence."
                ),
                enforcement="SOFT_BLOCK",
                override_authority="BOARD",
                rationale=(
                    "Institutional memory is only as good as its completeness. "
                    "Events not recorded in IMRAF are effectively invisible to future "
                    "AEG reasoning and to human audit."
                ),
            ),
            ConstitutionalArticle(
                article_id="ARTICLE-008",
                title="Counterfactual Before Blame",
                principle=(
                    "A module shall not be declared the primary cause of a loss unless "
                    "a counterfactual analysis shows the loss would not have occurred "
                    "without that module's signal."
                ),
                enforcement="ADVISORY",
                override_authority="HUMAN_ONLY",
                rationale=(
                    "Correlation is not causation. Blaming a module without counterfactual "
                    "evidence leads to incorrect influence weight reductions and degrades "
                    "the module ecosystem over time."
                ),
            ),
        ]
        for article in _FOUNDING:
            self._articles[article.article_id] = article


# Singleton
constitution_registry = ConstitutionRegistry()
