"""
EOW Quant Engine — core/profit
Phase 7A: Gate-Aware Profit Engine

All profit-maximization logic lives here. Every module is gated behind
GlobalGateController — no profit operation runs without explicit gate approval.

Boot flow:
    GateAwareController.allow_profit_engine(gate_status)  ← master check
    ScanController.can_scan(gate_status)                  ← signal gate
    GateAwareTradeRanker.rank(gate_status, ...)           ← ranking
    GateAwareCompetitionEngine.select(gate_status, ...)   ← selection
    GateAwareCapitalConcentrator.concentrate(gate_status, ...) ← sizing
    GateAwareEdgeAmplifier.evaluate(gate_status, ...)     ← amplification

Public API:
    from core.profit import (
        gate_aware_controller,
        scan_controller,
        trade_ranker,
        trade_competition_engine,
        capital_concentrator,
        edge_amplifier,
    )
"""
from core.profit.gate_aware_controller import GateAwareController,       gate_aware_controller
from core.profit.scan_controller        import ScanController,            scan_controller
from core.profit.trade_ranker           import GateAwareTradeRanker,      trade_ranker
from core.profit.trade_competition      import GateAwareCompetitionEngine, trade_competition_engine
from core.profit.capital_concentrator   import GateAwareCapitalConcentrator, capital_concentrator
from core.profit.edge_amplifier         import GateAwareEdgeAmplifier,    edge_amplifier

__all__ = [
    "GateAwareController",       "gate_aware_controller",
    "ScanController",             "scan_controller",
    "GateAwareTradeRanker",       "trade_ranker",
    "GateAwareCompetitionEngine", "trade_competition_engine",
    "GateAwareCapitalConcentrator", "capital_concentrator",
    "GateAwareEdgeAmplifier",     "edge_amplifier",
]
