"""Device update tracking.

Determines when a Domoticz device unit actually needs to be updated,
comparing incoming values against the current device state and applying
a periodic refresh interval for graphing device types.
"""

import time
from typing import Dict, Tuple


class DeviceUpdateTracker:
    """Tracks device updates and determines when updates are needed."""

    GRAPH_UPDATE_INTERVAL = 125  # ~2 minutes

    GRAPHING_TYPES = {80, 242, 243}  # Temperature, Custom types that graph
    NON_GRAPHING_TYPES = {244}  # Switch types

    def __init__(self):
        self._last_update_times: Dict[int, float] = {}
        self._device_type_cache: Dict[int, bool] = {}

    def _is_graphing_device(self, unit) -> bool:
        """Determine if a unit produces graphs."""
        device_id = unit.ID

        if device_id in self._device_type_cache:
            return self._device_type_cache[device_id]

        # Text devices (Type 243, SubType 19) don't graph
        if hasattr(unit, "SubType") and unit.Type == 243 and unit.SubType == 19:
            self._device_type_cache[device_id] = False
            return False

        is_graphing = unit.Type in self.GRAPHING_TYPES
        self._device_type_cache[device_id] = is_graphing
        return is_graphing

    def _normalize_value(self, value_str: str) -> str:
        """Normalize a value for comparison.

        Parses as float and re-formats with consistent precision to prevent
        false change detection from formatting differences (e.g. "23.40" vs "23.4").
        """
        if not value_str:
            return ""

        value_str = value_str.strip()
        if ";" in value_str:
            value_str = value_str.split(";")[0].strip()

        try:
            float_value = float(value_str)
            # Use 2 decimal places for all numeric values — enough for pressure (bar)
            # and COP, while temperatures just get a trailing zero (harmless).
            # Both old and new values pass through the same normalization, so
            # the absolute precision doesn't matter — consistency does.
            return f"{float_value:.2f}"
        except ValueError:
            return value_str.lower()

    def needs_update(self, unit, new_values: Dict) -> Tuple[bool, str, str]:
        """Determine if a unit needs updating."""
        current_time = time.monotonic()
        device_id = unit.ID
        is_graphing = self._is_graphing_device(unit)

        # Compare values
        current_nvalue = unit.nValue
        current_svalue = str(unit.sValue)

        values_changed = False
        diff_message = ""

        if "nValue" in new_values and new_values["nValue"] != current_nvalue:
            values_changed = True
            diff_message += f"nValue: {current_nvalue} -> {new_values['nValue']}; "

        if "sValue" in new_values:
            norm_current = self._normalize_value(current_svalue)
            norm_new = self._normalize_value(new_values["sValue"])
            if norm_current != norm_new:
                values_changed = True
                diff_message += f"sValue: {current_svalue} -> {new_values['sValue']}"

        if values_changed:
            if is_graphing:
                self._last_update_times[device_id] = current_time
            return True, "Values changed", diff_message

        # Periodic update for graphing devices
        if is_graphing:
            last_update = self._last_update_times.get(device_id, 0)
            time_since = current_time - last_update
            if time_since >= self.GRAPH_UPDATE_INTERVAL:
                self._last_update_times[device_id] = current_time
                # Include current value in log for visibility
                value_info = f"sValue: {new_values.get('sValue', current_svalue)}"
                return True, "Interval update", value_info
            return False, f"Next update in {int(self.GRAPH_UPDATE_INTERVAL - time_since)}s", ""

        return False, "No changes", ""
