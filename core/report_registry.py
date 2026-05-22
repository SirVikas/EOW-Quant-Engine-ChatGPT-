"""
FTD-RTAG: Canonical Report Registry.

Single source of truth for all PHOENIX LIO report descriptors.
Each report declares its family, tier, dependencies, overlapping reports,
constitutional scope, archive priority, and evidence requirements.

Pure data — no I/O, no side effects. Import-safe.

Hard rule: The registry MUST NOT be mutated at runtime.
           All reporting governance remains under human constitutional authority.
"""
from __future__ import annotations
from typing import Any, Dict

REGISTRY_VERSION = "1.0"

# ── Export tiers ──────────────────────────────────────────────────────────────
TIER_CORE        = "CORE"
TIER_RESEARCH    = "RESEARCH"
TIER_GOVERNANCE  = "GOVERNANCE"
TIER_EPISTEMIC   = "EPISTEMIC"
TIER_CONTINUITY  = "CONTINUITY"
TIER_FORENSICS   = "FORENSICS"

# ── Archive priorities ────────────────────────────────────────────────────────
PRIORITY_CRITICAL = "CRITICAL"
PRIORITY_HIGH     = "HIGH"
PRIORITY_MEDIUM   = "MEDIUM"
PRIORITY_LOW      = "LOW"

# ── Report families ───────────────────────────────────────────────────────────
FAMILY_ECONOMIC        = "ECONOMIC"
FAMILY_COGNITIVE       = "COGNITIVE"
FAMILY_GOVERNANCE      = "GOVERNANCE"
FAMILY_EPISTEMIC       = "EPISTEMIC"
FAMILY_CONTINUITY      = "CONTINUITY"
FAMILY_HUMAN_ALIGNMENT = "HUMAN_ALIGNMENT"
FAMILY_REPLAY          = "REPLAY"
FAMILY_FORENSICS       = "FORENSICS"

# ── Known sets ────────────────────────────────────────────────────────────────
KNOWN_FAMILIES: frozenset = frozenset({
    FAMILY_ECONOMIC, FAMILY_COGNITIVE, FAMILY_GOVERNANCE,
    FAMILY_EPISTEMIC, FAMILY_CONTINUITY, FAMILY_HUMAN_ALIGNMENT,
    FAMILY_REPLAY, FAMILY_FORENSICS,
})

KNOWN_TIERS: frozenset = frozenset({
    TIER_CORE, TIER_RESEARCH, TIER_GOVERNANCE,
    TIER_EPISTEMIC, TIER_CONTINUITY, TIER_FORENSICS,
})

KNOWN_PRIORITIES: frozenset = frozenset({
    PRIORITY_CRITICAL, PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW,
})

# Required fields for every registry entry.
REGISTRY_REQUIRED_FIELDS: tuple = (
    "report_id", "name", "report_family", "doctrine_version",
    "export_tier", "endpoint", "bundle_key", "dependencies",
    "overlapping_reports", "constitutional_scope", "archive_priority",
    "evidence_requirements", "description",
)

# ── Canonical report registry ─────────────────────────────────────────────────

REPORT_REGISTRY: Dict[str, Dict[str, Any]] = {

    "SUMMARY": {
        "report_id":           "SUMMARY",
        "name":                "Trading Summary",
        "report_family":       FAMILY_ECONOMIC,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_CORE,
        "endpoint":            "/api/learning-intelligence/summary",
        "bundle_key":          "summary",
        "dependencies":        [],
        "overlapping_reports": ["ECOLOGY", "RL_LEARNING"],
        "constitutional_scope": "ECONOMIC_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 0},
        "description": "Core economic performance summary — PnL, win rate, session stats",
    },

    "PATTERNS": {
        "report_id":           "PATTERNS",
        "name":                "Pattern Library",
        "report_family":       FAMILY_COGNITIVE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/patterns",
        "bundle_key":          "patterns",
        "dependencies":        ["SUMMARY"],
        "overlapping_reports": ["COGNITION"],
        "constitutional_scope": "COGNITIVE_OBSERVABILITY",
        "archive_priority":    PRIORITY_MEDIUM,
        "evidence_requirements": {"min_trades": 10},
        "description": "Learned strategy patterns and regime-specific pattern library",
    },

    "NEGATIVE_MEMORY": {
        "report_id":           "NEGATIVE_MEMORY",
        "name":                "Negative Memory Archive",
        "report_family":       FAMILY_COGNITIVE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/negative-memory",
        "bundle_key":          "negative_memory",
        "dependencies":        ["SUMMARY"],
        "overlapping_reports": ["MEMORY_PRESSURE"],
        "constitutional_scope": "COGNITIVE_OBSERVABILITY",
        "archive_priority":    PRIORITY_MEDIUM,
        "evidence_requirements": {"min_trades": 5},
        "description": "Aversion catalog — high-loss patterns and adverse regime memory",
    },

    "ECOLOGY": {
        "report_id":           "ECOLOGY",
        "name":                "Strategy Ecology",
        "report_family":       FAMILY_ECONOMIC,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_CORE,
        "endpoint":            "/api/learning-intelligence/ecology",
        "bundle_key":          "ecology",
        "dependencies":        ["SUMMARY"],
        "overlapping_reports": ["SUMMARY", "REGIME_CARTOGRAPHY"],
        "constitutional_scope": "ECONOMIC_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 10},
        "description": "Strategy ecosystem health — regime distribution, strategy population balance",
    },

    "RL_LEARNING": {
        "report_id":           "RL_LEARNING",
        "name":                "RL Learning Intelligence",
        "report_family":       FAMILY_ECONOMIC,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_CORE,
        "endpoint":            "/api/learning-intelligence/rl",
        "bundle_key":          "rl",
        "dependencies":        ["SUMMARY"],
        "overlapping_reports": ["COGNITION", "SUMMARY"],
        "constitutional_scope": "ECONOMIC_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 10},
        "description": "RL policy learning state — Q-values, reward shaping, policy evolution",
    },

    "TOPOLOGY": {
        "report_id":           "TOPOLOGY",
        "name":                "Strategy Topology",
        "report_family":       FAMILY_COGNITIVE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/topology",
        "bundle_key":          "topology",
        "dependencies":        ["PATTERNS", "ECOLOGY"],
        "overlapping_reports": ["PATTERNS"],
        "constitutional_scope": "COGNITIVE_OBSERVABILITY",
        "archive_priority":    PRIORITY_MEDIUM,
        "evidence_requirements": {"min_trades": 20},
        "description": "Strategy relationship topology — decision surface mapping",
    },

    "COGNITION": {
        "report_id":           "COGNITION",
        "name":                "Cognitive State",
        "report_family":       FAMILY_COGNITIVE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/cognition",
        "bundle_key":          "cognition",
        "dependencies":        ["RL_LEARNING", "PATTERNS"],
        "overlapping_reports": ["RL_LEARNING", "MEMORY_PRESSURE"],
        "constitutional_scope": "COGNITIVE_OBSERVABILITY",
        "archive_priority":    PRIORITY_MEDIUM,
        "evidence_requirements": {"min_trades": 10},
        "description": "Cognitive architecture state — ontology drift, belief updating, adaptation velocity",
    },

    "SOVEREIGN_READINESS": {
        "report_id":           "SOVEREIGN_READINESS",
        "name":                "Sovereign Readiness",
        "report_family":       FAMILY_GOVERNANCE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_GOVERNANCE,
        "endpoint":            "/api/learning-intelligence/sovereign-readiness",
        "bundle_key":          "sovereign_readiness",
        "dependencies":        ["SUMMARY", "COGNITION"],
        "overlapping_reports": ["GAGS"],
        "constitutional_scope": "GOVERNANCE_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 30},
        "description": "Governance readiness diagnostics — sovereignty gate assessment",
    },

    "ALPHA_DISCOVERY": {
        "report_id":           "ALPHA_DISCOVERY",
        "name":                "Alpha Discovery",
        "report_family":       FAMILY_ECONOMIC,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/alpha-discovery",
        "bundle_key":          "alpha_discovery",
        "dependencies":        ["SUMMARY", "ECOLOGY"],
        "overlapping_reports": ["ECONOMIC_GROUND_TRUTH"],
        "constitutional_scope": "ECONOMIC_OBSERVABILITY",
        "archive_priority":    PRIORITY_MEDIUM,
        "evidence_requirements": {"min_trades": 20},
        "description": "Alpha signal discovery — edge identification and regime-specific alpha",
    },

    "SESSION_ATTRIBUTION": {
        "report_id":           "SESSION_ATTRIBUTION",
        "name":                "Session Attribution",
        "report_family":       FAMILY_FORENSICS,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_FORENSICS,
        "endpoint":            "/api/learning-intelligence/session-attribution",
        "bundle_key":          "session_attribution",
        "dependencies":        ["SUMMARY"],
        "overlapping_reports": ["REGIME_CARTOGRAPHY"],
        "constitutional_scope": "FORENSICS_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 10},
        "description": "Session-level forensics — NY/LN/AS/EU attribution and performance breakdown",
    },

    "EXPLORATION_DIAGNOSTICS": {
        "report_id":           "EXPLORATION_DIAGNOSTICS",
        "name":                "Exploration Diagnostics",
        "report_family":       FAMILY_REPLAY,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/exploration-diagnostics",
        "bundle_key":          "exploration_diagnostics",
        "dependencies":        ["SUMMARY"],
        "overlapping_reports": ["EXPLORATION_ECONOMIC_ATTRIBUTION", "EIOD"],
        "constitutional_scope": "REPLAY_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 10},
        "description": "Exploration health — epsilon decay, trial diversity, exploration effectiveness",
    },

    "EXPLORATION_ECONOMIC_ATTRIBUTION": {
        "report_id":           "EXPLORATION_ECONOMIC_ATTRIBUTION",
        "name":                "Exploration Economic Attribution",
        "report_family":       FAMILY_REPLAY,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/exploration-economic-attribution",
        "bundle_key":          "exploration_economic_attribution",
        "dependencies":        ["EXPLORATION_DIAGNOSTICS", "ECONOMIC_GROUND_TRUTH"],
        "overlapping_reports": ["EXPLORATION_DIAGNOSTICS"],
        "constitutional_scope": "REPLAY_OBSERVABILITY",
        "archive_priority":    PRIORITY_MEDIUM,
        "evidence_requirements": {"min_trades": 20},
        "description": "Economic cost/benefit of exploration — PnL attribution to exploration vs exploitation",
    },

    "ECONOMIC_GROUND_TRUTH": {
        "report_id":           "ECONOMIC_GROUND_TRUTH",
        "name":                "Economic Ground Truth",
        "report_family":       FAMILY_ECONOMIC,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_CORE,
        "endpoint":            "/api/learning-intelligence/economic-ground-truth",
        "bundle_key":          "economic_ground_truth",
        "dependencies":        [],
        "overlapping_reports": ["SUMMARY", "TIMEFRAME_SURVIVABILITY"],
        "constitutional_scope": "ECONOMIC_OBSERVABILITY",
        "archive_priority":    PRIORITY_CRITICAL,
        "evidence_requirements": {"min_trades": 0},
        "description": "Ground truth economic performance — fees, slippage, net/gross PnL, Sharpe-family",
    },

    "TIMEFRAME_SURVIVABILITY": {
        "report_id":           "TIMEFRAME_SURVIVABILITY",
        "name":                "Timeframe Survivability",
        "report_family":       FAMILY_ECONOMIC,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/timeframe-survivability",
        "bundle_key":          "timeframe_survivability",
        "dependencies":        ["ECONOMIC_GROUND_TRUTH"],
        "overlapping_reports": ["REGIME_CARTOGRAPHY", "ECONOMIC_GROUND_TRUTH"],
        "constitutional_scope": "ECONOMIC_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 30},
        "description": "Survivability across holding periods — how strategy performance degrades over time",
    },

    "REGIME_CARTOGRAPHY": {
        "report_id":           "REGIME_CARTOGRAPHY",
        "name":                "Regime Survivability Cartography",
        "report_family":       FAMILY_ECONOMIC,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/regime-survivability-cartography",
        "bundle_key":          "regime_survivability_cartography",
        "dependencies":        ["TIMEFRAME_SURVIVABILITY", "SESSION_ATTRIBUTION"],
        "overlapping_reports": ["TIMEFRAME_SURVIVABILITY", "ECOLOGY"],
        "constitutional_scope": "ECONOMIC_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 50},
        "description": "Regime-indexed survivability map — performance across market regimes",
    },

    "MEMORY_PRESSURE": {
        "report_id":           "MEMORY_PRESSURE",
        "name":                "Memory Pressure Dynamics",
        "report_family":       FAMILY_COGNITIVE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/memory-pressure-dynamics",
        "bundle_key":          "memory_pressure_dynamics",
        "dependencies":        ["COGNITION", "NEGATIVE_MEMORY"],
        "overlapping_reports": ["COGNITION", "NEGATIVE_MEMORY"],
        "constitutional_scope": "COGNITIVE_OBSERVABILITY",
        "archive_priority":    PRIORITY_MEDIUM,
        "evidence_requirements": {"min_trades": 20},
        "description": "Memory buffer pressure — eviction dynamics, aversion memory saturation",
    },

    "COUNTERFACTUAL_LAB": {
        "report_id":           "COUNTERFACTUAL_LAB",
        "name":                "Counterfactual Interventions",
        "report_family":       FAMILY_REPLAY,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_RESEARCH,
        "endpoint":            "/api/learning-intelligence/counterfactual-interventions",
        "bundle_key":          "counterfactual_interventions",
        "dependencies":        ["REGIME_CARTOGRAPHY", "EXPLORATION_DIAGNOSTICS"],
        "overlapping_reports": ["REGIME_CARTOGRAPHY"],
        "constitutional_scope": "REPLAY_OBSERVABILITY",
        "archive_priority":    PRIORITY_MEDIUM,
        "evidence_requirements": {"min_trades": 50},
        "description": "Counterfactual analysis — what-if interventions on strategy parameters",
    },

    "GAGS": {
        "report_id":           "GAGS",
        "name":                "Adaptive Governance Simulator",
        "report_family":       FAMILY_GOVERNANCE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_GOVERNANCE,
        "endpoint":            "/api/learning-intelligence/adaptive-governance-simulator",
        "bundle_key":          "adaptive_governance_simulator",
        "dependencies":        ["SOVEREIGN_READINESS", "ECONOMIC_GROUND_TRUTH"],
        "overlapping_reports": ["GADD", "SOVEREIGN_READINESS"],
        "constitutional_scope": "GOVERNANCE_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 30},
        "description": "Governance parameter simulation — threshold sensitivity and adaptive governance scenarios",
    },

    "GADD": {
        "report_id":           "GADD",
        "name":                "Governed Adaptive Doctrine",
        "report_family":       FAMILY_GOVERNANCE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_GOVERNANCE,
        "endpoint":            "/api/learning-intelligence/governed-adaptive-doctrine",
        "bundle_key":          "governed_adaptive_doctrine",
        "dependencies":        ["GAGS"],
        "overlapping_reports": ["GAGS"],
        "constitutional_scope": "GOVERNANCE_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 30},
        "description": "Active governance doctrine — current adaptive doctrine state and constitutional compliance",
    },

    "GRVL": {
        "report_id":           "GRVL",
        "name":                "Reality Verification",
        "report_family":       FAMILY_GOVERNANCE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_GOVERNANCE,
        "endpoint":            "/api/learning-intelligence/reality-verification",
        "bundle_key":          "reality_verification",
        "dependencies":        ["ECONOMIC_GROUND_TRUTH"],
        "overlapping_reports": ["GADD"],
        "constitutional_scope": "GOVERNANCE_OBSERVABILITY",
        "archive_priority":    PRIORITY_CRITICAL,
        "evidence_requirements": {"min_trades": 0},
        "description": "Reality gate verification — alignment of engine assumptions with market ground truth",
    },

    "GMPD": {
        "report_id":           "GMPD",
        "name":                "Guarded Micro Pilot",
        "report_family":       FAMILY_GOVERNANCE,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_GOVERNANCE,
        "endpoint":            "/api/learning-intelligence/guarded-micro-pilot",
        "bundle_key":          "guarded_micro_pilot",
        "dependencies":        ["GRVL", "SOVEREIGN_READINESS"],
        "overlapping_reports": ["GRVL"],
        "constitutional_scope": "GOVERNANCE_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 50},
        "description": "Micro-pilot deployment governance — staged live readiness gating",
    },

    "LHEO": {
        "report_id":           "LHEO",
        "name":                "Long-Horizon Evolution",
        "report_family":       FAMILY_CONTINUITY,
        "doctrine_version":    "1.0",
        "export_tier":         TIER_CONTINUITY,
        "endpoint":            "/api/learning-intelligence/long-horizon-evolution",
        "bundle_key":          "long_horizon_evolution",
        "dependencies":        ["COGNITION", "EXPLORATION_DIAGNOSTICS"],
        "overlapping_reports": ["COGNITION", "EIOD"],
        "constitutional_scope": "CONTINUITY_OBSERVABILITY",
        "archive_priority":    PRIORITY_HIGH,
        "evidence_requirements": {"min_trades": 50},
        "description": "Long-horizon cognitive evolution — ontology drift, belief continuity, adaptation lineage",
    },

    "CKPD": {
        "report_id":           "CKPD",
        "name":                "Constitutional Recovery Observatory",
        "report_family":       FAMILY_CONTINUITY,
        "doctrine_version":    "1.21",
        "export_tier":         TIER_CONTINUITY,
        "endpoint":            "/api/learning-intelligence/constitutional-recovery-observatory",
        "bundle_key":          "constitutional_recovery_observatory",
        "dependencies":        [],
        "overlapping_reports": ["LHEO"],
        "constitutional_scope": "CONTINUITY_OBSERVABILITY",
        "archive_priority":    PRIORITY_CRITICAL,
        "evidence_requirements": {"min_trades": 10},
        "description": "FTD-CKPD: Knowledge preservation & catastrophic recovery readiness — 7 recovery metrics",
    },

    "EIOD": {
        "report_id":           "EIOD",
        "name":                "Epistemic Integrity Observatory",
        "report_family":       FAMILY_EPISTEMIC,
        "doctrine_version":    "1.22",
        "export_tier":         TIER_EPISTEMIC,
        "endpoint":            "/api/learning-intelligence/epistemic-integrity-observatory",
        "bundle_key":          "epistemic_integrity_observatory",
        "dependencies":        ["EXPLORATION_DIAGNOSTICS"],
        "overlapping_reports": ["LHEO"],
        "constitutional_scope": "EPISTEMIC_OBSERVABILITY",
        "archive_priority":    PRIORITY_CRITICAL,
        "evidence_requirements": {"min_trades": 10},
        "description": "FTD-EIOD: Scientific method governance — 8 epistemic metrics, 6 classifications",
    },

    "HMAO": {
        "report_id":           "HMAO",
        "name":                "Human Meaning Alignment Observatory",
        "report_family":       FAMILY_HUMAN_ALIGNMENT,
        "doctrine_version":    "1.23",
        "export_tier":         TIER_CONTINUITY,
        "endpoint":            "/api/learning-intelligence/human-meaning-alignment",
        "bundle_key":          "human_meaning_alignment",
        "dependencies":        ["EXPLORATION_DIAGNOSTICS", "EIOD"],
        "overlapping_reports": ["EIOD"],
        "constitutional_scope": "ALIGNMENT_OBSERVABILITY",
        "archive_priority":    PRIORITY_CRITICAL,
        "evidence_requirements": {"min_trades": 10},
        "description": "FTD-HMAO: Human purpose alignment governance — 8 alignment metrics, 6 classifications",
    },
}

# Total registered reports — must equal len(REPORT_REGISTRY)
EXPECTED_REPORT_COUNT = 25
