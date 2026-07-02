import domoticz_stub as stub

import plugin
from context import DebugLevel


def setup_function():
    stub.reset()


def test_basic_level_uses_status():
    log = plugin.DebugLogger(DebugLevel.BASIC)
    log.log("hello", DebugLevel.BASIC)
    assert stub.calls["status"] == ["hello"]
    assert stub.calls["debug"] == []


def test_device_level_uses_prefixed_debug():
    log = plugin.DebugLogger(DebugLevel.DEVICE)
    log.log("x", DebugLevel.DEVICE)
    assert stub.calls["debug"] == ["[DEVICE] x"]


def test_disabled_level_logs_nothing():
    log = plugin.DebugLogger(DebugLevel.NONE)
    log.log("x", DebugLevel.DEVICE)
    assert stub.calls["debug"] == [] and stub.calls["status"] == []


def test_error_includes_exception_type():
    plugin.DebugLogger().error("boom", ValueError("bad"))
    assert stub.calls["error"] == ["boom (ValueError: bad)"]
