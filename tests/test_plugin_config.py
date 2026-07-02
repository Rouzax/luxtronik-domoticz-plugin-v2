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


def test_defaults_when_missing_or_invalid():
    cfg = read_plugin_config({"Address": "1.2.3.4", "Port": "x", "Mode6": "nope"})
    assert cfg.debug_level == 0
    assert cfg.port == 0
    assert cfg.heartbeat_raw == ConfigLimits.HEARTBEAT_DEFAULT
    assert cfg.max_cop_raw == "30"
    assert cfg.pump_comp_enable_raw == "0"
    assert cfg.pump_comp_params_raw == "2,60,3,140"
    assert cfg.language == ""
