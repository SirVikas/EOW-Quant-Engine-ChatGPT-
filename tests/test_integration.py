"""
FTD-026A — System Integration Tests
/tests/test_integration.py

Per spec:
  - Full system run test (all API endpoints return 200)
  - Export report test (ZIP contains .md + .pdf, all 15 sections)
  - No crash test (main imports cleanly, no circular imports)
  - No duplication test (each adapter delegates to ONE source)

Layer coverage:
  Layer 1  DATA         /api/lake, /api/trades
  Layer 2  INTELLIGENCE /api/thoughts, /api/last-skip, /api/signal-filter
  Layer 3  SUGGESTIONS  /api/suggestions, /api/ct-scan
  Layer 4  AUTO-TUNING  /api/auto-tuning
  Layer 6  ALERTS       /api/alert-state
  Layer 7  EVOLUTION    /api/evolution
  Layer 8  PORTFOLIO    /api/portfolio-state
  Layer 9  RISK         /api/risk-state, /api/risk-engine
  Layer 10 AUDIT        /api/audit-log, /api/errors
  Layer 11 AI BRAIN     /api/ai-brain, /api/regime
  Layer 12 CAPITAL      /api/capital-allocator
  Layer 13 EXPORT       /api/report/full-system
"""
from __future__ import annotations

import io
import json
import pathlib
import zipfile

import pytest
from fastapi.testclient import TestClient


# ── Fixture: shared test client ───────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    import main
    from core.orchestrator.execution_orchestrator import ExecutionOrchestrator
    ExecutionOrchestrator._reset_authority()
    c = TestClient(main.app)
    yield c
    ExecutionOrchestrator._reset_authority()


# ── 1. No-crash: imports and module init ──────────────────────────────────────

def test_main_imports_cleanly():
    """main.py must import without exceptions."""
    import main  # noqa: F401 — any ImportError will fail this test


def test_all_adapter_modules_import():
    """All FTD-026A adapter modules must be importable."""
    from core.intelligence.suggestion_engine import suggestion_engine
    from core.alerts.alert_engine            import alert_engine
    from core.evolution.evolution_engine     import evolution_engine
    from core.portfolio.allocation_engine    import allocation_engine
    from core.audit.audit_engine             import audit_engine
    from core.meta.ai_brain                  import ai_brain
    from core.capital.scaling_engine         import scaling_engine
    from core.tuning.tuner_controller        import tuner_controller

    assert suggestion_engine.PHASE == "015"
    assert alert_engine.PHASE      == "018"
    assert evolution_engine.PHASE  == "019"
    assert allocation_engine.PHASE == "020"
    assert audit_engine.PHASE      == "022"
    assert ai_brain.PHASE          == "023"
    assert scaling_engine.PHASE    == "024"
    assert tuner_controller.PHASE  == "016"


def test_function_registry_exists_and_has_entries():
    """FTD-014B: function_registry.json must exist with ≥ 50 entries."""
    reg_path = pathlib.Path("core/registry/function_registry.json")
    assert reg_path.exists(), "function_registry.json not found"
    data = json.loads(reg_path.read_text())
    # Registry may be a list or a dict with a 'functions' key
    if isinstance(data, list):
        entries = data
    else:
        entries = data.get("functions", [])
    assert len(entries) >= 50, f"Expected ≥ 50 entries, got {len(entries)}"
    first = entries[0]
    assert "function_name"  in first
    assert "owner_module"   in first


# ── 2. Full system run: all layer endpoints return 200 ───────────────────────

LAYER_ENDPOINTS = [
    # Layer 1 – DATA
    "/api/lake",
    "/api/trades",
    # Layer 2 – INTELLIGENCE
    "/api/thoughts",
    "/api/last-skip",
    "/api/signal-filter",
    # Layer 3 – SUGGESTIONS
    "/api/suggestions",
    "/api/ct-scan",
    # Layer 4 – AUTO-TUNING
    "/api/auto-tuning",
    # Layer 6 – ALERTS
    "/api/alert-state",
    # Layer 7 – EVOLUTION
    "/api/evolution",
    # Layer 8 – PORTFOLIO
    "/api/portfolio-state",
    # Layer 9 – RISK
    "/api/risk-state",
    "/api/risk-engine",
    # Layer 10 – AUDIT
    "/api/audit-log",
    "/api/errors",
    # Layer 11 – AI BRAIN
    "/api/ai-brain",
    "/api/regime",
    # Layer 12 – CAPITAL
    "/api/capital-allocator",
    # Layer 13 – EXPORT (smoke only — full test below)
    "/api/report/full-system",
]


@pytest.mark.parametrize("endpoint", LAYER_ENDPOINTS)
def test_all_layer_endpoints_return_200(client, endpoint):
    """Every layer endpoint must return HTTP 200."""
    r = client.get(endpoint)
    assert r.status_code == 200, (
        f"Endpoint {endpoint} returned {r.status_code}: {r.text[:200]}"
    )


@pytest.mark.parametrize("endpoint", LAYER_ENDPOINTS)
def test_all_layer_endpoints_return_json_or_zip(client, endpoint):
    """Every layer endpoint must return JSON or application/zip."""
    r = client.get(endpoint)
    ct = r.headers.get("content-type", "")
    assert "application/json" in ct or "application/zip" in ct, (
        f"Endpoint {endpoint} returned unexpected content-type: {ct}"
    )


# ── 3. Export report test ─────────────────────────────────────────────────────

def test_full_system_report_is_valid_zip(client):
    """FTD-025A: /api/report/full-system must return a valid ZIP."""
    r = client.get("/api/report/full-system")
    assert r.status_code == 200
    assert "application/zip" in r.headers.get("content-type", "")
    buf = io.BytesIO(r.content)
    assert zipfile.is_zipfile(buf), "Response is not a valid ZIP file"


def test_full_system_report_contains_md_and_pdf(client):
    """ZIP must contain exactly one .md and one .pdf file."""
    r = client.get("/api/report/full-system")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    names = zf.namelist()
    md_files  = [n for n in names if n.endswith(".md")]
    pdf_files = [n for n in names if n.endswith(".pdf")]
    assert len(md_files)  == 1, f"Expected 1 .md file, got {md_files}"
    assert len(pdf_files) == 1, f"Expected 1 .pdf file, got {pdf_files}"


def test_full_system_report_has_all_15_sections(client):
    """Markdown report must contain all 15 section headers."""
    r = client.get("/api/report/full-system")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    md_name = next(n for n in zf.namelist() if n.endswith(".md"))
    md = zf.read(md_name).decode("utf-8")
    for i in range(1, 16):
        assert f"## {i}." in md, f"Section {i} missing from full system report"


def test_full_system_report_pdf_is_non_empty(client):
    """PDF must be non-empty (at least 5 KB)."""
    r = client.get("/api/report/full-system")
    zf = zipfile.ZipFile(io.BytesIO(r.content))
    pdf_name = next(n for n in zf.namelist() if n.endswith(".pdf"))
    pdf_bytes = zf.read(pdf_name)
    assert len(pdf_bytes) >= 5_000, f"PDF too small: {len(pdf_bytes)} bytes"


# ── 4. No-duplication test ────────────────────────────────────────────────────

def test_suggestion_engine_delegates_to_ct_scan():
    """FTD-015: SuggestionEngine must use ct_scan_engine, not duplicate logic."""
    src = pathlib.Path("core/intelligence/suggestion_engine.py").read_text()
    assert "ct_scan_engine" in src, "suggestion_engine.py must delegate to ct_scan_engine"
    assert "def scan(" not in src,  "suggestion_engine.py must not duplicate scan logic"


def test_evolution_engine_delegates_to_genome():
    """FTD-019: EvolutionEngine must use genome_engine, not duplicate it."""
    src = pathlib.Path("core/evolution/evolution_engine.py").read_text()
    assert "GenomeEngine" in src or "genome" in src.lower()
    assert "def evolve(" not in src and "genetic" not in src.lower()


def test_audit_engine_delegates_to_error_registry():
    """FTD-022: AuditEngine must use error_registry, not duplicate it."""
    src = pathlib.Path("core/audit/audit_engine.py").read_text()
    assert "error_registry" in src


def test_tuner_controller_delegates_to_dynamic_thresholds():
    """FTD-016: TunerController must use dynamic_threshold_provider."""
    src = pathlib.Path("core/tuning/tuner_controller.py").read_text()
    assert "dynamic_threshold_provider" in src or "dynamic_thresholds" in src


def test_scaling_engine_delegates_to_capital_allocator():
    """FTD-024: ScalingEngine must use capital_allocator."""
    src = pathlib.Path("core/capital/scaling_engine.py").read_text()
    assert "capital_allocator" in src


# ── 5. Adapter summaries return correct module/phase labels ──────────────────

def test_adapter_summaries():
    from core.intelligence.suggestion_engine import suggestion_engine
    from core.alerts.alert_engine            import alert_engine
    from core.evolution.evolution_engine     import evolution_engine
    from core.audit.audit_engine             import audit_engine
    from core.meta.ai_brain                  import ai_brain
    from core.capital.scaling_engine         import scaling_engine
    from core.tuning.tuner_controller        import tuner_controller

    assert suggestion_engine.summary()["module"] == "SUGGESTION_ENGINE"
    assert alert_engine.summary()["module"]       == "ALERT_ENGINE"
    assert evolution_engine.summary()["module"]   == "EVOLUTION_ENGINE"
    assert audit_engine.summary()["module"]       == "AUDIT_ENGINE"
    assert ai_brain.summary()["module"]           == "AI_BRAIN"
    assert scaling_engine.summary()["module"]     == "SCALING_ENGINE"
    assert tuner_controller.summary()["module"]   == "TUNER_CONTROLLER"


# ── 6. Data flow: 014B → 025A pipeline ───────────────────────────────────────

def test_data_flow_pnl_feeds_suggestions(client):
    """PnL stats used in suggestions endpoint (Layer 1 → Layer 3)."""
    r = client.get("/api/suggestions")
    assert r.status_code == 200
    d = r.json()
    assert "findings" in d
    assert "health"   in d


def test_data_flow_risk_feeds_alerts(client):
    """Risk/gate state feeds alert engine (Layer 9 → Layer 6)."""
    r = client.get("/api/alert-state")
    assert r.status_code == 200
    d = r.json()
    assert "alerts"      in d
    assert "alert_count" in d


def test_data_flow_genome_feeds_evolution(client):
    """Genome state feeds evolution endpoint (genome → Layer 7)."""
    r = client.get("/api/evolution")
    assert r.status_code == 200
    d = r.json()
    assert "generation" in d
    assert "strategies" in d


def test_data_flow_capital_allocator_feeds_capital_endpoint(client):
    """capital_allocator.summary() feeds /api/capital-allocator (Layer 12)."""
    r = client.get("/api/capital-allocator")
    assert r.status_code == 200
    d = r.json()
    assert "module" in d
    assert d["module"] == "SCALING_ENGINE"


def test_data_flow_all_layers_feed_full_report(client):
    """Full system report aggregates all layers (014B → 025A pipeline)."""
    r = client.get("/api/report/full-system")
    assert r.status_code == 200
    zf  = zipfile.ZipFile(io.BytesIO(r.content))
    md  = zf.read(next(n for n in zf.namelist() if n.endswith(".md"))).decode()
    # Verify key sections appear for layers 1–13
    for section in [
        "Executive Summary",        # Layer 1
        "Performance",              # Layer 2
        "Signal Pipeline",          # Layer 3
        "Decision Trace",           # Layer 4
        "Risk State",               # Layer 9
        "Portfolio",                # Layer 8
        "AI Brain",                 # Layer 11
        "Suggestions",              # Layer 3
        "Auto-Tuning",              # Layer 4
        "Evolution",                # Layer 7
        "Capital",                  # Layer 12
        "Audit",                    # Layer 10
        "Alerts",                   # Layer 6
        "Final Diagnosis",          # Layer 14
        "Action Checklist",         # Layer 15
    ]:
        assert section in md, f"Section '{section}' missing from full report"
