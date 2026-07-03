import domoticz_stub as stub

import plugin


class _Boom:
    def onStart(self):
        raise RuntimeError("start boom")

    def onStop(self):
        raise RuntimeError("stop boom")

    def onHeartbeat(self):
        raise RuntimeError("beat boom")


def setup_function():
    stub.reset()


def test_heartbeat_error_is_caught_and_logged(monkeypatch):
    monkeypatch.setattr(plugin, "_plugin", _Boom())
    plugin.onHeartbeat()  # must NOT raise
    assert any("beat boom" in m for m in stub.calls["error"])


def test_start_and_stop_errors_are_caught(monkeypatch):
    monkeypatch.setattr(plugin, "_plugin", _Boom())
    plugin.onStart()
    plugin.onStop()
    assert any("start boom" in m for m in stub.calls["error"])
    assert any("stop boom" in m for m in stub.calls["error"])


def test_oncommand_error_is_caught_and_logged(monkeypatch):
    class _RaisingSpecs:
        def get(self, *a, **k):
            raise RuntimeError("cmd boom")

    monkeypatch.setattr(plugin, "_unit_specs", _RaisingSpecs())
    plugin.onCommand("dev1", 1, "On", 0, "")  # must NOT raise
    assert any("cmd boom" in m for m in stub.calls["error"])
    assert any("onCommand failed" in m for m in stub.calls["error"])
