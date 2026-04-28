import importlib
from core.profit.scan_controller import ScanController

sc_mod = importlib.import_module("core.profit.scan_controller")


def test_scan_heartbeat_logging_is_throttled(monkeypatch):
    ctrl = ScanController()

    logs = []
    monkeypatch.setattr(sc_mod.logger, "debug", lambda msg: logs.append(msg))

    ts = {"v": 1000.0}
    monkeypatch.setattr(sc_mod.time, "time", lambda: ts["v"])

    gate = {"can_trade": True, "safe_mode": False}
    ctrl.can_scan(gate)   # should log
    ctrl.can_scan(gate)   # same timestamp, should not log
    ts["v"] = 1002.0
    ctrl.can_scan(gate)   # still inside 5s interval, no log
    ts["v"] = 1006.0
    ctrl.can_scan(gate)   # outside interval, should log again

    assert len(logs) == 2
