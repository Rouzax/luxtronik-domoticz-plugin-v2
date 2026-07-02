# pyright: reportMissingImports=false
"""The single seam between the plugin and the Domoticz framework.

This is the only module that imports DomoticzEx. Everything the plugin needs from
the framework (logging, debug/heartbeat setup, device unit create/lookup) goes
through these functions. The framework-injected `devices` mapping is passed in by
the caller, because Domoticz injects Parameters/Devices/Settings into the plugin
entry module's namespace, not into this module.
"""

import DomoticzEx as Domoticz


def log_status(message: str) -> None:
    Domoticz.Status(message)


def log_debug(message: str) -> None:
    Domoticz.Debug(message)


def log_error(message: str) -> None:
    Domoticz.Error(message)


def set_debugging(mask: int) -> None:
    Domoticz.Debugging(mask)


def set_heartbeat(seconds: int) -> None:
    Domoticz.Heartbeat(seconds)


def unit_exists(devices, device_id: str, unit_id: int) -> bool:
    return device_id in devices and unit_id in devices[device_id].Units


def create_unit(device_id: str, unit_id: int, name: str, params: dict) -> object:
    unit = Domoticz.Unit(Name=name, DeviceID=device_id, Unit=unit_id, **params)
    unit.Create()
    return unit


def get_unit(devices, device_id: str, unit_id: int) -> object:
    return devices[device_id].Units[unit_id]
