"""Debug logger for plugin diagnostics."""

import domoticz_api
from context import DebugLevel


class DebugLogger:
    """Handles all debug logging for the plugin.

    BASIC level uses Domoticz.Status() for UI visibility.
    Other levels use Domoticz.Debug() for log file only.
    Errors always log via Domoticz.Error().
    """

    def __init__(self, debug_level: DebugLevel = DebugLevel.NONE):
        self._level = debug_level

    @property
    def level(self) -> DebugLevel:
        return self._level

    @level.setter
    def level(self, value: int):
        # Handle -1 (ALL) specially since IntFlag doesn't handle negative values well
        if value == -1:
            self._level = DebugLevel.ALL
        else:
            self._level = DebugLevel(value)

    def is_all(self) -> bool:
        """Check if ALL debugging is enabled."""
        return self._level == DebugLevel.ALL or int(self._level) == -1

    def _is_enabled(self, level: DebugLevel) -> bool:
        """Check if a specific level is enabled."""
        if self._level == DebugLevel.NONE:
            return False
        if self.is_all():
            return True
        return bool(self._level & level)

    def log(self, message: str, level: DebugLevel) -> None:
        """Log a debug message if the level is enabled.

        BASIC level → Domoticz.Status() (visible in UI)
        Other levels → Domoticz.Debug() (log file only)
        """
        if not self._is_enabled(level):
            return

        # BASIC uses Status() for UI visibility, others use Debug()
        if level == DebugLevel.BASIC:
            domoticz_api.log_status(message)
        else:
            # Add level prefix for clarity in logs
            prefix = {
                DebugLevel.DEVICE: "[DEVICE]",
                DebugLevel.COMMS: "[COMMS]",
                DebugLevel.VERBOSE: "[VERBOSE]",
            }.get(level, "[DEBUG]")
            domoticz_api.log_debug(f"{prefix} {message}")

    def error(self, message: str, exc: Exception | None = None) -> None:
        """Log an error message. Always logs regardless of level.

        Args:
            message: The error message
            exc: Optional exception to include type information
        """
        if exc:
            domoticz_api.log_error(f"{message} ({type(exc).__name__}: {exc})")
        else:
            domoticz_api.log_error(message)

    def warning(self, message: str) -> None:
        """Log a warning message. Always logs regardless of level."""
        domoticz_api.log_status(f"Warning: {message}")
