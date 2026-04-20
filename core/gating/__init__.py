"""
EOW Quant Engine — core/gating
Phase 6.6: Hard Gating + Safety Enforcement System

Central authority package that controls ALL trading permission.
No trade may be executed without explicit approval from this package.

Boot flow:
    HardStartValidator.run()        ← HARD STOP if conditions fail
    GlobalGateController.evaluate() ← master permission check
    SafeModeEngine.activate()       ← auto-protection on degradation
    PreTradeGate.check(gate_status) ← final per-trade validation

Public API:
    from core.gating import (
        gate_logger,
        safe_mode_engine,
        global_gate_controller,
        hard_start_validator,
        pre_trade_gate,
    )
"""
from core.gating.gate_logger          import GatingLogger,          gate_logger
from core.gating.safe_mode_engine     import SafeModeEngine,        safe_mode_engine
from core.gating.global_gate_controller import GlobalGateController, global_gate_controller
from core.gating.hard_start_validator import HardStartValidator,    hard_start_validator
from core.gating.pre_trade_gate       import PreTradeGate,          pre_trade_gate

__all__ = [
    "GatingLogger",          "gate_logger",
    "SafeModeEngine",        "safe_mode_engine",
    "GlobalGateController",  "global_gate_controller",
    "HardStartValidator",    "hard_start_validator",
    "PreTradeGate",          "pre_trade_gate",
]
