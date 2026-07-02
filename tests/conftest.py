"""Shared pytest scaffolding.

Domoticz injects the ``DomoticzEx`` extension module and globals (Parameters,
Devices, ...) into plugins at runtime; neither exists in a plain test
environment. We register a lightweight stub for ``DomoticzEx`` so that
``import plugin`` succeeds offline. The plugin only touches ``DomoticzEx`` at
device-creation time (``Domoticz.Unit(...)``), which these tests do not
exercise, so an empty stub is sufficient.
"""

import sys
from pathlib import Path

_here = Path(__file__).parent  # tests/
_root = _here.parent  # repo root
for _p in (_root, _here):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import domoticz_stub  # noqa: E402

sys.modules.setdefault("DomoticzEx", domoticz_stub)
