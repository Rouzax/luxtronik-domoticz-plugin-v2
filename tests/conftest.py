"""Shared pytest scaffolding.

Domoticz injects the ``DomoticzEx`` extension module and globals (Parameters,
Devices, ...) into plugins at runtime; neither exists in a plain test
environment. We register a lightweight stub for ``DomoticzEx`` so that
``import plugin`` succeeds offline. The plugin only touches ``DomoticzEx`` at
device-creation time (``Domoticz.Unit(...)``), which these tests do not
exercise, so an empty stub is sufficient.
"""
import sys
import types

if "DomoticzEx" not in sys.modules:
    _stub = types.ModuleType("DomoticzEx")
    # Attributes are only accessed at runtime, not at import; define no-op
    # placeholders so any accidental access fails loudly rather than silently.
    sys.modules["DomoticzEx"] = _stub
