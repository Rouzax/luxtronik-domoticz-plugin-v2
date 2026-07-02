import pytest

from addresses import ConfigLimits
from plugin_config import PluginConfig, read_plugin_config


def test_full_params():
    p = {
        "Mode6": "2",
        "Mode3": "1",
        "Address": "10.0.0.5",
        "Port": "8889",
        "Mode2": "20",
        "Mode1": "45",
        "Mode4": "1",
        "Mode5": "3,70,4,150",
    }
    cfg = read_plugin_config(p)
    assert cfg == PluginConfig(
        debug_level=2,
        language="1",
        address="10.0.0.5",
        port=8889,
        heartbeat_raw=20,
        max_cop_raw="45",
        pump_comp_enable_raw="1",
        pump_comp_params_raw="3,70,4,150",
    )


def _valid_required():
    return {"Address": "1.2.3.4", "Port": "8889", "Mode3": "1"}


def test_guarded_fields_default_on_invalid():
    cfg = read_plugin_config({**_valid_required(), "Mode6": "nope", "Mode2": "x"})
    assert cfg.debug_level == 0
    assert cfg.heartbeat_raw == ConfigLimits.HEARTBEAT_DEFAULT


def test_optional_get_fields_default_when_missing():
    cfg = read_plugin_config(_valid_required())
    assert cfg.max_cop_raw == "30"
    assert cfg.pump_comp_enable_raw == "0"
    assert cfg.pump_comp_params_raw == "2,60,3,140"


def test_missing_required_key_raises():
    with pytest.raises(KeyError):
        read_plugin_config({"Port": "8889", "Mode3": "1"})  # no Address


def test_invalid_port_raises():
    with pytest.raises(ValueError):
        read_plugin_config({"Address": "1.2.3.4", "Port": "notaport", "Mode3": "1"})
