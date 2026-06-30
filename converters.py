"""Base, mixin, and simple read converters for the Luxtronik plugin.

Extracted from plugin.py. Does not import DomoticzEx or plugin.
Shared runtime state is accessed via the context module.
"""
from abc import ABC, abstractmethod
import math
from typing import Any, Dict, List, Optional, Tuple

from addresses import LuxtronikAddress, ConfigLimits
import context
from context import DebugLevel


# =============================================================================
# Data Converters (Strategy Pattern)
# =============================================================================

# Type aliases for converter return types
DataStore = Dict[str, List[int]]  # command -> data_list
ConvertResult = Dict[str, Any]  # {'nValue': ..., 'sValue': ...}
GatedResult = Tuple[Optional[ConvertResult], Optional[str]]  # (result, gate_reason)


class DataConverter(ABC):
    """Abstract base class for data converters.

    All converters receive data_store (Dict[command, data_list]) and the command
    key to access their primary data source. Gated converters can access other
    commands (e.g., READ_CALCUL for frequency data) for gating decisions.
    """

    @abstractmethod
    def convert(self, data_store: DataStore, command: str, address: Any, *args) -> ConvertResult:
        """Convert raw data to device update parameters.

        Args:
            data_store: Dict mapping command names to data lists
            command: The command key for this device's primary data
            address: Protocol address or list of addresses
            *args: Additional converter-specific arguments

        Returns:
            Dict with nValue and/or sValue for device update
        """
        pass


class SteadyStateGateMixin:
    """Mixin providing steady-state gating check with reason reporting.

    Uses the controller's minimum frequency target (calc address 237) as the
    gate signal. Returns a reason string if gated, None if gate passes.

    Gate Logic:
    - If min_target_freq <= 0: System is idle, gate closed, counter resets
    - If actual_freq < min_target_freq: System is ramping up, gate closed, counter resets
    - If freq >= min_target: Increment counter; gate opens only after N consecutive
      heartbeats where N = ceil(SETTLING_SECONDS / heartbeat_interval)

    The settling requirement ensures thermal equilibrium before trusting readings.
    Live data showed ~2-3 minutes needed for stabilization after compressor start.
    """

    _steady_count: int = 0

    def check_steady_state(self, data_store: DataStore) -> Optional[str]:
        """Check if compressor is at steady-state operating speed.

        Returns:
            None if gate passes (steady-state operation for sufficient duration)
            String with reason if gated (idle, ramping, or settling)
        """
        calc_data = data_store.get('READ_CALCUL', [])

        # Ensure we have enough data
        if len(calc_data) <= max(LuxtronikAddress.COMPRESSOR_FREQ, LuxtronikAddress.COMPRESSOR_FREQ_MIN):
            self._steady_count = 0
            return "insufficient data"

        try:
            actual_freq = float(calc_data[LuxtronikAddress.COMPRESSOR_FREQ])
            min_target_freq = float(calc_data[LuxtronikAddress.COMPRESSOR_FREQ_MIN])

            # Idle state: min_target is 0
            if min_target_freq <= 0:
                self._steady_count = 0
                return f"idle (freq={actual_freq:.0f} Hz, min_target=0)"

            # Startup ramp: actual hasn't reached minimum target yet
            if actual_freq < min_target_freq:
                self._steady_count = 0
                return f"ramping (freq={actual_freq:.0f} Hz < {min_target_freq:.0f} Hz)"

            # Frequency is at target -- count consecutive heartbeats
            self._steady_count += 1
            required = math.ceil(ConfigLimits.SETTLING_SECONDS / context.heartbeat_interval)

            if self._steady_count < required:
                return (f"settling ({self._steady_count}/{required} heartbeats, "
                        f"freq={actual_freq:.0f} Hz)")

            # Gate passes - steady-state for sufficient duration
            return None

        except (IndexError, TypeError, ValueError) as e:
            self._steady_count = 0
            return f"error checking frequency: {e}"


class FloatConverter(DataConverter):
    """Converts data to float value."""

    def convert(self, data_store: DataStore, command: str, address: int, divider: float = 10) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            value = float(data_list[address]) / divider
            return {'sValue': str(value)}
        except (IndexError, TypeError, ZeroDivisionError) as e:
            context.logger.log(f"FloatConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'sValue': '0.0'}


class NumberConverter(DataConverter):
    """Converts data to integer value."""

    def convert(self, data_store: DataStore, command: str, address: int, divider: float = 1.0) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            value = int(data_list[address] / divider)
            return {'nValue': value}
        except (IndexError, TypeError, ZeroDivisionError) as e:
            context.logger.log(f"NumberConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'nValue': 0}


class SelectorSwitchConverter(DataConverter):
    """Converts data to selector switch level."""

    def convert(self, data_store: DataStore, command: str, address: int, mapping: List[int]) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            value = data_list[address]
            if value in mapping:
                level = mapping.index(value) * 10
            else:
                # Default to first option if value not in mapping
                context.logger.log(f"Selector value {value} not in mapping {mapping}, defaulting to 0",
                                   DebugLevel.VERBOSE)
                level = 0
            return {'nValue': level, 'sValue': str(level)}
        except (IndexError, ValueError) as e:
            context.logger.error(f"SelectorSwitchConverter error", exc=e)
            return {'nValue': 0, 'sValue': '0'}


class InstantPowerConverter(DataConverter):
    """Converts instant power for computed energy meter."""

    def convert(self, data_store: DataStore, command: str, address: int, *args) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            idx = address[0] if isinstance(address, list) else address
            power = float(data_list[idx])
            return {'sValue': f"{power:.1f}"}
        except (IndexError, TypeError) as e:
            context.logger.log(f"InstantPowerConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'sValue': "0.0"}


class InstantPowerSplitConverter(DataConverter):
    """Splits instant power based on operating mode."""

    def convert(self, data_store: DataStore, command: str, address: int, config: List) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            state_idx, valid_states = config
            idx = address[0] if isinstance(address, list) else address

            power = float(data_list[idx])
            current_state = int(data_list[state_idx])

            result_power = power if current_state in valid_states else 0.0
            return {'sValue': f"{result_power:.1f}"}
        except (IndexError, TypeError, ValueError) as e:
            context.logger.log(f"InstantPowerSplitConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'sValue': "0.0"}


class RuntimeHoursConverter(DataConverter):
    """Converts seconds to hours for runtime display.

    Displays as integer hours for cleaner presentation.
    Used for compressor lifetime runtime tracking.
    """

    def convert(self, data_store: DataStore, command: str, address: int, *args) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            seconds = float(data_list[address])
            hours = seconds / 3600
            return {'nValue': 0, 'sValue': f"{hours:.0f}"}
        except (IndexError, TypeError) as e:
            context.logger.log(f"RuntimeHoursConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'nValue': 0, 'sValue': '0'}


class IntegerValueConverter(DataConverter):
    """Converts data to integer value for sValue display.

    Used for count values like compressor starts where we want
    clean integer display in custom sensors.
    """

    def convert(self, data_store: DataStore, command: str, address: int, *args) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            value = int(data_list[address])
            return {'nValue': 0, 'sValue': str(value)}
        except (IndexError, TypeError) as e:
            context.logger.log(f"IntegerValueConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'nValue': 0, 'sValue': '0'}


class BooleanSwitchConverter(DataConverter):
    """Converts boolean (0/1) value to switch state for read-only display.

    Used for status indicators that show on/off state without write capability.
    Example: cooling_permitted flag showing if passive cooling is released.
    """

    def convert(self, data_store: DataStore, command: str, address: int, *args) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            value = bool(int(data_list[address]))
            return {'nValue': 1 if value else 0, 'sValue': 'On' if value else 'Off'}
        except (IndexError, TypeError, ValueError) as e:
            context.logger.log(f"BooleanSwitchConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'nValue': 0, 'sValue': 'Off'}
