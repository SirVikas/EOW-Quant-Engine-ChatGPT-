import asyncio

from core.ws_stabilizer import WsStabilizer


class _MockMdp:
    async def reconnect(self):
        return None


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


def test_first_reconnect_logs_soft_ws001(monkeypatch):
    stab = WsStabilizer(_MockMdp())
    codes = []

    def _capture(code: str, symbol: str = "", extra: str = ""):
        codes.append(code)

    monkeypatch.setattr(stab, "_error_log", _capture)
    _run(stab._force_reconnect(61.0))
    assert codes[-1] == "WS_001"


def test_second_reconnect_escalates_to_ws002(monkeypatch):
    stab = WsStabilizer(_MockMdp())
    codes = []

    def _capture(code: str, symbol: str = "", extra: str = ""):
        codes.append(code)

    monkeypatch.setattr(stab, "_error_log", _capture)
    _run(stab._force_reconnect(61.0))
    _run(stab._force_reconnect(70.0))
    assert codes[-1] == "WS_002"
