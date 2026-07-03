import domoticz_stub as stub

import domoticz_api


def setup_function():
    stub.reset()


def test_logging_primitives_route_to_framework():
    domoticz_api.log_status("s")
    domoticz_api.log_debug("d")
    domoticz_api.log_error("e")
    assert stub.calls["status"] == ["s"]
    assert stub.calls["debug"] == ["d"]
    assert stub.calls["error"] == ["e"]


def test_setup_primitives():
    domoticz_api.set_debugging(62)
    domoticz_api.set_heartbeat(30)
    assert stub.calls["debugging"] == [62]
    assert stub.calls["heartbeat"] == [30]


def test_create_unit_registers_and_returns():
    unit = domoticz_api.create_unit("dev1", 5, "Name", {"TypeName": "Temperature"})
    assert unit.Name == "Name"
    assert domoticz_api.unit_exists(stub.Devices, "dev1", 5)
    assert domoticz_api.get_unit(stub.Devices, "dev1", 5) is unit


def test_unit_exists_false_when_absent():
    assert domoticz_api.unit_exists(stub.Devices, "nope", 1) is False
    domoticz_api.create_unit("dev1", 5, "Name", {})
    assert domoticz_api.unit_exists(stub.Devices, "dev1", 6) is False


def test_state_roundtrip():
    stub.reset()
    assert domoticz_api.load_state() is None
    domoticz_api.save_state({"v": 1, "auto_names": {"d:1": {"name": "N"}}})
    assert domoticz_api.load_state() == {"v": 1, "auto_names": {"d:1": {"name": "N"}}}
