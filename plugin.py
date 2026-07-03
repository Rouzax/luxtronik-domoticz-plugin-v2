"""
Luxtronik Heat Pump Controller Plugin v2 - Refactored for DomoticzEx Framework
Author: Rouzax, 2025 (Refactored)

<plugin key="luxtronikex" name="Luxtronik Heat Pump Controller v2" author="Rouzax" version="2.1.2" externallink="https://github.com/Rouzax/luxtronik-domoticz-plugin-v2">
    <description>
        <h2>Luxtronik Heat Pump Controller Plugin</h2><br/>
        <p>This plugin connects to Luxtronik-based heat pump controllers using socket communication.</p>

        <h3>Features:</h3>
        <ul>
            <li>Real-time monitoring of heat pump parameters</li>
            <li>Support for temperature readings, operating modes, and power consumption</li>
            <li>Multi-language support (English, Polish, Dutch, German, French)</li>
            <li>Configurable update intervals</li>
            <li>Multi-instance support for multiple heat pumps</li>
        </ul>

        <h3>Configuration Notes:</h3>
        <ul>
            <li>Default port for Luxtronik is typically 8889</li>
            <li>Update interval is clamped to 10-60 seconds for stability</li>
            <li>Values greater than 30 seconds will trigger a Domoticz timeout warning, but the plugin will continue to function correctly</li>
        </ul>

        <h3>Security Notes:</h3>
        <ul>
            <li>The Luxtronik protocol uses plain TCP without encryption (hardware limitation)</li>
            <li>Keep your heat pump on a trusted LAN/VLAN; do not expose to the internet</li>
            <li>Use a VPN if remote access is required</li>
        </ul>

        <h3>COP Accuracy Note:</h3>
        <p>For accurate COP averages over time, enable: <b>Settings → Log History → 'Only add newly received values to the Log'</b></p>
        <p>When disabled, Domoticz fills in the last received value every 5 minutes even when the heat pump is idle, skewing COP averages.</p>
        <p>The controller's power reading only measures compressor power. Enable 'Pump Power Compensation' to include estimated circulation pump power for true system COP.</p>
    </description>
    <params>
        <param field="Address" label="Heat Pump IP Address" width="200px" required="true" default="127.0.0.1">
            <description>IP address of your Luxtronik controller</description>
        </param>
        <param field="Port" label="Heat Pump Port" width="60px" required="true" default="8889">
            <description>TCP port of your Luxtronik controller (default: 8889)</description>
        </param>
        <param field="Mode1" label="Max COP Value" width="75px" required="false" default="30">
            <description>Maximum COP value to accept. Readings above this are discarded as measurement artifacts. Leave empty to disable filtering.</description>
        </param>
        <param field="Mode2" label="Update Interval" width="150px" required="true" default="20">
            <description>Data update interval in seconds (will be clamped to 10-60)</description>
        </param>
        <param field="Mode3" label="Language" width="150px">
            <description>Select interface language</description>
            <options>
                <option label="English" value="0" default="true"/>
                <option label="Polish" value="1"/>
                <option label="Dutch" value="2"/>
                <option label="German" value="3"/>
                <option label="French" value="4"/>
            </options>
        </param>
        <param field="Mode4" label="Pump Power Compensation" width="150px">
            <description>Add estimated circulation pump power to compressor reading for more accurate COP. Requires pump speed data from controller.</description>
            <options>
                <option label="Off" value="0" default="true"/>
                <option label="On" value="1"/>
            </options>
        </param>
        <param field="Mode5" label="Pump Power Ranges (W)" width="200px" required="false" default="2,60,3,140">
            <description>
                <table border="1" cellpadding="3" cellspacing="0" style="margin:4px 0">
                    <tr><th>Position</th><th>Pump</th><th>Default (W)</th></tr>
                    <tr><td>1</td><td>HUP min</td><td>2</td></tr>
                    <tr><td>2</td><td>HUP max</td><td>60</td></tr>
                    <tr><td>3</td><td>VBO min</td><td>3</td></tr>
                    <tr><td>4</td><td>VBO max</td><td>140</td></tr>
                </table>
                Default values are for WZSV 92K3M. Check your manual for other models.
            </description>
        </param>
        <param field="Mode6" label="Debug Level" width="150px">
            <description>Select debug categories to enable</description>
            <options>
                <option label="None" value="0" default="true"/>
                <option label="Basic" value="1"/>
                <option label="Basic + Device" value="3"/>
                <option label="Basic + Comms" value="5"/>
                <option label="Basic + Device + Comms" value="7"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""

from typing import Any, Dict, Optional, Tuple

import domoticz_api
from addresses import ConfigLimits, LuxtronikAddress, SocketCommand
from connection import ConnectionManager
from context import DebugLevel
from converters import CycleTracker, DataStore
from debug_logger import DebugLogger
from device_factory import DeviceFactory
from device_spec import DeviceSpec, Field
from device_specs_table import build_device_specs
from device_update_tracker import DeviceUpdateTracker
from plugin_config import read_plugin_config
from translation_manager import TranslationManager
from translations import DEVICE_TRANSLATIONS, SELECTOR_OPTIONS, WORKING_MODE_STATUSES

# Global logger instance
_logger = DebugLogger()

# Heartbeat interval in seconds (set during onStart, used for settling time calculations)
_heartbeat_interval: int = ConfigLimits.HEARTBEAT_DEFAULT


# Global translation manager
_translator = TranslationManager()


# =============================================================================
# Module-level spec storage (for command handling across restarts)
# =============================================================================
# NOTE: These globals are necessary due to DomoticzEx framework constraints.
# The framework calls Unit.onCommand() directly without passing plugin context.
# There is no clean way to inject dependencies into Unit instances at runtime,
# so we use module-level storage that is populated during plugin initialization.
# This pattern is safe because:
# 1. Domoticz runs plugins single-threaded per hardware instance
# 2. The globals are only written during onStart() and cleared during onStop()
# 3. Each hardware instance has its own Python interpreter context
_unit_specs: Dict[Tuple[str, int], "DeviceSpec"] = {}  # (DeviceID, Unit) -> Spec
_plugin_ref: Optional["LuxtronikPlugin"] = None  # Reference to plugin instance


# =============================================================================
# Main Plugin Class
# =============================================================================
class LuxtronikPlugin:
    """Main plugin class orchestrating all components."""

    def __init__(self):
        self.connection: Optional[ConnectionManager] = None
        self.update_tracker = DeviceUpdateTracker()
        self.cycle_tracker = CycleTracker()  # For last cycle duration tracking
        self.available_writes: Dict[int, Field] = {}
        self._device_specs: Dict[int, DeviceSpec] = {}  # Unit ID -> Spec
        self._command_specs: Dict[str, Dict[int, DeviceSpec]] = {
            "READ_CALCUL": {},
            "READ_PARAMS": {},
        }
        self._device_id: str = ""  # Will be set during onStart
        self._pump_compensation_enabled: bool = False
        self._pump_power_ranges: Optional[Dict[str, float]] = None

    def _get_device_id(self) -> str:
        """Generate stable DeviceID based on HardwareID.

        HardwareID is assigned by Domoticz when hardware is created and never
        changes, even if the hardware is renamed or IP address changes.
        This ensures device stability across configuration changes.
        """
        hw_id = _parameters().get("HardwareID", "0")
        return f"luxtronikex_hw{hw_id}"

    def _init_available_writes(self) -> None:
        """Initialize available write fields."""
        self.available_writes = {
            -1: Field(),
            LuxtronikAddress.TEMP_OFFSET: Field(
                _translator.get_device_name("temp_offset"), list(range(-50, 51, 5))
            ),
            LuxtronikAddress.HEATING_MODE: Field(
                _translator.get_device_name("heating_mode"), [0, 1, 2, 3, 4]
            ),
            LuxtronikAddress.HOT_WATER_MODE: Field(
                _translator.get_device_name("hot_water_mode"), [0, 1, 2, 3, 4]
            ),
            LuxtronikAddress.DHW_TEMP_TARGET: Field(
                _translator.get_device_name("dhw_temp_target"), list(range(300, 651, 5))
            ),
            LuxtronikAddress.COOLING_ENABLED: Field(
                _translator.get_device_name("cooling_enabled"), [0, 1]
            ),
            LuxtronikAddress.DHW_POWER_MODE: Field(
                _translator.get_device_name("dhw_power_mode"), [0, 1]
            ),
            LuxtronikAddress.ROOM_TEMP_SETPOINT: Field(
                _translator.get_device_name("room_temp_setpoint"), list(range(150, 301, 5))
            ),
        }

    def create_devices(self) -> None:
        """Create all Domoticz devices."""
        global _unit_specs, _plugin_ref

        _logger.log("Creating devices", DebugLevel.BASIC)

        # Store reference to plugin for command handling
        _plugin_ref = self

        self._init_available_writes()
        specs = build_device_specs()

        # Inject CycleTracker into the last_cycle device spec
        # The last_cycle device needs stateful tracking between heartbeats
        for spec in specs:
            if spec.spec_id == "last_cycle":
                spec.read_args = (self.cycle_tracker,)
                _logger.log("Injected CycleTracker into last_cycle device", DebugLevel.VERBOSE)
                break

        # Multi-instance support: unique DeviceID per hardware
        device_id = self._device_id

        for spec in specs:
            unit_id = spec.unit_id  # Use explicit unit_id, not position
            name = _translator.get_device_name(spec.spec_id)
            full_name = f"{_parameters()['Name']} - {name}"

            # Store spec in module-level storage for command handling
            _unit_specs[(device_id, unit_id)] = spec

            # Store spec for later use (device updates)
            self._device_specs[unit_id] = spec
            self._command_specs[spec.command][unit_id] = spec

            # Add description if available
            description = _translator.get_device_description(spec.spec_id)
            if description:
                spec.device_params["Description"] = description

            # Check if device exists
            if not domoticz_api.unit_exists(_devices(), device_id, unit_id):
                # Create new unit
                domoticz_api.create_unit(device_id, unit_id, full_name, spec.device_params)
                _logger.log(
                    f"Created device {unit_id} (spec_id={spec.spec_id}): {name}", DebugLevel.DEVICE
                )
            else:
                # Device exists - check if it should be updated
                existing_unit = domoticz_api.get_unit(_devices(), device_id, unit_id)
                current_name = existing_unit.Name
                needs_options_update = False
                needs_properties_update = False

                # Smart rename: only rename if current name's translation part
                # matches a known translation (not user-customized)
                # Device names have format: "{HardwareName} - {TranslatedName}"
                if current_name != full_name:
                    # Extract the translation part (after " - ")
                    if " - " in current_name:
                        translation_part = current_name.split(" - ", 1)[1]
                    else:
                        translation_part = current_name

                    # Check if translation part is a known translation
                    if _translator.is_known_device_name(translation_part, spec.spec_id):
                        existing_unit.Name = full_name
                        needs_properties_update = True
                        _logger.log(
                            f"Device {unit_id} (spec_id={spec.spec_id}) renamed: {current_name} -> {full_name}",
                            DebugLevel.DEVICE,
                        )

                # Update description if it's a known translation
                current_description = existing_unit.Description
                new_description = _translator.get_device_description(spec.spec_id)

                if (
                    current_description != new_description
                    and new_description
                    and _translator.is_known_description(current_description, spec.spec_id)
                ):
                    existing_unit.Description = new_description
                    needs_properties_update = True
                    _logger.log(
                        f"Device {unit_id} (spec_id={spec.spec_id}) description updated",
                        DebugLevel.DEVICE,
                    )

                # For selector switches: update LevelNames if they're known translations
                if spec.selector_options:
                    current_options = existing_unit.Options
                    if "LevelNames" in current_options:
                        current_level_names = current_options["LevelNames"]
                        new_level_names = _translator.translate_selector_options(
                            spec.selector_options
                        )

                        if current_level_names != new_level_names:
                            # Check if current options are known translations
                            current_items = current_level_names.split("|")
                            all_known = all(
                                _translator.is_known_selector_option(item, opt_key)
                                for item, opt_key in zip(
                                    current_items, spec.selector_options, strict=False
                                )
                            )

                            if all_known:
                                existing_unit.Options = {
                                    **current_options,
                                    "LevelNames": new_level_names,
                                }
                                needs_options_update = True
                                _logger.log(
                                    f"Device {unit_id} (spec_id={spec.spec_id}) selector options updated",
                                    DebugLevel.DEVICE,
                                )

                if needs_properties_update or needs_options_update:
                    # DomoticzEx requires UpdateProperties=True to update Name/Description
                    # and UpdateOptions=True to update Options
                    existing_unit.Update(
                        Log=False,
                        UpdateProperties=needs_properties_update,
                        UpdateOptions=needs_options_update,
                    )
                else:
                    _logger.log(
                        f"Device {unit_id} (spec_id={spec.spec_id}) already exists: {current_name}",
                        DebugLevel.DEVICE,
                    )

        _logger.log(f"Device creation complete: {len(specs)} devices", DebugLevel.BASIC)

    def update_device(self, unit_id: int, new_values: Dict[str, Any]) -> bool:
        """Update a single device with optimized tracking.

        Returns:
            True if device was updated, False if unchanged
        """
        if unit_id not in self._device_specs:
            return False

        spec = self._device_specs[unit_id]
        device_id = self._device_id

        if not domoticz_api.unit_exists(_devices(), device_id, unit_id):
            _logger.log(f"Device {unit_id} (spec_id={spec.spec_id}) not found", DebugLevel.DEVICE)
            return False

        unit = domoticz_api.get_unit(_devices(), device_id, unit_id)
        needs_update, reason, diff = self.update_tracker.needs_update(unit, new_values)

        if needs_update:
            if "nValue" in new_values:
                unit.nValue = new_values["nValue"]
            if "sValue" in new_values:
                unit.sValue = str(new_values["sValue"])
            unit.Update(Log=True)
            _logger.log(f"Updated {spec.spec_id}: {reason} - {diff}", DebugLevel.DEVICE)
            return True
        else:
            # Log tracker decisions at VERBOSE level for debugging update issues
            _logger.log(f"{spec.spec_id}: {reason}", DebugLevel.VERBOSE)
            return False

    def update_devices(self, command: str, data_store: DataStore) -> None:
        """Update all devices for a command type using shared data store.

        Args:
            command: The command type ('READ_CALCUL', 'READ_PARAMS')
            data_store: Dict mapping all command names to their data lists
        """
        _logger.log(f"Updating devices for {command}", DebugLevel.VERBOSE)

        data_list = data_store.get(command, [])
        if not data_list:
            _logger.log(f"No data in store for {command}", DebugLevel.COMMS)
            return

        # Track update statistics
        updated_count = 0
        unchanged_count = 0
        gated_count = 0

        for unit_id, spec in self._command_specs[command].items():
            try:
                address = spec.address
                result = spec.read_converter.convert(data_store, command, address, *spec.read_args)

                # Handle both tuple (gated converters) and dict (regular converters) returns
                if isinstance(result, tuple):
                    new_values, gate_reason = result
                else:
                    new_values, gate_reason = result, None

                # Skip update if converter returns None (gating active)
                if new_values is None:
                    gated_count += 1
                    if gate_reason:
                        _logger.log(
                            f"Skipping {spec.spec_id}: gated - {gate_reason}", DebugLevel.VERBOSE
                        )
                    else:
                        _logger.log(
                            f"Skipping {spec.spec_id}: converter returned None", DebugLevel.VERBOSE
                        )
                    continue

                if self.update_device(unit_id, new_values):
                    updated_count += 1
                else:
                    unchanged_count += 1
            except Exception as e:
                _logger.error(f"Error updating device {unit_id} (spec_id={spec.spec_id})", exc=e)

        # Log summary at BASIC level
        _logger.log(
            f"{command}: Updated {updated_count}, unchanged {unchanged_count}, gated {gated_count}",
            DebugLevel.BASIC,
        )

    def update_all(self) -> None:
        """Update all devices from all sources.

        Fetches all command data first into a shared data_store, then updates
        devices. This allows gated converters to access data from other commands
        (e.g., compressor frequency from READ_CALCUL for steady-state checks).

        Uses a single TCP connection for all read commands to avoid redundant
        handshakes (the Luxtronik controller supports sequential commands).
        """
        _logger.log("Full update starting", DebugLevel.VERBOSE)

        # Command codes mapping
        command_codes = {
            "READ_CALCUL": SocketCommand.READ_CALCUL,
            "READ_PARAMS": SocketCommand.READ_PARAMS,
        }

        # Phase 1: Fetch all command data on a single connection
        batch = [(code, 0, 0) for code in command_codes.values()]
        assert self.connection is not None  # set in onStart before any update runs
        batch_results = self.connection.execute_batch_with_retry(batch)

        data_store: DataStore = {}
        for command_name, code in command_codes.items():
            result = batch_results.get(code)
            if result:
                _, _, length, data_list = result
                if length > 0:
                    data_store[command_name] = data_list
                    _logger.log(f"Fetched {command_name}: {length} values", DebugLevel.VERBOSE)
                else:
                    _logger.log(f"No data received for {command_name}", DebugLevel.COMMS)
            else:
                _logger.log(f"No result for {command_name}", DebugLevel.COMMS)

        # Apply pump power compensation (modifies POWER_TOTAL in-place)
        self._apply_pump_compensation(data_store)

        # Phase 2: Update devices with shared data store
        for command in command_codes:
            if command in data_store:
                self.update_devices(command, data_store)

        _logger.log("Full update complete", DebugLevel.VERBOSE)

    def _validate_heartbeat(self, requested: int) -> int:
        """Validate and clamp heartbeat interval to safe range.

        Args:
            requested: User-requested heartbeat interval in seconds

        Returns:
            Clamped heartbeat value within ConfigLimits.HEARTBEAT_MIN and HEARTBEAT_MAX
        """
        if requested < ConfigLimits.HEARTBEAT_MIN:
            _logger.warning(
                f"Heartbeat interval {requested}s is below minimum. "
                f"Adjusted to {ConfigLimits.HEARTBEAT_MIN}s"
            )
            return ConfigLimits.HEARTBEAT_MIN
        elif requested > ConfigLimits.HEARTBEAT_MAX:
            _logger.warning(
                f"Heartbeat interval {requested}s exceeds maximum. "
                f"Adjusted to {ConfigLimits.HEARTBEAT_MAX}s"
            )
            return ConfigLimits.HEARTBEAT_MAX
        return requested

    def _configure_max_cop(self, raw_value: str) -> None:
        """Parse and apply the max COP limit to the COP converter.

        Args:
            raw_value: String from Parameters['Mode1'].
                       Empty string or '0' disables filtering.
                       Positive float sets the upper COP limit.
        """
        raw_value = raw_value.strip()

        if not raw_value or raw_value == "0":
            DeviceFactory._cop_converter.max_cop = None
            _logger.log("Max COP filter: disabled", DebugLevel.BASIC)
            return

        try:
            max_cop = float(raw_value)
            if max_cop <= 0:
                DeviceFactory._cop_converter.max_cop = None
                _logger.log("Max COP filter: disabled (non-positive value)", DebugLevel.BASIC)
            else:
                DeviceFactory._cop_converter.max_cop = max_cop
                _logger.log(f"Max COP filter: enabled at {max_cop:.1f}", DebugLevel.BASIC)
        except ValueError:
            DeviceFactory._cop_converter.max_cop = None
            _logger.warning(
                f"Invalid Max COP value '{raw_value}', filter disabled. "
                f"Expected a positive number."
            )

    def _configure_pump_compensation(self, mode4: str, mode5: str) -> None:
        """Parse pump power compensation settings.

        Args:
            mode4: '0' (off) or '1' (on)
            mode5: 'HUP_min,HUP_max,VBO_min,VBO_max' in watts
        """
        self._pump_compensation_enabled = mode4 == "1"
        self._pump_power_ranges = None

        if not self._pump_compensation_enabled:
            return

        try:
            parts = [float(x.strip()) for x in mode5.split(",")]
            if len(parts) != 4:
                raise ValueError(f"Expected 4 values, got {len(parts)}")
            if any(p < 0 for p in parts):
                raise ValueError("Negative power values not allowed")
            if parts[0] > parts[1] or parts[2] > parts[3]:
                raise ValueError("Min must not exceed max")
            self._pump_power_ranges = {
                "hup_min": parts[0],
                "hup_max": parts[1],
                "vbo_min": parts[2],
                "vbo_max": parts[3],
            }
            _logger.log(
                f"Pump power compensation enabled: HUP {parts[0]}-{parts[1]}W, VBO {parts[2]}-{parts[3]}W",
                DebugLevel.BASIC,
            )
        except (ValueError, IndexError) as e:
            _logger.error(f"Invalid pump power ranges '{mode5}': {e}. Disabling compensation.")
            self._pump_compensation_enabled = False

    @staticmethod
    def _estimate_pump_power(speed_pct: float, p_min: float, p_max: float) -> float:
        """Estimate pump power from speed percentage using quadratic model.

        Quadratic is a reasonable middle ground between linear (overestimates)
        and cubic affinity law (underestimates for ECM pumps).
        """
        if speed_pct <= 0:
            return 0.0
        fraction = max(0.0, min(1.0, speed_pct / 100.0))
        return p_min + (p_max - p_min) * fraction * fraction

    def _apply_pump_compensation(self, data_store: DataStore) -> None:
        """Add estimated pump power to compressor power reading in data store.

        Modifies POWER_TOTAL in-place so all downstream converters
        (power devices, COP calculators) automatically use the corrected value.
        """
        if not self._pump_compensation_enabled or self._pump_power_ranges is None:
            return

        calc_data = data_store.get("READ_CALCUL", [])
        if not calc_data:
            return

        try:
            ranges = self._pump_power_ranges
            compressor_power = float(calc_data[LuxtronikAddress.POWER_TOTAL])
            hup_speed = float(calc_data[LuxtronikAddress.HEATING_PUMP_SPEED])
            vbo_speed = float(calc_data[LuxtronikAddress.BRINE_PUMP_SPEED])

            hup_power = self._estimate_pump_power(hup_speed, ranges["hup_min"], ranges["hup_max"])
            vbo_power = self._estimate_pump_power(vbo_speed, ranges["vbo_min"], ranges["vbo_max"])

            total_power = compressor_power + hup_power + vbo_power
            # Intentional float into the int calc list: compensated power carries
            # sub-watt precision that InstantPowerConverter reads back as a float.
            calc_data[LuxtronikAddress.POWER_TOTAL] = total_power  # type: ignore[assignment]

            _logger.log(
                f"Pump compensation: compressor={compressor_power:.0f}W + "
                f"HUP({hup_speed:.0f}%)={hup_power:.0f}W + "
                f"VBO({vbo_speed:.0f}%)={vbo_power:.0f}W = {total_power:.0f}W",
                DebugLevel.DEVICE,
            )
        except (IndexError, TypeError, ValueError) as e:
            _logger.log(f"Pump compensation error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)

    def _check_cop_logging_setting(self) -> None:
        """Check and warn if COP logging setting is not optimal.

        For accurate COP averages over time, Domoticz should be configured with:
        Settings → Log History → 'Only add newly received values to the Log' = ENABLED

        When disabled (default), Domoticz fills in the last received value every 5 minutes,
        even when no new data is received. This means if the last COP sent was 10.2, that
        value gets logged every 5 minutes even when the heat pump is idle, skewing averages.

        When enabled, Domoticz only logs values when they are actually received, creating
        gaps during idle periods. This gives accurate daily/monthly COP averages.
        """
        settings = _settings()
        if settings is None:
            # Settings dictionary not available (older Domoticz version?)
            _logger.log(
                "Settings dictionary not available, skipping COP logging check", DebugLevel.VERBOSE
            )
            return

        try:
            # Settings dictionary is populated by Domoticz plugin framework
            # ShortLogAddOnlyNewValues: 1 = enabled (recommended), 0 = disabled
            # Note: Settings values are returned as strings
            setting_value = settings.get("ShortLogAddOnlyNewValues", "0")

            # Handle string comparison (Settings returns strings)
            if str(setting_value) == "1":
                _logger.log(
                    "COP Logging: 'Only add newly received values' is ENABLED (recommended)",
                    DebugLevel.BASIC,
                )
            else:
                # This is an important warning, always show it
                domoticz_api.log_status(
                    "COP Warning: For accurate COP averages, enable "
                    "Settings → Log History → 'Only add newly received values to the Log'. "
                    "Currently disabled - stale values will be logged during idle periods."
                )
        except Exception as e:
            # Other errors - log but don't fail
            _logger.log(f"Could not check COP logging setting: {e}", DebugLevel.VERBOSE)

    def onStart(self) -> None:
        """Initialize the plugin."""
        global _logger, _translator, _heartbeat_interval

        try:
            cfg = read_plugin_config(_parameters())

            # Setup debugging
            _logger.level = cfg.debug_level
            if _logger.level == DebugLevel.NONE:
                domoticz_api.set_debugging(0)  # Silence everything
            elif _logger.level == DebugLevel.ALL:
                domoticz_api.set_debugging(62)  # Plugin Debug() + framework device/connection info
            else:
                domoticz_api.set_debugging(2)  # Only plugin Debug() calls, no framework noise

            _logger.log("Plugin starting", DebugLevel.BASIC)

            # Bridge live logger/translator into context so extracted modules
            # (including TranslationManager.set_language below) can log through
            # the real logger instead of the pre-onStart null logger.
            import context

            context.logger = _logger
            context.translator = _translator

            # Initialize translations
            _translator.load_translations(
                DEVICE_TRANSLATIONS, SELECTOR_OPTIONS, WORKING_MODE_STATUSES
            )
            _translator.set_language(cfg.language)

            # Note: command handling is wired via the module-level onCommand()
            # function (see bottom of module). DomoticzEx dispatches commands to
            # Unit, then Device, then the module, so no custom class registration
            # is needed and it works reliably across plugin hot-reloads.

            # Generate unique DeviceID for multi-instance support
            self._device_id = self._get_device_id()
            _logger.log(f"DeviceID: {self._device_id}", DebugLevel.BASIC)

            # Initialize connection
            self.connection = ConnectionManager(cfg.address, cfg.port)

            # Set heartbeat with validation
            heartbeat = self._validate_heartbeat(cfg.heartbeat_raw)
            domoticz_api.set_heartbeat(heartbeat)
            _heartbeat_interval = heartbeat
            _logger.log(f"Heartbeat set to {heartbeat}s", DebugLevel.BASIC)

            # Bridge the computed heartbeat into context now that it's known.
            context.heartbeat_interval = _heartbeat_interval

            # Configure max COP limit
            self._configure_max_cop(cfg.max_cop_raw)
            self._configure_pump_compensation(cfg.pump_comp_enable_raw, cfg.pump_comp_params_raw)

            # Create devices (this also initializes available_writes)
            self.create_devices()

            # Enable writes only for known safe addresses
            # These are the ONLY addresses that can be written to
            allowed_write_addresses = [addr for addr in self.available_writes if addr != -1]
            self.connection.enable_writes(allowed_write_addresses)
            _logger.log(
                f"Write protection enabled for {len(allowed_write_addresses)} addresses",
                DebugLevel.BASIC,
            )

            # Initial update
            self.update_all()

            _logger.log("Plugin started successfully", DebugLevel.BASIC)

            # Check COP logging configuration
            # Settings dictionary is populated by Domoticz plugin framework
            self._check_cop_logging_setting()

        except ValueError as e:
            _logger.error("Configuration error during plugin start", exc=e)
        except Exception as e:
            _logger.error("Plugin start failed", exc=e)

    def onStop(self) -> None:
        """Clean up plugin resources."""
        global _plugin_ref, _unit_specs

        _logger.log("Plugin stopping", DebugLevel.BASIC)

        if self.connection:
            # Disable writes before closing
            self.connection.disable_writes()
            self.connection.close()

        # Clear specs first so any late onCommand() won't find a spec and exits early,
        # rather than finding a spec but having no plugin reference to execute against.
        _unit_specs.clear()
        _plugin_ref = None

        _logger.log("Plugin stopped", DebugLevel.BASIC)

    def onHeartbeat(self) -> None:
        """Handle periodic updates."""
        _logger.log("Heartbeat triggered", DebugLevel.VERBOSE)
        self.update_all()


# =============================================================================
# Plugin Instance and Callbacks
# =============================================================================


def _devices():
    """The framework-injected Devices mapping (None before onStart)."""
    return globals().get("Devices")


def _parameters() -> dict:
    """The framework-injected Parameters mapping (empty before onStart)."""
    return globals().get("Parameters") or {}


def _settings():
    """The framework-injected Settings mapping (None if unavailable)."""
    return globals().get("Settings")


_plugin = LuxtronikPlugin()


def onStart():
    try:
        _plugin.onStart()
    except Exception as e:
        domoticz_api.log_error(f"onStart failed ({type(e).__name__}: {e})")


def onStop():
    try:
        _plugin.onStop()
    except Exception as e:
        domoticz_api.log_error(f"onStop failed ({type(e).__name__}: {e})")


def onHeartbeat():
    try:
        _plugin.onHeartbeat()
    except Exception as e:
        domoticz_api.log_error(f"onHeartbeat failed ({type(e).__name__}: {e})")


def onCommand(DeviceID: str, Unit: int, Command: str, Level: int, Color: str) -> None:
    """Handle a command sent to one of the plugin's units.

    DomoticzEx dispatches commands to the Unit object, then the Device object,
    then this module-level function, in that order. Because the plugin uses the
    base DomoticzEx.Unit/Device classes (no custom subclass registration), the
    dispatch always falls through to here, which works reliably across plugin
    hot-reloads.

    SAFETY: All writes are validated against available_writes before sending to
    protect the heat pump's EEPROM from invalid values.
    """
    try:
        global _unit_specs, _plugin_ref

        spec = _unit_specs.get((DeviceID, Unit))

        if spec:
            _logger.log(
                f"Command received: spec_id={spec.spec_id}, Unit={Unit}, Command={Command}, Level={Level}",
                DebugLevel.COMMS,
            )
        else:
            _logger.log(
                f"Command received: DeviceID={DeviceID}, Unit={Unit}, Command={Command}, Level={Level}",
                DebugLevel.COMMS,
            )

        if not spec or not spec.write_converter or not _plugin_ref:
            _logger.log(f"No write handler for unit {Unit}", DebugLevel.COMMS)
            return

        try:
            # Convert command to value (Color is DomoticzEx's Hue payload)
            value = spec.write_converter.convert(
                Command=Command,
                Level=Level,
                Hue=Color,
                available_writes=_plugin_ref.available_writes,
            )

            # Get address from spec
            address = spec.address
            if isinstance(address, list):
                address = address[0]

            # CRITICAL SAFETY CHECK: Validate value against allowed writes
            # This protects the heat pump's EEPROM from invalid values
            if address not in _plugin_ref.available_writes:
                _logger.error(
                    f"WRITE BLOCKED: Address {address} not in available_writes (spec_id={spec.spec_id})"
                )
                return

            allowed_values = _plugin_ref.available_writes[address].get_val()
            if value not in allowed_values:
                _logger.error(
                    f"WRITE BLOCKED: Invalid value {value} for "
                    f"{_plugin_ref.available_writes[address].get_name()} (spec_id={spec.spec_id}). "
                    f"Allowed values: {allowed_values}"
                )
                return

            _logger.log(
                f"Writing validated value {value} to address {address} (spec_id={spec.spec_id})",
                DebugLevel.BASIC,
            )

            # Execute write command
            assert _plugin_ref.connection is not None  # set in onStart before commands dispatch
            _plugin_ref.connection.execute_with_retry(SocketCommand.WRITE_PARAMS, address, value)

            # Update all devices to reflect the change
            _plugin_ref.update_all()

        except Exception as e:
            _logger.error(f"Error processing command for spec_id={spec.spec_id}", exc=e)
    except Exception as e:
        domoticz_api.log_error(f"onCommand failed ({type(e).__name__}: {e})")
