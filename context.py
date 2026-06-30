"""Shared runtime state and the DebugLevel enum, for modules that must not import
plugin.py or DomoticzEx. plugin.onStart() replaces logger/translator/heartbeat/refrigerant
with the live objects; the defaults keep converters importable offline (tests inject stubs)."""
from enum import IntFlag
from refrigerant import get as _get_refrigerant
from addresses import ConfigLimits


# =============================================================================
# Debug Level Constants (using IntFlag for bitwise operations)
# =============================================================================
class DebugLevel(IntFlag):
    """Debug level flags for controlling log output.

    Levels:
        NONE (0):    Errors only (always logged)
        BASIC (1):   Lifecycle, summaries, write confirmations -> Status()
        DEVICE (2):  Device updates (changes only) -> Debug()
        COMMS (4):   Connections, protocol, commands -> Debug()
        VERBOSE (8): Tracker details, data conversion -> Debug()
        ALL (-1):    Everything
    """
    NONE = 0
    BASIC = 1       # Lifecycle, summaries, write confirmations
    DEVICE = 2      # Device updates (changes only)
    COMMS = 4       # Connections, protocol, commands
    VERBOSE = 8     # Tracker details, data conversion
    ALL = -1        # All debugging enabled


# =============================================================================
# Null/passthrough defaults (replaced by plugin.onStart with live objects)
# =============================================================================
class _NullLogger:
    """Drop-in logger used before onStart wires in the real DebugLogger."""
    level = 0

    def log(self, *a, **k) -> None:
        pass

    def error(self, *a, **k) -> None:
        pass


class _PassthroughTranslator:
    """Drop-in translator used before onStart wires in the real TranslationManager."""

    def get_working_mode_status(self, key: str) -> str:
        return key


# Module-level state: replaced by plugin.onStart() with live objects.
logger: _NullLogger = _NullLogger()
translator: _PassthroughTranslator = _PassthroughTranslator()
heartbeat_interval: int = ConfigLimits.HEARTBEAT_DEFAULT
refrigerant = _get_refrigerant("R407C")
