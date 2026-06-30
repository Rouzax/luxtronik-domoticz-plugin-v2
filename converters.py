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
            context.logger.error("SelectorSwitchConverter error", exc=e)
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


# =============================================================================
# translate() helper -- wraps context.translator for converter use
# =============================================================================

def translate(key: str) -> str:
    """Shorthand for working mode status translation lookup."""
    return context.translator.get_working_mode_status(key)


# =============================================================================
# Gated and complex read converters (extracted from plugin.py Task 4)
# =============================================================================

class TempDiffConverter(DataConverter):
    """Calculates temperature difference between two sensors."""

    def convert(self, data_store: DataStore, command: str, indices: List[int], divider: float) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            temp1 = float(data_list[indices[0]]) / divider
            temp2 = float(data_list[indices[1]]) / divider
            return {'sValue': str(round(temp1 - temp2, 1))}
        except (IndexError, TypeError, ZeroDivisionError) as e:
            context.logger.log(f"TempDiffConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'sValue': '0.0'}


class GatedFloatConverter(SteadyStateGateMixin, DataConverter):
    """Float converter with steady-state gating.

    Returns tuple (result, gate_reason) - result is None when gated.
    Used for sensors like superheat and pressures that have meaningless
    values when the compressor is not running at steady-state.
    """

    def convert(self, data_store: DataStore, command: str, address: int, divider: float = 10) -> GatedResult:
        # Check steady-state gate first
        gate_reason = self.check_steady_state(data_store)
        if gate_reason:
            return (None, gate_reason)

        try:
            data_list = data_store.get(command, [])
            value = float(data_list[address]) / divider
            return ({'sValue': str(value)}, None)
        except (IndexError, TypeError, ZeroDivisionError) as e:
            context.logger.log(f"GatedFloatConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return (None, f"error: {type(e).__name__}")


class GatedTempDiffConverter(SteadyStateGateMixin, DataConverter):
    """Temperature difference converter with steady-state gating.

    Returns tuple (result, gate_reason) - result is None when gated.
    Used for brine and heating delta-T which approach zero when loops equilibrate.
    """

    def convert(self, data_store: DataStore, command: str, indices: List[int], divider: float) -> GatedResult:
        # Allow updates during passive cooling (pumps running, delta-T is meaningful)
        calc_data = data_store.get('READ_CALCUL', [])
        passive_cooling = (
            len(calc_data) > LuxtronikAddress.PASSIVE_COOLING_FLAG
            and int(calc_data[LuxtronikAddress.PASSIVE_COOLING_FLAG]) == 1
        )

        if not passive_cooling:
            gate_reason = self.check_steady_state(data_store)
            if gate_reason:
                return (None, gate_reason)

        try:
            data_list = data_store.get(command, [])
            temp1 = float(data_list[indices[0]]) / divider
            temp2 = float(data_list[indices[1]]) / divider
            return ({'sValue': str(round(temp1 - temp2, 1))}, None)
        except (IndexError, TypeError, ZeroDivisionError) as e:
            context.logger.log(f"GatedTempDiffConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return (None, f"error: {type(e).__name__}")


class TextStateConverter(DataConverter):
    """Converts heat pump state to text status."""

    # Map Luxtronik mode values to WORKING_MODE_STATUSES keys
    MODE_NAMES = {
        0: 'Heating',
        1: 'DHW',
        2: 'Swimming pool',
        3: 'Cooling',
        4: 'No requirement'
    }

    def convert(self, data_store: DataStore, command: str, address: int, config: List) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])

            # Check for passive cooling mode
            if len(data_list) > LuxtronikAddress.PASSIVE_COOLING_FLAG and data_list[LuxtronikAddress.PASSIVE_COOLING_FLAG] == 1:
                return {'nValue': 0, 'sValue': translate('Cooling')}

            power_idx, power_threshold = config
            current_power = float(data_list[power_idx])
            current_mode = data_list[address]

            if current_power <= power_threshold:
                return {'nValue': 0, 'sValue': translate('Idle')}

            mode_key = self.MODE_NAMES.get(current_mode, 'No requirement')
            return {'nValue': 0, 'sValue': translate(mode_key)}
        except (IndexError, TypeError) as e:
            context.logger.log(f"TextStateConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'nValue': 0, 'sValue': translate('Idle')}


class COPCalculatorConverter(SteadyStateGateMixin, DataConverter):
    """Calculates COP from heat output and power input.

    Implements steady-state gating to prevent logging during transient states.
    Returns a tuple of (result, gate_reason) where result is None if gated.

    Gate Logic:
    1. If allowed_modes specified, current mode must be in list
    2. If passive cooling is active, return None (can't measure COP)
    3. Compressor must be at steady-state: actual_freq >= min_target_freq
    4. Power input must be above noise threshold (10W)
    5. Heat output must be above noise threshold (100W)
    6. Calculated COP must not exceed max_cop limit (configurable)
    """

    # Noise thresholds - minimal values to filter measurement noise
    MIN_POWER_INPUT_W = 10.0
    MIN_HEAT_OUTPUT_W = 100.0

    def __init__(self):
        """Initialize with no max COP limit (set from plugin parameters at startup)."""
        self.max_cop: Optional[float] = None

    def convert(self, data_store: DataStore, command: str, address: int, config: List) -> GatedResult:
        """Calculate COP only during steady-state operation in allowed modes.

        Args:
            data_store: Dict mapping command names to data lists
            command: The command key (should be READ_CALCUL for COP)
            address: Primary address (heat output index)
            config: [heat_output_idx, power_input_idx, allowed_modes]
                    allowed_modes is optional list of mode values (e.g., [0, 1] for heating + DHW)

        Returns:
            Tuple of (result_dict, gate_reason) where result_dict is None if gated
        """
        try:
            data_list = data_store.get(command, [])

            heat_output_idx = config[0]
            power_input_idx = config[1]
            allowed_modes = config[2] if len(config) > 2 else None

            # Gate 1: Check operating mode if filter specified
            if allowed_modes is not None:
                if len(data_list) > LuxtronikAddress.WORKING_MODE:
                    mode = int(data_list[LuxtronikAddress.WORKING_MODE])
                    if mode not in allowed_modes:
                        return (None, f"mode filtered (mode={mode}, allowed={allowed_modes})")
                else:
                    return (None, "mode data unavailable")

            # Gate 2: Check for passive cooling (if applicable)
            if len(data_list) > LuxtronikAddress.PASSIVE_COOLING_FLAG:
                if int(data_list[LuxtronikAddress.PASSIVE_COOLING_FLAG]) == 1:
                    return (None, "passive cooling active")

            # Gate 3: Steady-state operation check (uses mixin)
            gate_reason = self.check_steady_state(data_store)
            if gate_reason:
                return (None, gate_reason)

            # Get values
            heat_output = float(data_list[heat_output_idx])
            power_input = float(data_list[power_input_idx])

            # Gate 4: Basic sanity checks - filter noise
            if power_input < self.MIN_POWER_INPUT_W:
                return (None, f"noise filter (power={power_input:.0f}W < {self.MIN_POWER_INPUT_W:.0f}W)")
            if heat_output < self.MIN_HEAT_OUTPUT_W:
                return (None, f"noise filter (heat={heat_output:.0f}W < {self.MIN_HEAT_OUTPUT_W:.0f}W)")

            # Calculate and return COP
            cop = heat_output / power_input

            # Gate 5: Max COP sanity check - filter transient spikes
            if self.max_cop is not None and cop > self.max_cop:
                return (None, f"COP {cop:.2f} exceeds max limit ({self.max_cop:.1f})")

            return ({'nValue': 0, 'sValue': f"{cop:.2f}"}, None)

        except (IndexError, TypeError, ZeroDivisionError) as e:
            context.logger.log(f"COPCalculatorConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return (None, f"error: {type(e).__name__}")


class CapacityConverter(SteadyStateGateMixin, DataConverter):
    """Calculates compressor capacity utilization percentage.

    Capacity = (actual_freq / max_freq) * 100

    Gated to only report during steady-state operation, preventing
    misleading readings during startup ramps.

    Returns 0% when compressor is off (actual_freq = 0).
    """

    def convert(self, data_store: DataStore, command: str, address: int, indices: List[int]) -> GatedResult:
        try:
            data_list = data_store.get(command, [])
            actual_idx, max_idx = indices

            actual = float(data_list[actual_idx])
            maximum = float(data_list[max_idx])

            # If max is 0 or negative, we can't calculate
            if maximum <= 0:
                return (None, f"max frequency is 0 or negative ({maximum})")

            # If compressor is off, return 0%
            if actual <= 0:
                return ({'nValue': 0, 'sValue': "0"}, None)

            # Check steady-state gate for meaningful readings
            gate_reason = self.check_steady_state(data_store)
            if gate_reason:
                return (None, gate_reason)

            # Calculate capacity percentage
            percent = (actual / maximum) * 100
            percent = min(100, percent)  # Clamp to 100% max

            return ({'nValue': 0, 'sValue': f"{percent:.0f}"}, None)

        except (IndexError, TypeError, ValueError) as e:
            context.logger.log(f"CapacityConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return (None, f"error: {type(e).__name__}")


class CycleTracker:
    """Tracks compressor cycle completions by detecting timer resets.

    The current cycle timer (Time_WPein_akt, index 67) resets to 0 when
    a new cycle starts. By tracking the previous value, we detect completions:

        Previous: 1920s (32 min) -> Current: 60s (1 min) = RESET DETECTED

    Returns update dict only when a cycle completes, allowing sparse updates
    to Domoticz that accurately represent individual cycle durations.

    Usage:
        tracker = CycleTracker()
        # Each heartbeat:
        result = tracker.update(current_cycle_seconds)
        if result is not None:
            # Cycle completed - update device
    """

    # Minimum cycle duration to record (filters glitches/restarts)
    MIN_CYCLE_MINUTES = 1.0
    # Maximum plausible cycle duration (24 hours) -- anything longer is a
    # stale value from before a Domoticz/plugin reboot, not a real cycle.
    MAX_CYCLE_SECONDS = 86400

    def __init__(self):
        self.previous_cycle_seconds = 0

    def update(self, current_cycle_seconds: int) -> Optional[Dict[str, Any]]:
        """Check for cycle completion and return update dict if detected.

        Args:
            current_cycle_seconds: Current cycle time from controller (index 67)

        Returns:
            Dict with nValue/sValue when cycle completes (for device update)
            None when cycle is still running (don't update device)
        """
        result = None

        # Reset detected: current < previous means timer restarted
        if current_cycle_seconds < self.previous_cycle_seconds:
            # Discard if previous value is implausibly large (stale after reboot)
            if self.previous_cycle_seconds > self.MAX_CYCLE_SECONDS:
                context.logger.log(
                    f"Cycle discarded: previous={self.previous_cycle_seconds}s exceeds "
                    f"max {self.MAX_CYCLE_SECONDS}s (likely stale after reboot)",
                    DebugLevel.VERBOSE
                )
            else:
                # Previous value was the completed cycle's duration
                completed_minutes = self.previous_cycle_seconds / 60

                # Ignore very short "cycles" (glitches, restarts)
                if completed_minutes >= self.MIN_CYCLE_MINUTES:
                    result = {'nValue': 0, 'sValue': f"{completed_minutes:.0f}"}
                    context.logger.log(
                        f"Cycle completed: {completed_minutes:.0f} min "
                        f"(prev={self.previous_cycle_seconds}s, curr={current_cycle_seconds}s)",
                        DebugLevel.VERBOSE
                    )

        self.previous_cycle_seconds = current_cycle_seconds
        return result


class LastCycleConverter(DataConverter):
    """Converter wrapper for CycleTracker.

    Unlike other converters, this one requires a stateful CycleTracker
    instance to be passed in via the plugin. The converter itself just
    reads the current cycle time and delegates to the tracker.

    Returns gated result - only updates when a cycle actually completes.
    """

    def convert(self, data_store: DataStore, command: str, address: int,
                tracker: 'CycleTracker') -> GatedResult:
        try:
            data_list = data_store.get(command, [])
            current_cycle_s = int(data_list[address])

            result = tracker.update(current_cycle_s)

            if result is not None:
                return (result, None)
            else:
                return (None, "cycle in progress")

        except (IndexError, TypeError) as e:
            context.logger.log(f"LastCycleConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return (None, f"error: {type(e).__name__}")


class RefrigerantDiffConverter(SteadyStateGateMixin, DataConverter):
    """Condensing saturation temperature minus a reference temperature.

    Computes t_cond = t_sat(calc[hp_addr] / hp_divider) using the refrigerant's
    P-T saturation curve, then returns t_cond - calc[ref_addr] / ref_divider.

    Pressure-temperature curve note:
    - Uses the saturated-liquid (bubble) line as the condensing reference.
    - For R407C (zeotropic, ~5-6 K glide) this sits below the dew-point condensing
      temperature. A dew-line table would be needed for true condensing temperature.
    - The high-pressure gauge-vs-absolute basis from the controller is unverified;
      use this converter only for basis-tolerant metrics (lift, condenser approach),
      not for subcooling where absolute basis matters.

    Gated to steady-state compressor operation (SteadyStateGateMixin).
    """

    def convert(self, data_store: DataStore, command: str, indices: List[int], hp_divider: float = 100, ref_divider: float = 10) -> GatedResult:
        gate_reason = self.check_steady_state(data_store)
        if gate_reason:
            return (None, gate_reason)

        try:
            calc = data_store.get(command, [])
            hp_addr, ref_addr = indices
            t_cond = context.refrigerant.t_sat(float(calc[hp_addr]) / hp_divider)
            ref = float(calc[ref_addr]) / ref_divider
            return ({'sValue': str(round(t_cond - ref, 1))}, None)
        except (IndexError, TypeError, ZeroDivisionError) as e:
            context.logger.log(
                f"RefrigerantDiffConverter error: {type(e).__name__}: {e}",
                DebugLevel.VERBOSE
            )
            return (None, f"error: {type(e).__name__}")


class FreqHeadroomConverter(DataConverter):
    """Target minus actual compressor frequency (Hz).

    Reports how much frequency headroom remains between the current operating
    frequency and the controller's target frequency. A positive value means the
    compressor is running below target; negative means it is running above.

    Gated to compressor-on (actual > 0). Returns None when the compressor is idle.
    Unlike SteadyStateGateMixin, this gate does not require settling: the metric
    is meaningful as soon as the compressor is spinning.
    """

    def convert(self, data_store: DataStore, command: str, indices: List[int], *args) -> GatedResult:
        try:
            calc = data_store.get(command, [])
            target_addr, actual_addr = indices
            actual = calc[actual_addr]
            if actual <= 0:
                return (None, "idle (compressor off)")
            target = calc[target_addr]
            return ({'sValue': str(int(round(target - actual)))}, None)
        except (IndexError, TypeError) as e:
            context.logger.log(
                f"FreqHeadroomConverter error: {type(e).__name__}: {e}",
                DebugLevel.VERBOSE
            )
            return (None, f"error: {type(e).__name__}")


# =============================================================================
# Write Converters
# =============================================================================
class WriteConverter(ABC):
    """Abstract base class for write converters."""

    @abstractmethod
    def convert(self, **kwargs) -> int:
        """Convert command to value for writing."""
        pass


class CommandToNumberConverter(WriteConverter):
    """Converts On/Off command to number."""

    def convert(self, Command: str = '', **kwargs) -> int:
        return 1 if Command == 'On' else 0


class LevelWithDividerConverter(WriteConverter):
    """Returns level divided by divider."""

    def __init__(self, divider: float):
        self.divider = divider

    def convert(self, Level: int = 0, **kwargs) -> int:
        return int(Level / self.divider)


class AvailableWritesConverter(WriteConverter):
    """Returns value from available writes based on level."""

    def __init__(self, divider: float, writes_idx: int):
        self.divider = divider
        self.writes_idx = writes_idx

    def convert(self, available_writes: Dict, Level: int = 0, **kwargs) -> int:
        try:
            values = available_writes[self.writes_idx].get_val()
            index = int(Level / self.divider)
            if 0 <= index < len(values):
                return values[index]
            else:
                context.logger.error(
                    f"Level {Level} (index {index}) out of range for writes_idx {self.writes_idx}"
                )
                return values[0] if values else 0
        except (KeyError, IndexError, TypeError) as e:
            context.logger.error("AvailableWritesConverter error", exc=e)
            return 0
