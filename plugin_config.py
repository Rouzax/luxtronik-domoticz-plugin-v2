"""Pure parsing of the Domoticz plugin Parameters dict into a typed config.

No Domoticz import: this operates on a plain dict so it is trivially testable.
Each field reproduces the exact transform onStart used inline.
"""

from dataclasses import dataclass

from addresses import ConfigLimits


@dataclass(frozen=True)
class PluginConfig:
    debug_level: int
    language: str
    address: str
    port: int
    heartbeat_raw: int
    max_cop_raw: str
    pump_comp_enable_raw: str
    pump_comp_params_raw: str


def _int_or(params: dict, key: str, default: int) -> int:
    try:
        return int(params[key])
    except (ValueError, TypeError, KeyError):
        return default


def read_plugin_config(params: dict) -> PluginConfig:
    return PluginConfig(
        debug_level=_int_or(params, "Mode6", 0),
        language=params.get("Mode3", ""),
        address=params.get("Address", ""),
        port=_int_or(params, "Port", 0),
        heartbeat_raw=_int_or(params, "Mode2", ConfigLimits.HEARTBEAT_DEFAULT),
        max_cop_raw=params.get("Mode1", "30"),
        pump_comp_enable_raw=params.get("Mode4", "0"),
        pump_comp_params_raw=params.get("Mode5", "2,60,3,140"),
    )
