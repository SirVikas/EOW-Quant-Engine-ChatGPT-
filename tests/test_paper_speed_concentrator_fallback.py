import importlib
from core.capital_concentrator import ConcentrationResult
from core.profit.capital_concentrator import GateAwareCapitalConcentrator

cc_mod = importlib.import_module("core.profit.capital_concentrator")


class _RejectBase:
    def concentrate(self, **kwargs):
        return ConcentrationResult(
            ok=False,
            size_multiplier=0.0,
            band="REJECT",
            capped=False,
            max_risk_usdt=0.0,
            reason="CC_REJECT(rank below bands)",
        )


class _PassBase:
    def concentrate(self, **kwargs):
        return ConcentrationResult(
            ok=True,
            size_multiplier=1.5,
            band="HIGH",
            capped=False,
            max_risk_usdt=10.0,
            reason="CC_HIGH",
        )


def test_paper_speed_concentrator_reject_becomes_safe_fallback(monkeypatch):
    # Gate open path
    monkeypatch.setattr(cc_mod.gate_aware_controller, "allow_profit_engine", lambda _: True)

    cc = GateAwareCapitalConcentrator(base=_RejectBase())
    out = cc.concentrate(
        gate_status={"reason": "ALL_CLEAR"},
        rank_score=0.40,
        equity=1000.0,
        base_risk_usdt=10.0,
        upstream_mult=1.2,
        ev=0.1,
    )

    assert out.ok is True
    assert out.band == "SAFE_FALLBACK"
    assert out.size_multiplier == 1.2


def test_concentrator_keeps_normal_result_when_ok(monkeypatch):
    monkeypatch.setattr(cc_mod.gate_aware_controller, "allow_profit_engine", lambda _: True)
    cc = GateAwareCapitalConcentrator(base=_PassBase())
    out = cc.concentrate(
        gate_status={"reason": "ALL_CLEAR"},
        rank_score=0.9,
        equity=1000.0,
        base_risk_usdt=10.0,
        upstream_mult=1.0,
        ev=0.2,
    )
    assert out.ok is True
    assert out.band == "HIGH"
