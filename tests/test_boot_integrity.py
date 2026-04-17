"""Boot integrity checks for FTD-REF-052-A remediation."""

from core.bootstrap.api_loader import ApiLoader
from core.strategy_engine import StrategyEngine
from core.ws_stabilizer import WsStabilizer
from main import _resolve_boot_deployability


class _MockMdp:
    async def reconnect(self):
        return None


def test_indicators_pending_forces_not_ready_and_low_score():
    score, status = _resolve_boot_deployability(
        network_score=30,
        database_score=30,
        rr_edge_score=40,
        indicators_state="PENDING_RUNTIME_VALIDATION",
    )
    assert status == "NOT_READY"
    assert score < 50


def test_rr_edge_zero_forces_zero_deployability():
    score, status = _resolve_boot_deployability(
        network_score=30,
        database_score=30,
        rr_edge_score=0,
        indicators_state="VALIDATED",
    )
    assert status == "NOT_READY"
    assert score == 0


def test_warming_up_with_healthy_infra_gets_improving_floor():
    score, status = _resolve_boot_deployability(
        network_score=30,
        database_score=15,
        rr_edge_score=0,
        indicators_state="WARMING_UP",
    )
    assert status == "IMPROVING"
    assert score >= 60


def test_websocket_instability_applies_network_penalty():
    stab = WsStabilizer(_MockMdp())
    stab._stats.reconnect_count = 3
    assert stab.summary()["network_penalty"] == 10


def test_data_insufficient_returns_hard_block_reason():
    assert StrategyEngine.evaluate_data_sufficiency(12, required_min=50) == "NO_TRADE_DATA_INSUFFICIENT"


def test_boot_loader_summary_syncs_with_api_status_values():
    loader = ApiLoader()
    loader.set_runtime_status(websocket="STABLE", indicators="VALIDATED")
    loader.set_deployability(score=37, status="NOT_READY")
    payload = loader.summary()

    assert payload["websocket"] == "STABLE"
    assert payload["indicators"] == "VALIDATED"
    assert payload["deployability"] == "NOT_READY"
    assert payload["deployability_score"] == 37
