"""
Luxtronik Heat Pump Controller Plugin v2 - Refactored for DomoticzEx Framework
Author: Rouzax, 2025 (Refactored)

<plugin key="luxtronikex" name="Luxtronik Heat Pump Controller v2" author="Rouzax" version="2.0.2">
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
        <p>For accurate COP (Coefficient of Performance) averages over time, enable: <b>Settings → Log History → 'Only add newly received values to the Log'</b></p>
        <p>When disabled, Domoticz fills in the last received value every 5 minutes even when the heat pump is idle, skewing COP averages. When enabled, no values are logged during idle periods, giving accurate daily/monthly averages.</p>
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

import DomoticzEx as Domoticz
import socket
import struct
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any, Tuple
from enum import IntFlag, auto
from abc import ABC, abstractmethod

from translations import Language, DEVICE_TRANSLATIONS, SELECTOR_OPTIONS, WORKING_MODE_STATUSES


# =============================================================================
# Debug Level Constants (using IntFlag for bitwise operations)
# =============================================================================
class DebugLevel(IntFlag):
    """Debug level flags for controlling log output.
    
    Levels:
        NONE (0):    Errors only (always logged)
        BASIC (1):   Lifecycle, summaries, write confirmations → Status()
        DEVICE (2):  Device updates (changes only) → Debug()
        COMMS (4):   Connections, protocol, commands → Debug()
        VERBOSE (8): Tracker details, data conversion → Debug()
        ALL (-1):    Everything
    """
    NONE = 0
    BASIC = 1       # Lifecycle, summaries, write confirmations
    DEVICE = 2      # Device updates (changes only)
    COMMS = 4       # Connections, protocol, commands
    VERBOSE = 8     # Tracker details, data conversion
    ALL = -1        # All debugging enabled


# =============================================================================
# Socket Commands
# =============================================================================
class SocketCommand:
    """Socket command codes for Luxtronik communication."""
    WRITE_PARAMS = 3002
    READ_PARAMS = 3003
    READ_CALCUL = 3004
    READ_VISIBI = 3005
    
    @classmethod
    def get_name(cls, code: int) -> str:
        """Get command name from code."""
        names = {
            cls.WRITE_PARAMS: 'WRITE_PARAMS',
            cls.READ_PARAMS: 'READ_PARAMS',
            cls.READ_CALCUL: 'READ_CALCUL',
            cls.READ_VISIBI: 'READ_VISIBI'
        }
        return names.get(code, f'UNKNOWN({code})')


# =============================================================================
# Luxtronik Address Constants
# =============================================================================
class LuxtronikAddress:
    """Named constants for Luxtronik protocol addresses.
    
    These map to specific data indices in the Luxtronik protocol.
    Using named constants improves code readability and maintainability.
    """
    # READ_CALCUL addresses (sensor readings)
    HEAT_SUPPLY_TEMP = 10
    HEAT_RETURN_TEMP = 11
    RETURN_TEMP_TARGET = 12
    HOT_GAS_TEMP = 14
    OUTSIDE_TEMP = 15
    OUTSIDE_TEMP_AVG = 16
    DHW_TEMP = 17
    SOURCE_IN_TEMP = 19
    SOURCE_OUT_TEMP = 20
    MC1_TEMP = 21
    MC1_TEMP_TARGET = 22
    MC2_TEMP = 24
    MC2_TEMP_TARGET = 25
    COMPRESSOR_RUNTIME = 56        # ID_WEB_Zaehler_BetrZeitVD1 - seconds
    COMPRESSOR_STARTS = 57         # ID_WEB_Zaehler_BetrZeitImpVD1 - count
    HEATING_RUNTIME = 64           # ID_WEB_Zaehler_BetrZeitHz - heating mode seconds
    DHW_RUNTIME = 65               # ID_WEB_Zaehler_BetrZeitBW - DHW mode seconds
    COOLING_RUNTIME = 66           # ID_WEB_Zaehler_BetrZeitKue - cooling mode seconds
    CURRENT_CYCLE_TIME = 67        # Time_WPein_akt - current cycle duration in seconds
    WORKING_MODE = 80
    ERROR_COUNT = 105              # ID_WEB_AnzahlFehlerInSpeicher - stored error count
    COOLING_PERMITTED = 146        # ID_WEB_FreigabKuehl - cooling release/permitted flag
    HEATING_FLOW = 155             # ID_WEB_WMZ_Durchfluss - heating circuit flow (L/h)
    SOURCE_FLOW = 173              # ID_WEB_Durchfluss_WQ - source/brine circuit flow (L/h)
    SUCTION_TEMP = 176
    DISCHARGE_TEMP = 177           # ID_WEB_LIN_VDH - discharge line temp
    SUPERHEAT = 178
    HIGH_PRESSURE = 180
    LOW_PRESSURE = 181
    BRINE_PUMP_SPEED = 183
    ROOM_TEMP = 227
    ROOM_TEMP_TARGET = 228
    COMPRESSOR_FREQ = 231
    EVAPORATING_TEMP = 232         # Vapourisation_Temperature
    CONDENSING_TEMP = 233          # Liquefaction_Temperature
    TARGET_FREQUENCY = 236         # ID_WEB_Freq_VD_Soll - controller target frequency
    COMPRESSOR_FREQ_MIN = 237      # ID_WEB_Freq_VD_Min - minimum frequency target
    COMPRESSOR_FREQ_MAX = 238      # Freq_VD_Max - maximum frequency
    SOURCE_SPREAD_TARGET = 239     # VBO_Temp_Spread_Soll
    SOURCE_SPREAD_ACTUAL = 240     # VBO_Temp_Spread_Ist
    HEATING_PUMP_SPEED = 241
    HEATING_SPREAD_TARGET = 242    # HUP_Temp_Spread_Soll
    HEATING_SPREAD_ACTUAL = 243    # HUP_Temp_Spread_Ist
    HEAT_OUTPUT = 257
    PASSIVE_COOLING_FLAG = 259
    POWER_TOTAL = 268
    
    # READ_PARAMS addresses (configuration parameters)
    TEMP_OFFSET = 1
    HEATING_MODE = 3
    HOT_WATER_MODE = 4
    DHW_TEMP_TARGET = 105
    COOLING_ENABLED = 108
    DHW_POWER_MODE = 1052
    ROOM_TEMP_SETPOINT = 1148


# =============================================================================
# Configuration Constants
# =============================================================================
class ConfigLimits:
    """Configuration limits for plugin parameters."""
    HEARTBEAT_MIN = 10
    HEARTBEAT_MAX = 60
    HEARTBEAT_DEFAULT = 20


# =============================================================================
# Debug Logger (Single Responsibility)
# =============================================================================
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
            Domoticz.Status(message)
        else:
            # Add level prefix for clarity in logs
            prefix = {
                DebugLevel.DEVICE: "[DEVICE]",
                DebugLevel.COMMS: "[COMMS]",
                DebugLevel.VERBOSE: "[VERBOSE]",
            }.get(level, "[DEBUG]")
            Domoticz.Debug(f"{prefix} {message}")
    
    def error(self, message: str, exc: Exception = None) -> None:
        """Log an error message. Always logs regardless of level.
        
        Args:
            message: The error message
            exc: Optional exception to include type information
        """
        if exc:
            Domoticz.Error(f"{message} ({type(exc).__name__}: {exc})")
        else:
            Domoticz.Error(message)
    
    def warning(self, message: str) -> None:
        """Log a warning message. Always logs regardless of level."""
        Domoticz.Status(f"Warning: {message}")


# Global logger instance
_logger = DebugLogger()


# =============================================================================
# Translation Manager (Single Responsibility)
# =============================================================================
class TranslationManager:
    """Manages translations for the plugin.
    
    Uses spec_id as the primary key for device translations, eliminating the
    need for separate name_key and description key mappings.
    """
    
    LANGUAGE_MAP = {
        '0': Language.ENGLISH,
        '1': Language.POLISH,
        '2': Language.DUTCH,
        '3': Language.GERMAN,
        '4': Language.FRENCH
    }
    
    def __init__(self):
        self._device_translations: Dict[str, Dict] = {}
        self._selector_options: Dict[str, Dict[Language, str]] = {}
        self._working_mode_statuses: Dict[str, Dict[Language, str]] = {}
        self._current_language = Language.ENGLISH
    
    def set_language(self, language_code: str) -> None:
        """Set current language from plugin parameter."""
        if language_code not in self.LANGUAGE_MAP:
            _logger.warning(f"Unknown language code '{language_code}', falling back to English")
            language = Language.ENGLISH
        else:
            language = self.LANGUAGE_MAP[language_code]
        
        self._current_language = language
        _logger.log(f"Language set to: {language.name}", DebugLevel.BASIC)
    
    def load_translations(self, device_translations: Dict, 
                          selector_options: Dict, 
                          working_mode_statuses: Dict) -> None:
        """Load translations from data dictionaries."""
        self._device_translations = device_translations
        self._selector_options = selector_options
        self._working_mode_statuses = working_mode_statuses
    
    def get_device_name(self, spec_id: str) -> str:
        """Get device name for current language by spec_id."""
        if spec_id not in self._device_translations:
            return spec_id
        
        names = self._device_translations[spec_id].get('name', {})
        return names.get(self._current_language, 
                        names.get(Language.ENGLISH, spec_id))
    
    def get_device_name_for_language(self, spec_id: str, language: Language) -> str:
        """Get device name for a specific language by spec_id."""
        if spec_id not in self._device_translations:
            return spec_id
        
        names = self._device_translations[spec_id].get('name', {})
        return names.get(language, names.get(Language.ENGLISH, spec_id))
    
    def get_device_description(self, spec_id: str) -> str:
        """Get device description for current language by spec_id."""
        if spec_id not in self._device_translations:
            return ""
        
        descs = self._device_translations[spec_id].get('description', {})
        return descs.get(self._current_language, 
                        descs.get(Language.ENGLISH, ""))
    
    def get_device_description_for_language(self, spec_id: str, language: Language) -> str:
        """Get device description for a specific language by spec_id."""
        if spec_id not in self._device_translations:
            return ""
        
        descs = self._device_translations[spec_id].get('description', {})
        return descs.get(language, descs.get(Language.ENGLISH, ""))
    
    def is_known_device_name(self, name: str, spec_id: str) -> bool:
        """Check if name matches any known translation for the spec_id.
        
        Used to determine if a device name can be safely renamed (it's a known
        translation) vs user-customized (should be left alone).
        """
        if spec_id not in self._device_translations:
            return False
        
        names = self._device_translations[spec_id].get('name', {})
        return name in names.values()
    
    def is_known_description(self, description: str, spec_id: str) -> bool:
        """Check if description matches any known translation for spec_id."""
        if spec_id not in self._device_translations:
            return False
        
        descs = self._device_translations[spec_id].get('description', {})
        return description in descs.values()
    
    def get_selector_option(self, option_key: str) -> str:
        """Get selector option text for current language."""
        if option_key not in self._selector_options:
            return option_key
        
        options = self._selector_options[option_key]
        return options.get(self._current_language, 
                          options.get(Language.ENGLISH, option_key))
    
    def get_selector_option_for_language(self, option_key: str, language: Language) -> str:
        """Get selector option text for a specific language."""
        if option_key not in self._selector_options:
            return option_key
        
        options = self._selector_options[option_key]
        return options.get(language, options.get(Language.ENGLISH, option_key))
    
    def translate_selector_options(self, options: List[str]) -> str:
        """Translate selector switch options and join with pipes."""
        return '|'.join(self.get_selector_option(opt) for opt in options)
    
    def is_known_selector_option(self, text: str, option_key: str) -> bool:
        """Check if text matches any known translation for selector option."""
        if option_key not in self._selector_options:
            return False
        
        options = self._selector_options[option_key]
        return text in options.values()
    
    def get_working_mode_status(self, status_key: str) -> str:
        """Get working mode status text for current language."""
        if status_key not in self._working_mode_statuses:
            return status_key
        
        statuses = self._working_mode_statuses[status_key]
        return statuses.get(self._current_language, 
                          statuses.get(Language.ENGLISH, status_key))


# Global translation manager
_translator = TranslationManager()


def translate(key: str) -> str:
    """Shorthand for working mode status translation lookup."""
    return _translator.get_working_mode_status(key)


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
    - If min_target_freq <= 0: System is idle, gate closed
    - If actual_freq < min_target_freq: System is ramping up, gate closed
    - Otherwise: System at steady-state, gate open
    """
    
    def check_steady_state(self, data_store: DataStore) -> Optional[str]:
        """Check if compressor is at steady-state operating speed.
        
        Returns:
            None if gate passes (steady-state operation)
            String with reason if gated (idle or ramping)
        """
        calc_data = data_store.get('READ_CALCUL', [])
        
        # Ensure we have enough data
        if len(calc_data) <= max(LuxtronikAddress.COMPRESSOR_FREQ, LuxtronikAddress.COMPRESSOR_FREQ_MIN):
            return "insufficient data"
        
        try:
            actual_freq = float(calc_data[LuxtronikAddress.COMPRESSOR_FREQ])
            min_target_freq = float(calc_data[LuxtronikAddress.COMPRESSOR_FREQ_MIN])
            
            # Idle state: min_target is 0
            if min_target_freq <= 0:
                return f"idle (freq={actual_freq:.0f} Hz, min_target=0)"
            
            # Startup ramp: actual hasn't reached minimum target yet
            if actual_freq < min_target_freq:
                return f"ramping (freq={actual_freq:.0f} Hz < {min_target_freq:.0f} Hz)"
            
            # Gate passes - steady-state operation
            return None
            
        except (IndexError, TypeError, ValueError) as e:
            return f"error checking frequency: {e}"


class FloatConverter(DataConverter):
    """Converts data to float value."""
    
    def convert(self, data_store: DataStore, command: str, address: int, divider: float = 10) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            value = float(data_list[address]) / divider
            return {'sValue': str(value)}
        except (IndexError, TypeError, ZeroDivisionError) as e:
            _logger.log(f"FloatConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'sValue': '0.0'}


class NumberConverter(DataConverter):
    """Converts data to integer value."""
    
    def convert(self, data_store: DataStore, command: str, address: int, divider: float = 1.0) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            value = int(data_list[address] / divider)
            return {'nValue': value}
        except (IndexError, TypeError, ZeroDivisionError) as e:
            _logger.log(f"NumberConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
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
                _logger.log(f"Selector value {value} not in mapping {mapping}, defaulting to 0", 
                           DebugLevel.VERBOSE)
                level = 0
            return {'nValue': level, 'sValue': str(level)}
        except (IndexError, ValueError) as e:
            _logger.error(f"SelectorSwitchConverter error", exc=e)
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
            _logger.log(f"InstantPowerConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
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
            _logger.log(f"InstantPowerSplitConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'sValue': "0.0"}


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
            _logger.log(f"COPCalculatorConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
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
            _logger.log(f"TextStateConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'nValue': 0, 'sValue': translate('Idle')}


class TempDiffConverter(DataConverter):
    """Calculates temperature difference between two sensors."""
    
    def convert(self, data_store: DataStore, command: str, indices: List[int], divider: float) -> ConvertResult:
        try:
            data_list = data_store.get(command, [])
            temp1 = float(data_list[indices[0]]) / divider
            temp2 = float(data_list[indices[1]]) / divider
            return {'sValue': str(round(temp1 - temp2, 1))}
        except (IndexError, TypeError, ZeroDivisionError) as e:
            _logger.log(f"TempDiffConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
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
            _logger.log(f"GatedFloatConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return (None, f"error: {type(e).__name__}")


class GatedTempDiffConverter(SteadyStateGateMixin, DataConverter):
    """Temperature difference converter with steady-state gating.
    
    Returns tuple (result, gate_reason) - result is None when gated.
    Used for brine and heating ΔT which approach zero when loops equilibrate.
    """
    
    def convert(self, data_store: DataStore, command: str, indices: List[int], divider: float) -> GatedResult:
        # Allow updates during passive cooling (pumps running, ΔT is meaningful)
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
            _logger.log(f"GatedTempDiffConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return (None, f"error: {type(e).__name__}")


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
            _logger.log(f"RuntimeHoursConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
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
            _logger.log(f"IntegerValueConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
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
            _logger.log(f"BooleanSwitchConverter error at address {address}: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return {'nValue': 0, 'sValue': 'Off'}


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
            _logger.log(f"CapacityConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
            return (None, f"error: {type(e).__name__}")


class CycleTracker:
    """Tracks compressor cycle completions by detecting timer resets.
    
    The current cycle timer (Time_WPein_akt, index 67) resets to 0 when 
    a new cycle starts. By tracking the previous value, we detect completions:
    
        Previous: 1920s (32 min) → Current: 60s (1 min) = RESET DETECTED
    
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
            # Previous value was the completed cycle's duration
            completed_minutes = self.previous_cycle_seconds / 60
            
            # Ignore very short "cycles" (glitches, restarts)
            if completed_minutes >= self.MIN_CYCLE_MINUTES:
                result = {'nValue': 0, 'sValue': f"{completed_minutes:.0f}"}
                _logger.log(
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
            _logger.log(f"LastCycleConverter error: {type(e).__name__}: {e}", DebugLevel.VERBOSE)
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
                _logger.error(f"Level {Level} (index {index}) out of range for writes_idx {self.writes_idx}")
                return values[0] if values else 0
        except (KeyError, IndexError, TypeError) as e:
            _logger.error(f"AvailableWritesConverter error", exc=e)
            return 0


# =============================================================================
# Field Definition
# =============================================================================
@dataclass
class Field:
    """Represents a writable field with allowed values."""
    name: str = 'Unknown'
    values: List[int] = field(default_factory=list)
    
    def get_name(self) -> str:
        return self.name
    
    def get_val(self) -> List[int]:
        return self.values


# =============================================================================
# Device Specification (Data Transfer Object)
# =============================================================================
@dataclass
class DeviceSpec:
    """Specification for creating a Domoticz device.
    
    Attributes:
        unit_id: Stable, explicit Unit number (never changes even if list order changes)
        spec_id: Human-readable identifier used for debugging and translation lookup
        command: The Luxtronik command type (READ_CALCUL, READ_PARAMS, etc.)
        address: Protocol address or list of addresses
        read_converter: Converter for reading data
        read_args: Additional arguments for the read converter
        device_params: Domoticz device creation parameters
        write_converter: Optional converter for writing data
        selector_options: Optional list of untranslated option keys for selector switches
    """
    unit_id: int
    spec_id: str  # Also serves as translation key
    command: str
    address: Any  # int or List[int]
    read_converter: DataConverter
    read_args: Tuple = ()
    device_params: Dict[str, Any] = field(default_factory=dict)
    write_converter: Optional[WriteConverter] = None
    selector_options: Optional[List[str]] = None


# =============================================================================
# Device Update Tracker (Single Responsibility)
# =============================================================================
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
        if hasattr(unit, 'SubType') and unit.Type == 243 and unit.SubType == 19:
            self._device_type_cache[device_id] = False
            return False
        
        is_graphing = unit.Type in self.GRAPHING_TYPES
        self._device_type_cache[device_id] = is_graphing
        return is_graphing
    
    def _normalize_value(self, value_str: str) -> str:
        """Normalize a value for comparison."""
        if not value_str:
            return ""
        
        value_str = value_str.strip()
        if ';' in value_str:
            value_str = value_str.split(';')[0].strip()
        
        try:
            float_value = float(value_str)
            decimals = max(len(value_str.split('.')[1]) if '.' in value_str else 0, 1)
            return f"{float_value:.{decimals}f}"
        except ValueError:
            return value_str.lower()
    
    def needs_update(self, unit, new_values: Dict) -> Tuple[bool, str, str]:
        """Determine if a unit needs updating."""
        current_time = time.time()
        device_id = unit.ID
        is_graphing = self._is_graphing_device(unit)
        
        # Compare values
        current_nvalue = unit.nValue
        current_svalue = str(unit.sValue)
        
        values_changed = False
        diff_message = ""
        
        if 'nValue' in new_values and new_values['nValue'] != current_nvalue:
            values_changed = True
            diff_message += f"nValue: {current_nvalue} -> {new_values['nValue']}; "
        
        if 'sValue' in new_values:
            norm_current = self._normalize_value(current_svalue)
            norm_new = self._normalize_value(new_values['sValue'])
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


# =============================================================================
# Connection Manager (Single Responsibility)
# =============================================================================
class ConnectionManager:
    """Manages socket connections to the Luxtronik controller.
    
    SECURITY NOTE: The Luxtronik protocol uses plain TCP without encryption
    or authentication. This is a hardware limitation. Ensure your heat pump
    is on a trusted network and not exposed to the internet.
    
    SAFETY: This class includes protection against unintended writes.
    Write operations require explicit validation before sending.
    """
    
    TIMEOUT = 5
    MAX_ATTEMPTS = 2  # 1 initial attempt + 1 retry
    
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self._socket: Optional[socket.socket] = None
        self._write_enabled = False  # Write protection flag
        self._allowed_write_addresses: set = set()  # Addresses that can be written
    
    def enable_writes(self, allowed_addresses: List[int]) -> None:
        """Enable write operations for specific addresses only.
        
        This must be called during plugin initialization to allow any writes.
        """
        self._allowed_write_addresses = set(allowed_addresses)
        self._write_enabled = True
        _logger.log(f"Writes enabled for addresses: {allowed_addresses}", DebugLevel.BASIC)
    
    def disable_writes(self) -> None:
        """Disable all write operations (safety lockout)."""
        self._write_enabled = False
        self._allowed_write_addresses.clear()
        _logger.log("Writes disabled", DebugLevel.BASIC)
    
    def connect(self) -> bool:
        """Establish connection to the controller."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(self.TIMEOUT)
            self._socket.connect((self.host, self.port))
            _logger.log(f"Connected to {self.host}:{self.port}", DebugLevel.COMMS)
            return True
        except socket.error as e:
            _logger.error(f"Connection failed to {self.host}:{self.port}", exc=e)
            self.close()
            return False
        except Exception as e:
            _logger.error(f"Unexpected connection error to {self.host}:{self.port}", exc=e)
            self.close()
            return False
    
    def close(self) -> None:
        """Close the connection."""
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None
    
    def _recv_exact(self, num_bytes: int) -> bytes:
        """Receive exactly num_bytes from the socket.
        
        TCP does not guarantee that recv() returns all requested bytes in a
        single call. This method loops until the full payload is received,
        preventing silent data corruption from partial reads.
        
        Raises:
            socket.error: If the connection is closed before all bytes arrive
        """
        data = b''
        while len(data) < num_bytes:
            chunk = self._socket.recv(num_bytes - len(data))
            if not chunk:
                raise socket.error("Connection closed during receive")
            data += chunk
        return data
    
    def send_command(self, command: int, address: int = 0, value: int = 0) -> Optional[Tuple[int, int, int, List[int]]]:
        """Send a command and receive response.
        
        SAFETY: Write commands (WRITE_PARAMS) are blocked unless:
        1. Writes are enabled via enable_writes()
        2. The address is in the allowed list
        """
        if not self._socket:
            return None
        
        # SAFETY CHECK: Block unauthorized write attempts
        if command == SocketCommand.WRITE_PARAMS:
            if not self._write_enabled:
                _logger.error("WRITE BLOCKED: Writes not enabled")
                return None
            if address not in self._allowed_write_addresses:
                _logger.error(f"WRITE BLOCKED: Address {address} not in allowed list")
                return None
            _logger.log(f"WRITE AUTHORIZED: address={address}, value={value}", DebugLevel.BASIC)
        
        try:
            # Send command and address
            self._socket.send(struct.pack('!i', command))
            self._socket.send(struct.pack('!i', address))
            
            # Send value for write commands
            if command == SocketCommand.WRITE_PARAMS:
                self._socket.send(struct.pack('!i', value))
            
            # Verify command echo
            received = struct.unpack('!i', self._recv_exact(4))[0]
            if received != command:
                raise Exception(f"Command verification failed: sent {command}, received {received}")
            
            # Process response
            stat = 0
            length = 0
            data_list = []
            
            if command == SocketCommand.READ_PARAMS:
                length = struct.unpack('!i', self._recv_exact(4))[0]
            elif command == SocketCommand.READ_CALCUL:
                stat = struct.unpack('!i', self._recv_exact(4))[0]
                length = struct.unpack('!i', self._recv_exact(4))[0]
            
            if length > 0:
                data_list = [struct.unpack('!i', self._recv_exact(4))[0] for _ in range(length)]
            
            _logger.log(f"{SocketCommand.get_name(command)}: Received {length} values", DebugLevel.COMMS)
            return command, stat, length, data_list
            
        except socket.error as e:
            _logger.error(f"Socket error during command", exc=e)
            return None
        except Exception as e:
            _logger.error(f"Command failed", exc=e)
            return None
    
    def execute_with_retry(self, command: int, address: int = 0, value: int = 0) -> Tuple[int, int, int, List[int]]:
        """Execute a single command with retry logic.
        
        Opens a connection, sends one command, then closes. Used for
        single-command operations like writes.
        """
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                if self.connect():
                    result = self.send_command(command, address, value)
                    if result:
                        return result
            except socket.error as e:
                if attempt == 0:
                    _logger.log(f"Socket error (retrying): {type(e).__name__}: {e}", DebugLevel.COMMS)
            finally:
                self.close()
        
        _logger.error(f"Command failed after {self.MAX_ATTEMPTS} attempts")
        return command, 0, 0, []
    
    def execute_batch_with_retry(self, commands: List[Tuple[int, int, int]]) -> Dict[int, Tuple[int, int, int, List[int]]]:
        """Execute multiple commands on a single connection with retry logic.
        
        The Luxtronik controller supports sequential commands on one TCP
        connection. This avoids redundant TCP handshakes when multiple
        read commands are needed (e.g., READ_CALCUL + READ_PARAMS).
        
        Args:
            commands: List of (command, address, value) tuples to execute.
            
        Returns:
            Dict mapping command code to its (command, stat, length, data_list)
            result. Failed commands are omitted from the dict.
        """
        for attempt in range(self.MAX_ATTEMPTS):
            try:
                if not self.connect():
                    continue
                
                results: Dict[int, Tuple[int, int, int, List[int]]] = {}
                all_ok = True
                
                for command, address, value in commands:
                    result = self.send_command(command, address, value)
                    if result:
                        results[command] = result
                    else:
                        all_ok = False
                        break  # Connection likely broken, retry from scratch
                
                if all_ok:
                    return results
                    
            except socket.error as e:
                if attempt == 0:
                    _logger.log(f"Socket error during batch (retrying): {type(e).__name__}: {e}", DebugLevel.COMMS)
            finally:
                self.close()
        
        _logger.error(f"Batch command failed after {self.MAX_ATTEMPTS} attempts")
        return {}


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
_unit_specs: Dict[Tuple[str, int], 'DeviceSpec'] = {}  # (DeviceID, Unit) -> Spec
_plugin_ref: Optional['LuxtronikPlugin'] = None  # Reference to plugin instance


# =============================================================================
# Custom Unit Class for DomoticzEx
# =============================================================================
class LuxtronikUnit(Domoticz.Unit):
    """Custom Unit class with command handling.
    
    Uses **kwargs to pass parameters directly to parent without
    interfering with Domoticz's TypeName auto-detection.
    """
    
    def __init__(self, Name: str, DeviceID: str, Unit: int, **kwargs):
        # Pass all kwargs directly to parent - don't override with defaults
        # This allows TypeName='Selector Switch' to properly set Type/Subtype/Switchtype
        super().__init__(Name, DeviceID, Unit, **kwargs)
    
    def onCommand(self, Command: str, Level: int, Hue: int) -> None:
        """Handle commands sent to this unit.
        
        SAFETY: All writes are validated against available_writes before sending
        to protect the heat pump's EEPROM from invalid values.
        """
        global _unit_specs, _plugin_ref
        
        # Get DeviceID from parent device
        device_id = self.Parent.DeviceID if hasattr(self, 'Parent') and self.Parent else "luxtronik"
        unit_id = self.Unit
        
        # Look up spec from module-level storage
        spec_key = (device_id, unit_id)
        spec = _unit_specs.get(spec_key)
        
        if spec:
            _logger.log(f"Command received: spec_id={spec.spec_id}, Unit={unit_id}, Command={Command}, Level={Level}", 
                       DebugLevel.COMMS)
        else:
            _logger.log(f"Command received: DeviceID={device_id}, Unit={unit_id}, Command={Command}, Level={Level}", 
                       DebugLevel.COMMS)
        
        if not spec or not spec.write_converter or not _plugin_ref:
            _logger.log(f"No write handler for unit {unit_id}", DebugLevel.COMMS)
            return
        
        try:
            # Convert command to value
            value = spec.write_converter.convert(
                Command=Command, Level=Level, Hue=Hue,
                available_writes=_plugin_ref.available_writes
            )
            
            # Get address from spec
            address = spec.address
            if isinstance(address, list):
                address = address[0]
            
            # CRITICAL SAFETY CHECK: Validate value against allowed writes
            # This protects the heat pump's EEPROM from invalid values
            if address not in _plugin_ref.available_writes:
                _logger.error(f"WRITE BLOCKED: Address {address} not in available_writes (spec_id={spec.spec_id})")
                return
            
            allowed_values = _plugin_ref.available_writes[address].get_val()
            if value not in allowed_values:
                _logger.error(
                    f"WRITE BLOCKED: Invalid value {value} for "
                    f"{_plugin_ref.available_writes[address].get_name()} (spec_id={spec.spec_id}). "
                    f"Allowed values: {allowed_values}"
                )
                return
            
            _logger.log(f"Writing validated value {value} to address {address} (spec_id={spec.spec_id})", DebugLevel.BASIC)
            
            # Execute write command
            _plugin_ref.connection.execute_with_retry(
                SocketCommand.WRITE_PARAMS, address, value
            )
            
            # Update all devices to reflect the change
            _plugin_ref.update_all()
            
        except Exception as e:
            _logger.error(f"Error processing command for spec_id={spec.spec_id}", exc=e)
    
    def onDeviceAdded(self) -> None:
        """Called when device is added externally."""
        _logger.log(f"Unit added: {self.Name}", DebugLevel.DEVICE)
    
    def onDeviceModified(self) -> None:
        """Called when device is modified externally."""
        _logger.log(f"Unit modified: {self.Name}", DebugLevel.DEVICE)
    
    def onDeviceRemoved(self) -> None:
        """Called when device is removed externally."""
        _logger.log(f"Unit removed: {self.Name}", DebugLevel.DEVICE)


# =============================================================================
# Custom Device Class for DomoticzEx
# =============================================================================
class LuxtronikDevice(Domoticz.Device):
    """Custom Device class for grouping units."""
    
    def __init__(self, DeviceID: str):
        super().__init__(DeviceID)
    
    def onCommand(self, Unit: int, Command: str, Level: int, Hue: int) -> None:
        """Handle commands at device level - delegate to unit."""
        if Unit in self.Units:
            unit = self.Units[Unit]
            if hasattr(unit, 'onCommand'):
                unit.onCommand(Command, Level, Hue)


# =============================================================================
# Register custom Device and Unit classes with DomoticzEx
# IMPORTANT: This MUST be at module level (not inside onStart) so that
# existing devices are loaded using the custom classes with their callbacks
# =============================================================================
Domoticz.Register(Device=LuxtronikDevice, Unit=LuxtronikUnit)


# =============================================================================
# Device Factory (Factory Pattern)
# =============================================================================
class DeviceFactory:
    """Factory for creating device specifications."""
    
    # Converter instances (flyweight pattern)
    _float_converter = FloatConverter()
    _gated_float_converter = GatedFloatConverter()
    _number_converter = NumberConverter()
    _selector_converter = SelectorSwitchConverter()
    _instant_power_converter = InstantPowerConverter()
    _instant_power_split_converter = InstantPowerSplitConverter()
    _cop_converter = COPCalculatorConverter()
    _text_state_converter = TextStateConverter()
    _temp_diff_converter = TempDiffConverter()
    _gated_temp_diff_converter = GatedTempDiffConverter()
    _command_to_number = CommandToNumberConverter()
    _runtime_hours_converter = RuntimeHoursConverter()
    _integer_value_converter = IntegerValueConverter()
    _boolean_switch_converter = BooleanSwitchConverter()
    _capacity_converter = CapacityConverter()
    _last_cycle_converter = LastCycleConverter()
    
    @classmethod
    def create_temperature_device(cls, unit_id: int, spec_id: str, command: str, 
                                   address: int,
                                   divider: float = 10, used: int = 1) -> DeviceSpec:
        """Create a temperature sensor device specification."""
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._float_converter,
            read_args=(divider,),
            device_params={'TypeName': 'Temperature', 'Used': used}
        )
    
    @classmethod
    def create_custom_device(cls, unit_id: int, spec_id: str, command: str, 
                             address: int,
                             unit: str, divider: float = 1, used: int = 1,
                             gated: bool = False, precision: str = '1',
                             image: Optional[int] = None) -> DeviceSpec:
        """Create a custom sensor device specification.
        
        Args:
            unit_id: Domoticz unit ID
            spec_id: Unique specification identifier (also used for translation)
            command: Luxtronik command type
            address: Protocol address for data
            unit: Unit string for display (e.g., 'K', 'bar', 'Hz')
            divider: Value divider for conversion
            used: Device used flag (default 1)
            gated: If True, use steady-state gating to skip updates when idle
            precision: Axis divisor for graph display (default '1', use '0.1' for finer resolution)
            image: Optional icon image number
        """
        converter = cls._gated_float_converter if gated else cls._float_converter
        params = {
            'TypeName': 'Custom',
            'Used': used,
            'Options': {'Custom': f'{precision};{unit}'}
        }
        if image is not None:
            params['Image'] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=converter,
            read_args=(divider,),
            device_params=params
        )
    
    @classmethod
    def create_setpoint_device(cls, unit_id: int, spec_id: str, command: str, 
                                address: int,
                                divider: float = 10, write_divider: float = 0.1,
                                min_val: str = "-5", max_val: str = "5",
                                step: str = "0.5", used: int = 0) -> DeviceSpec:
        """Create a setpoint device specification."""
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._float_converter,
            read_args=(divider,),
            device_params={
                'Type': 242,
                'Subtype': 1,
                'Used': used,
                'Options': {
                    'ValueStep': step,
                    'ValueMin': min_val,
                    'ValueMax': max_val,
                    'ValueUnit': '°C'
                }
            },
            write_converter=LevelWithDividerConverter(write_divider)
        )
    
    @classmethod
    def create_selector_device(cls, unit_id: int, spec_id: str, command: str, 
                               address: int,
                               options: List[str], mapping: List[int],
                               writes_idx: int, used: int = 1,
                               image: int = 15) -> DeviceSpec:
        """Create a selector switch device specification.
        
        Args:
            image: Icon image number (default 15 = heat pump). Common options:
                   15 = heat pump, 16 = fire, 7 = fan, 9 = door, etc.
        """
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._selector_converter,
            read_args=(mapping,),
            device_params={
                'TypeName': 'Selector Switch',
                'Image': image,
                'Used': used,
                'Options': {
                    'LevelActions': '|' * len(options),
                    'LevelNames': _translator.translate_selector_options(options),
                    'LevelOffHidden': 'false',
                    'SelectorStyle': '1'
                }
            },
            write_converter=AvailableWritesConverter(10, writes_idx),
            selector_options=options  # Store for language change updates
        )
    
    @classmethod
    def create_switch_device(cls, unit_id: int, spec_id: str, command: str, 
                              address: int,
                              used: int = 1, image: int = 16) -> DeviceSpec:
        """Create a switch device specification.
        
        Args:
            image: Icon image number (default 16 = fire). Common options:
                   15 = heat pump, 16 = fire, 7 = fan, 9 = door, etc.
        """
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._number_converter,
            read_args=(),
            device_params={'TypeName': 'Switch', 'Image': image, 'Used': used},
            write_converter=cls._command_to_number
        )
    
    @classmethod
    def create_power_device(cls, unit_id: int, spec_id: str, command: str, 
                            address: int,
                            used: int = 1, generated: bool = False,
                            image: Optional[int] = None) -> DeviceSpec:
        """Create a power meter device specification.
        
        Args:
            generated: If True, sets Switchtype=4 for energy export display
            image: Optional icon image number. If None, defaults to 15 for generated meters
        """
        params = {
            'TypeName': 'kWh',
            'Used': used,
            'Options': {'EnergyMeterMode': '1'}
        }
        if generated:
            params['Switchtype'] = 4
            params['Image'] = image if image is not None else 15
        elif image is not None:
            params['Image'] = image
        
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._instant_power_converter,
            read_args=(),
            device_params=params
        )
    
    @classmethod
    def create_split_power_device(cls, unit_id: int, spec_id: str, command: str, 
                                  address: int,
                                  state_idx: int, valid_states: List[int],
                                  used: int = 1, generated: bool = False,
                                  image: Optional[int] = None) -> DeviceSpec:
        """Create a split power meter device specification.
        
        Args:
            generated: If True, sets Switchtype=4 for energy export display
            image: Optional icon image number. If None, defaults to 15 for generated meters
        """
        params = {
            'TypeName': 'kWh',
            'Used': used,
            'Options': {'EnergyMeterMode': '1'}
        }
        if generated:
            params['Switchtype'] = 4
            params['Image'] = image if image is not None else 15
        elif image is not None:
            params['Image'] = image
        
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._instant_power_split_converter,
            read_args=([state_idx, valid_states],),
            device_params=params
        )
    
    @classmethod
    def create_cop_device(cls, unit_id: int, spec_id: str, command: str, 
                          heat_idx: int, power_idx: int,
                          used: int = 1,
                          allowed_modes: Optional[List[int]] = None) -> DeviceSpec:
        """Create a COP calculator device specification.
        
        Args:
            unit_id: Domoticz unit ID
            spec_id: Unique specification identifier (also used for translation)
            command: Luxtronik command type
            heat_idx: Index for heat output reading
            power_idx: Index for power input reading
            used: Device used flag (default 1)
            allowed_modes: Optional list of operating mode values to filter by
                          e.g., [0] for heating only, [1] for DHW only, [0, 1] for both
                          If None, no mode filtering is applied (total COP)
        """
        # Build config list: [heat_idx, power_idx] or [heat_idx, power_idx, allowed_modes]
        config = [heat_idx, power_idx]
        if allowed_modes is not None:
            config.append(allowed_modes)
        
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=heat_idx,  # Primary address for lookup
            read_converter=cls._cop_converter,
            read_args=(config,),
            device_params={
                'TypeName': 'Custom',
                'Used': used,
                'Options': {'Custom': '1;COP'}
            }
        )
    
    @classmethod
    def create_text_device(cls, unit_id: int, spec_id: str, command: str, 
                           address: int,
                           power_idx: int, power_threshold: float,
                           used: int = 1, image: Optional[int] = None) -> DeviceSpec:
        """Create a text status device specification.
        
        Args:
            image: Optional icon image number
        """
        params = {'TypeName': 'Text', 'Used': used}
        if image is not None:
            params['Image'] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._text_state_converter,
            read_args=([power_idx, power_threshold],),
            device_params=params
        )
    
    @classmethod
    def create_percentage_device(cls, unit_id: int, spec_id: str, command: str, 
                                 address: int,
                                 used: int = 1) -> DeviceSpec:
        """Create a percentage device specification."""
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._float_converter,
            read_args=(1,),
            device_params={'TypeName': 'Percentage', 'Used': used}
        )
    
    @classmethod
    def create_temp_diff_device(cls, unit_id: int, spec_id: str, command: str, 
                                indices: List[int],
                                divider: float = 10, used: int = 1,
                                gated: bool = False) -> DeviceSpec:
        """Create a temperature difference device specification.
        
        Args:
            unit_id: Domoticz unit ID
            spec_id: Unique specification identifier (also used for translation)
            command: Luxtronik command type
            indices: List of [temp1_address, temp2_address] for difference calculation
            divider: Value divider for temperature conversion
            used: Device used flag (default 1)
            gated: If True, use steady-state gating to skip updates when idle
        """
        converter = cls._gated_temp_diff_converter if gated else cls._temp_diff_converter
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=indices,
            read_converter=converter,
            read_args=(divider,),
            device_params={
                'TypeName': 'Custom',
                'Used': used,
                'Options': {'Custom': '1;K'}
            }
        )
    
    @classmethod
    def create_runtime_device(cls, unit_id: int, spec_id: str, command: str,
                              address: int, used: int = 1,
                              image: Optional[int] = None) -> DeviceSpec:
        """Create a runtime hours device specification.
        
        Converts seconds from controller to hours for display.
        Used for compressor lifetime runtime tracking.
        
        Args:
            image: Optional icon image number
        """
        params = {
            'TypeName': 'Custom',
            'Used': used,
            'Options': {'Custom': '1;h'}
        }
        if image is not None:
            params['Image'] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._runtime_hours_converter,
            read_args=(),
            device_params=params
        )
    
    @classmethod
    def create_counter_device(cls, unit_id: int, spec_id: str, command: str,
                              address: int, unit_label: str = 'count',
                              used: int = 1, image: Optional[int] = None) -> DeviceSpec:
        """Create a counter device specification.
        
        Displays integer counts like compressor starts.
        
        Args:
            image: Optional icon image number
        """
        params = {
            'TypeName': 'Custom',
            'Used': used,
            'Options': {'Custom': f'1;{unit_label}'}
        }
        if image is not None:
            params['Image'] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._integer_value_converter,
            read_args=(),
            device_params=params
        )
    
    @classmethod
    def create_capacity_device(cls, unit_id: int, spec_id: str, command: str,
                               actual_idx: int, max_idx: int,
                               used: int = 1) -> DeviceSpec:
        """Create a capacity utilization device specification.
        
        Calculates percentage from actual/max compressor frequency.
        Gated to only report during steady-state operation.
        """
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=actual_idx,  # Primary address for lookup
            read_converter=cls._capacity_converter,
            read_args=([actual_idx, max_idx],),
            device_params={
                'TypeName': 'Custom',
                'Used': used,
                'Options': {'Custom': '1;%'}
            }
        )
    
    @classmethod
    def create_last_cycle_device(cls, unit_id: int, spec_id: str, command: str,
                                 address: int, used: int = 1,
                                 image: Optional[int] = None) -> DeviceSpec:
        """Create a last cycle duration device specification.
        
        Tracks cycle completions and displays duration in minutes.
        Requires a CycleTracker instance to be passed during updates.
        Note: The tracker is passed in the read_args and must be set up
        by the plugin after initialization.
        
        Args:
            image: Optional icon image number
        """
        params = {
            'TypeName': 'Custom',
            'Used': used,
            'Options': {'Custom': '1;min'}
        }
        if image is not None:
            params['Image'] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._last_cycle_converter,
            read_args=(None,),  # Placeholder - tracker set during plugin init
            device_params=params
        )
    
    @classmethod
    def create_status_switch_device(cls, unit_id: int, spec_id: str, command: str,
                                    address: int, used: int = 1,
                                    image: Optional[int] = None) -> DeviceSpec:
        """Create a read-only status switch device specification.
        
        Shows on/off status based on controller flag without write capability.
        Used for status indicators like cooling_permitted.
        
        Args:
            image: Optional icon image number
        """
        params = {
            'Type': 244,
            'Subtype': 73,
            'Switchtype': 0,
            'Used': used
        }
        if image is not None:
            params['Image'] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._boolean_switch_converter,
            read_args=(),
            device_params=params
            # No write_converter - this is read-only
        )


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
            'READ_CALCUL': {},
            'READ_PARAMS': {},
        }
        self._device_id: str = ""  # Will be set during onStart
    
    def _get_device_id(self) -> str:
        """Generate stable DeviceID based on HardwareID.
        
        HardwareID is assigned by Domoticz when hardware is created and never
        changes, even if the hardware is renamed or IP address changes.
        This ensures device stability across configuration changes.
        """
        hw_id = Parameters.get('HardwareID', '0')
        return f"luxtronikex_hw{hw_id}"
    
    def _init_available_writes(self) -> None:
        """Initialize available write fields."""
        self.available_writes = {
            -1: Field(),
            LuxtronikAddress.TEMP_OFFSET: Field(_translator.get_device_name('temp_offset'), list(range(-50, 51, 5))),
            LuxtronikAddress.HEATING_MODE: Field(_translator.get_device_name('heating_mode'), [0, 1, 2, 3, 4]),
            LuxtronikAddress.HOT_WATER_MODE: Field(_translator.get_device_name('hot_water_mode'), [0, 1, 2, 3, 4]),
            LuxtronikAddress.DHW_TEMP_TARGET: Field(_translator.get_device_name('dhw_temp_target'), list(range(300, 651, 5))),
            LuxtronikAddress.COOLING_ENABLED: Field(_translator.get_device_name('cooling_enabled'), [0, 1]),
            LuxtronikAddress.DHW_POWER_MODE: Field(_translator.get_device_name('dhw_power_mode'), [0, 1]),
            LuxtronikAddress.ROOM_TEMP_SETPOINT: Field(_translator.get_device_name('room_temp_setpoint'), list(range(150, 301, 5)))
        }
    
    def _build_device_specs(self) -> List[DeviceSpec]:
        """Build all device specifications with stable Unit IDs.
        
        Each device has an explicit unit_id and spec_id that never changes,
        even if the order in this list changes. This ensures backward
        compatibility when adding, removing, or reordering devices.
        
        The spec_id is also used as the translation key for device names
        and descriptions via DEVICE_TRANSLATIONS.
        
        Unit ID Grouping (with gaps for future expansion):
        ═══════════════════════════════════════════════════
        
        Group 1: Status Overview (1-9)
        ──────────────────────────────
          1     : Working mode status display
          2-9   : Reserved for future status devices
        
        Group 2: User Controls (10-29)
        ──────────────────────────────
          10-16 : Writable control devices (mode selectors, setpoints)
          17-29 : Reserved for future controls
        
        Group 3: Power Input (30-39)
        ────────────────────────────
          30-32 : Electrical power (total, heating, DHW)
          33-39 : Reserved for future power metrics
        
        Group 4: Heat Output (40-49)
        ────────────────────────────
          40-42 : Thermal output (total, heating, DHW)
          43-49 : Reserved for future heat metrics
        
        Group 5: Efficiency (50-59)
        ───────────────────────────
          50-52 : COP metrics (total, heating, DHW)
          53-59 : Reserved for future efficiency metrics
        
        Group 6: Heating Circuit (60-79)
        ────────────────────────────────
          60-65 : Temperatures and spreads
          66-67 : Pump and flow
          68-79 : Reserved for future heating devices
        
        Group 7: DHW (80-89)
        ────────────────────
          80    : DHW temperature
          81-89 : Reserved for future DHW devices
        
        Group 8: Environment (90-99)
        ────────────────────────────
          90-91 : Outdoor temperatures
          92-93 : Room temperatures
          94-99 : Reserved for future environmental
        
        Group 9: Source Circuit (100-119)
        ──────────────────────────────────
          100-104 : Temperatures and spreads
          105-106 : Pump and flow
          107-119 : Reserved for future source devices
        
        Group 10: Mixing Circuits (120-139)
        ───────────────────────────────────
          120-121 : Mixing circuit 1
          122-129 : Reserved for MC1
          130-131 : Mixing circuit 2
          132-139 : Reserved for MC2
        
        Group 11: Compressor (140-159)
        ──────────────────────────────
          140-144 : Compressor operation
          145-159 : Reserved for future compressor
        
        Group 12: Refrigerant Circuit (160-179)
        ───────────────────────────────────────
          160-167 : Temperatures and pressures
          168-179 : Reserved for future refrigerant
        
        Group 13: Statistics & Counters (180-199)
        ─────────────────────────────────────────
          180-185 : Runtime counters and cycle tracking
          186-199 : Reserved for future statistics
        
        Group 14: Diagnostics (200-209)
        ───────────────────────────────
          200-201 : Error count and status flags
          202-209 : Reserved for future diagnostics
        """
        heating_mode_options = ['Automatic', '2nd heat source', 'Party', 'Holidays', 'Off']
        dhw_power_options = ['Normal', 'Luxury']
        
        return [
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 1: STATUS OVERVIEW (Units 1-9)
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 1: Current operating mode status text
            DeviceFactory.create_text_device(
                1, 'working_mode', 'READ_CALCUL', 
                LuxtronikAddress.WORKING_MODE,
                LuxtronikAddress.POWER_TOTAL, 0.1, used=1, image=15),
            
            # Units 2-9: Reserved for future status devices
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 2: USER CONTROLS (Units 10-29)
            # All writable devices in one place - the "control panel"
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 10: Heating operation mode selector switch [WRITABLE]
            DeviceFactory.create_selector_device(
                10, 'heating_mode', 'READ_PARAMS', 
                LuxtronikAddress.HEATING_MODE,
                heating_mode_options, [0, 1, 2, 3, 4], LuxtronikAddress.HEATING_MODE, used=1),
            
            # Unit 11: Hot water operation mode selector switch [WRITABLE]
            DeviceFactory.create_selector_device(
                11, 'hot_water_mode', 'READ_PARAMS', 
                LuxtronikAddress.HOT_WATER_MODE,
                heating_mode_options, [0, 1, 2, 3, 4], LuxtronikAddress.HOT_WATER_MODE, used=1,
                image=11),
            
            # Unit 12: DHW Power Mode selector switch [WRITABLE]
            DeviceFactory.create_selector_device(
                12, 'dhw_power_mode', 'READ_PARAMS', 
                LuxtronikAddress.DHW_POWER_MODE,
                dhw_power_options, [0, 1], LuxtronikAddress.DHW_POWER_MODE, used=1,
                image=11),
            
            # Unit 13: Cooling mode enable/disable switch [WRITABLE]
            DeviceFactory.create_switch_device(
                13, 'cooling_enabled', 'READ_PARAMS', 
                LuxtronikAddress.COOLING_ENABLED, used=1),
            
            # Unit 14: Temperature offset adjustment [WRITABLE]
            DeviceFactory.create_setpoint_device(
                14, 'temp_offset', 'READ_PARAMS', 
                LuxtronikAddress.TEMP_OFFSET,
                min_val="-5", max_val="5", used=0),
            
            # Unit 15: Domestic hot water target temperature setting [WRITABLE]
            DeviceFactory.create_setpoint_device(
                15, 'dhw_temp_target', 'READ_PARAMS', 
                LuxtronikAddress.DHW_TEMP_TARGET,
                min_val="30", max_val="65", used=0),
            
            # Unit 16: Actual room temperature set-point [WRITABLE]
            DeviceFactory.create_setpoint_device(
                16, 'room_temp_setpoint', 'READ_PARAMS', 
                LuxtronikAddress.ROOM_TEMP_SETPOINT,
                min_val="15", max_val="30", used=1),
            
            # Units 17-29: Reserved for future controls
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 3: POWER INPUT (Units 30-39)
            # Electrical consumption tracking
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 30: Total electrical power consumption
            DeviceFactory.create_power_device(
                30, 'power_total', 'READ_CALCUL', 
                LuxtronikAddress.POWER_TOTAL, used=1),
            
            # Unit 31: Heating mode electrical power consumption
            DeviceFactory.create_split_power_device(
                31, 'power_heating', 'READ_CALCUL', 
                LuxtronikAddress.POWER_TOTAL,
                LuxtronikAddress.WORKING_MODE, [0], used=1),
            
            # Unit 32: Hot water mode electrical power consumption
            DeviceFactory.create_split_power_device(
                32, 'power_dhw', 'READ_CALCUL', 
                LuxtronikAddress.POWER_TOTAL,
                LuxtronikAddress.WORKING_MODE, [1], used=1),
            
            # Units 33-39: Reserved for future power metrics
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 4: HEAT OUTPUT (Units 40-49)
            # Thermal energy delivery tracking
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 40: Total heat output power
            DeviceFactory.create_power_device(
                40, 'heat_out_total', 'READ_CALCUL', 
                LuxtronikAddress.HEAT_OUTPUT, generated=True, used=1),
            
            # Unit 41: Heating mode heat output power
            DeviceFactory.create_split_power_device(
                41, 'heat_out_heating', 'READ_CALCUL', 
                LuxtronikAddress.HEAT_OUTPUT,
                LuxtronikAddress.WORKING_MODE, [0], generated=True, used=1, image=15),
            
            # Unit 42: Hot water mode heat output power
            DeviceFactory.create_split_power_device(
                42, 'heat_out_dhw', 'READ_CALCUL', 
                LuxtronikAddress.HEAT_OUTPUT,
                LuxtronikAddress.WORKING_MODE, [1], generated=True, used=1, image=15),
            
            # Units 43-49: Reserved for future heat output metrics
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 5: EFFICIENCY (Units 50-59)
            # COP and efficiency metrics
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 50: Overall system COP (Coefficient of Performance)
            # Filtered to only log during active heating or DHW modes
            DeviceFactory.create_cop_device(
                50, 'cop_total', 'READ_CALCUL', 
                LuxtronikAddress.HEAT_OUTPUT, LuxtronikAddress.POWER_TOTAL,
                allowed_modes=[0, 1], used=1),  # Heating + DHW modes
            
            # Unit 51: COP for heating mode only
            # Only logs when system is in heating mode (mode 0) at steady-state
            DeviceFactory.create_cop_device(
                51, 'cop_heating', 'READ_CALCUL', 
                LuxtronikAddress.HEAT_OUTPUT, LuxtronikAddress.POWER_TOTAL,
                allowed_modes=[0], used=1),  # Heating mode only
            
            # Unit 52: COP for DHW (domestic hot water) mode only  
            # Only logs when system is in DHW mode (mode 1) at steady-state
            DeviceFactory.create_cop_device(
                52, 'cop_dhw', 'READ_CALCUL', 
                LuxtronikAddress.HEAT_OUTPUT, LuxtronikAddress.POWER_TOTAL,
                allowed_modes=[1], used=1),  # DHW mode only
            
            # Units 53-59: Reserved for future efficiency metrics
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 6: HEATING CIRCUIT (Units 60-79)
            # All heating circuit devices together
            # ═══════════════════════════════════════════════════════════════════
            
            # --- Temperatures (Units 60-65) ---
            
            # Unit 60: Heat supply/flow temperature sensor
            DeviceFactory.create_temperature_device(
                60, 'heat_supply_temp', 'READ_CALCUL', 
                LuxtronikAddress.HEAT_SUPPLY_TEMP, used=1),
            
            # Unit 61: Return temperature sensor from heating system
            DeviceFactory.create_temperature_device(
                61, 'heat_return_temp', 'READ_CALCUL', 
                LuxtronikAddress.HEAT_RETURN_TEMP, used=1),
            
            # Unit 62: Calculated target return temperature
            DeviceFactory.create_temperature_device(
                62, 'return_temp_target', 'READ_CALCUL', 
                LuxtronikAddress.RETURN_TEMP_TARGET, used=1),
            
            # Unit 63: Heating temperature difference (Supply - Return)
            # Gated: ΔT approaches zero as distribution loop equilibrates when idle
            DeviceFactory.create_temp_diff_device(
                63, 'heating_temp_diff', 'READ_CALCUL', 
                [LuxtronikAddress.HEAT_SUPPLY_TEMP, LuxtronikAddress.HEAT_RETURN_TEMP],
                gated=True, used=1),
            
            # Unit 64: Controller's heating circuit spread target (ΔT setpoint)
            DeviceFactory.create_custom_device(
                64, 'heating_spread_target', 'READ_CALCUL',
                LuxtronikAddress.HEATING_SPREAD_TARGET, 'K', divider=10, used=0, precision='0.1'),
            
            # Unit 65: Controller's heating circuit spread actual (measured ΔT)
            DeviceFactory.create_custom_device(
                65, 'heating_spread_actual', 'READ_CALCUL',
                LuxtronikAddress.HEATING_SPREAD_ACTUAL, 'K', divider=10, used=0, precision='0.1'),
            
            # --- Pump and Flow (Units 66-67) ---
            
            # Unit 66: Heating circulation pump speed percentage
            DeviceFactory.create_percentage_device(
                66, 'heating_pump_speed', 'READ_CALCUL', 
                LuxtronikAddress.HEATING_PUMP_SPEED, used=1),
            
            # Unit 67: Heating circuit flow rate measurement (hidden by default)
            # Note: This measures flow through the HUP pump circuit (water side)
            # Used for thermal power calculation via heat meter (WMZ)
            DeviceFactory.create_custom_device(
                67, 'heating_flow', 'READ_CALCUL',
                LuxtronikAddress.HEATING_FLOW, 'L/h', used=0, image=35),
            
            # Units 68-79: Reserved for future heating circuit devices
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 7: DHW (Units 80-89)
            # Domestic hot water system
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 80: Domestic hot water current temperature
            DeviceFactory.create_temperature_device(
                80, 'dhw_temp', 'READ_CALCUL', 
                LuxtronikAddress.DHW_TEMP, used=1),
            
            # Units 81-89: Reserved for future DHW devices
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 8: ENVIRONMENT (Units 90-99)
            # Outdoor and room temperatures
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 90: Outside ambient temperature sensor
            DeviceFactory.create_temperature_device(
                90, 'outside_temp', 'READ_CALCUL', 
                LuxtronikAddress.OUTSIDE_TEMP, used=1),
            
            # Unit 91: Average outside temperature over time
            DeviceFactory.create_temperature_device(
                91, 'outside_temp_avg', 'READ_CALCUL', 
                LuxtronikAddress.OUTSIDE_TEMP_AVG, used=0),
            
            # Unit 92: Room temperature sensor reading
            DeviceFactory.create_temperature_device(
                92, 'room_temp', 'READ_CALCUL', 
                LuxtronikAddress.ROOM_TEMP, used=1),
            
            # Unit 93: Room temperature setpoint (read-only display)
            DeviceFactory.create_temperature_device(
                93, 'room_temp_target', 'READ_CALCUL', 
                LuxtronikAddress.ROOM_TEMP_TARGET, used=0),
            
            # Units 94-99: Reserved for future environmental devices
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 9: SOURCE CIRCUIT (Units 100-119)
            # Ground/brine loop - complete circuit in one group
            # ═══════════════════════════════════════════════════════════════════
            
            # --- Temperatures (Units 100-104) ---
            
            # Unit 100: Source inlet temperature (from ground/well)
            DeviceFactory.create_temperature_device(
                100, 'source_in_temp', 'READ_CALCUL', 
                LuxtronikAddress.SOURCE_IN_TEMP, used=1),
            
            # Unit 101: Source outlet temperature (to ground/well)
            DeviceFactory.create_temperature_device(
                101, 'source_out_temp', 'READ_CALCUL', 
                LuxtronikAddress.SOURCE_OUT_TEMP, used=1),
            
            # Unit 102: Brine temperature difference (Source in - Source out)
            # Gated: ΔT approaches zero as source loop equilibrates when idle
            DeviceFactory.create_temp_diff_device(
                102, 'brine_temp_diff', 'READ_CALCUL', 
                [LuxtronikAddress.SOURCE_IN_TEMP, LuxtronikAddress.SOURCE_OUT_TEMP],
                gated=True, used=1),
            
            # Unit 103: Controller's source circuit spread target (ΔT setpoint)
            DeviceFactory.create_custom_device(
                103, 'source_spread_target', 'READ_CALCUL',
                LuxtronikAddress.SOURCE_SPREAD_TARGET, 'K', divider=10, used=0, precision='0.1'),
            
            # Unit 104: Controller's source circuit spread actual (measured ΔT)
            DeviceFactory.create_custom_device(
                104, 'source_spread_actual', 'READ_CALCUL',
                LuxtronikAddress.SOURCE_SPREAD_ACTUAL, 'K', divider=10, used=0, precision='0.1'),
            
            # --- Pump and Flow (Units 105-106) ---
            
            # Unit 105: Brine/well circulation pump speed percentage
            DeviceFactory.create_percentage_device(
                105, 'brine_pump_speed', 'READ_CALCUL', 
                LuxtronikAddress.BRINE_PUMP_SPEED, used=1),
            
            # Unit 106: Source/brine circuit flow rate measurement
            # Note: This measures flow through the VBO pump circuit (brine side)
            DeviceFactory.create_custom_device(
                106, 'source_flow', 'READ_CALCUL', 
                LuxtronikAddress.SOURCE_FLOW, 'l/h', used=1, image=35),
            
            # Units 107-119: Reserved for future source circuit devices
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 10: MIXING CIRCUITS (Units 120-139)
            # Multi-zone heating support
            # ═══════════════════════════════════════════════════════════════════
            
            # --- Mixing Circuit 1 (Units 120-129) ---
            
            # Unit 120: Mixing circuit 1 current temperature
            DeviceFactory.create_temperature_device(
                120, 'mc1_temp', 'READ_CALCUL', 
                LuxtronikAddress.MC1_TEMP, used=0),
            
            # Unit 121: Mixing circuit 1 target temperature
            DeviceFactory.create_temperature_device(
                121, 'mc1_temp_target', 'READ_CALCUL', 
                LuxtronikAddress.MC1_TEMP_TARGET, used=0),
            
            # Units 122-129: Reserved for MC1 expansion
            
            # --- Mixing Circuit 2 (Units 130-139) ---
            
            # Unit 130: Mixing circuit 2 current temperature
            DeviceFactory.create_temperature_device(
                130, 'mc2_temp', 'READ_CALCUL', 
                LuxtronikAddress.MC2_TEMP, used=0),
            
            # Unit 131: Mixing circuit 2 target temperature
            DeviceFactory.create_temperature_device(
                131, 'mc2_temp_target', 'READ_CALCUL', 
                LuxtronikAddress.MC2_TEMP_TARGET, used=0),
            
            # Units 132-139: Reserved for MC2 expansion
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 11: COMPRESSOR (Units 140-159)
            # Compressor operation and performance
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 140: Compressor frequency/speed
            DeviceFactory.create_custom_device(
                140, 'compressor_freq', 'READ_CALCUL', 
                LuxtronikAddress.COMPRESSOR_FREQ, 'Hz', used=1),
            
            # Unit 141: Controller target compressor frequency (hidden by default)
            # Compare to actual frequency to see controller tracking
            DeviceFactory.create_custom_device(
                141, 'target_frequency', 'READ_CALCUL',
                LuxtronikAddress.TARGET_FREQUENCY, 'Hz', used=0),
            
            # Unit 142: Minimum frequency target (hidden by default)
            # Used in COP gating logic to detect steady-state operation
            DeviceFactory.create_custom_device(
                142, 'min_frequency', 'READ_CALCUL',
                LuxtronikAddress.COMPRESSOR_FREQ_MIN, 'Hz', used=0),
            
            # Unit 143: Maximum frequency limit (hidden by default)
            # System capacity ceiling, used for capacity utilization calculation
            DeviceFactory.create_custom_device(
                143, 'max_frequency', 'READ_CALCUL',
                LuxtronikAddress.COMPRESSOR_FREQ_MAX, 'Hz', used=0),
            
            # Unit 144: Compressor capacity utilization percentage
            # Shows current load relative to maximum capability
            # Gated: only updates during steady-state operation
            DeviceFactory.create_capacity_device(
                144, 'compressor_capacity', 'READ_CALCUL',
                LuxtronikAddress.COMPRESSOR_FREQ, LuxtronikAddress.COMPRESSOR_FREQ_MAX, used=1),
            
            # Units 145-159: Reserved for future compressor devices
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 12: REFRIGERANT CIRCUIT (Units 160-179)
            # Refrigerant temperatures and pressures
            # ═══════════════════════════════════════════════════════════════════
            
            # --- Temperatures (Units 160-165) ---
            
            # Unit 160: Hot gas temperature monitoring (compressor outlet)
            DeviceFactory.create_temperature_device(
                160, 'hot_gas_temp', 'READ_CALCUL', 
                LuxtronikAddress.HOT_GAS_TEMP, used=1),
            
            # Unit 161: Compressor suction temperature (entering compressor)
            DeviceFactory.create_temperature_device(
                161, 'suction_temp', 'READ_CALCUL', 
                LuxtronikAddress.SUCTION_TEMP, used=1),
            
            # Unit 162: Discharge line temperature (after initial condenser cooling)
            DeviceFactory.create_temperature_device(
                162, 'discharge_temp', 'READ_CALCUL',
                LuxtronikAddress.DISCHARGE_TEMP, used=1),
            
            # Unit 163: Evaporating temperature (refrigerant evaporation point)
            DeviceFactory.create_temperature_device(
                163, 'evaporating_temp', 'READ_CALCUL',
                LuxtronikAddress.EVAPORATING_TEMP, used=1),
            
            # Unit 164: Condensing temperature (refrigerant condensation point)
            DeviceFactory.create_temperature_device(
                164, 'condensing_temp', 'READ_CALCUL',
                LuxtronikAddress.CONDENSING_TEMP, used=1),
            
            # Unit 165: Superheat monitoring
            # Gated: stale readings during idle corrupt operating averages
            DeviceFactory.create_custom_device(
                165, 'superheat', 'READ_CALCUL', 
                LuxtronikAddress.SUPERHEAT, 'K', divider=10, gated=True, used=1),
            
            # --- Pressures (Units 166-167) ---
            
            # Unit 166: High pressure monitoring
            # Gated: equilibrates to ambient when off, not operationally meaningful
            DeviceFactory.create_custom_device(
                166, 'high_pressure', 'READ_CALCUL', 
                LuxtronikAddress.HIGH_PRESSURE, 'bar', divider=100, gated=True, used=1),
            
            # Unit 167: Low pressure monitoring
            # Gated: equilibrates to ambient when off, not operationally meaningful
            DeviceFactory.create_custom_device(
                167, 'low_pressure', 'READ_CALCUL', 
                LuxtronikAddress.LOW_PRESSURE, 'bar', divider=100, gated=True, used=1),
            
            # Units 168-179: Reserved for future refrigerant devices
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 13: STATISTICS & COUNTERS (Units 180-199)
            # Operational history and lifetime tracking
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 180: Lifetime compressor operating hours
            # Useful for maintenance scheduling
            DeviceFactory.create_runtime_device(
                180, 'compressor_runtime', 'READ_CALCUL',
                LuxtronikAddress.COMPRESSOR_RUNTIME, used=1, image=21),
            
            # Unit 181: Total compressor start count
            # Indicates cycling behavior and compressor wear
            DeviceFactory.create_counter_device(
                181, 'compressor_starts', 'READ_CALCUL',
                LuxtronikAddress.COMPRESSOR_STARTS, 'starts', used=1),
            
            # Unit 182: Duration of last completed compressor cycle
            # Updates only when a cycle completes (sparse updates)
            DeviceFactory.create_last_cycle_device(
                182, 'last_cycle', 'READ_CALCUL',
                LuxtronikAddress.CURRENT_CYCLE_TIME, used=1, image=21),
            
            # Unit 183: Total operating hours in heating mode (hidden by default)
            DeviceFactory.create_runtime_device(
                183, 'heating_runtime', 'READ_CALCUL',
                LuxtronikAddress.HEATING_RUNTIME, used=0, image=21),
            
            # Unit 184: Total operating hours in hot water mode (hidden by default)
            DeviceFactory.create_runtime_device(
                184, 'dhw_runtime', 'READ_CALCUL',
                LuxtronikAddress.DHW_RUNTIME, used=0, image=21),
            
            # Unit 185: Total operating hours in passive cooling mode (hidden by default)
            DeviceFactory.create_runtime_device(
                185, 'cooling_runtime', 'READ_CALCUL',
                LuxtronikAddress.COOLING_RUNTIME, used=0, image=21),
            
            # Units 186-199: Reserved for future statistics
            
            # ═══════════════════════════════════════════════════════════════════
            # GROUP 14: DIAGNOSTICS (Units 200-209)
            # Error tracking and status flags
            # ═══════════════════════════════════════════════════════════════════
            
            # Unit 200: Error count in controller memory (hidden by default)
            # Quick health indicator - check logs if count increases
            DeviceFactory.create_counter_device(
                200, 'error_count', 'READ_CALCUL',
                LuxtronikAddress.ERROR_COUNT, 'errors', used=0, image=13),
            
            # Unit 201: Cooling permitted status (hidden by default)
            # Read-only indicator showing if passive cooling is currently released
            # Based on outdoor temperature and settings - not user controllable
            DeviceFactory.create_status_switch_device(
                201, 'cooling_permitted', 'READ_CALCUL',
                LuxtronikAddress.COOLING_PERMITTED, used=0, image=16),
            
            # Units 202-209: Reserved for future diagnostics
        ]
     
    def create_devices(self) -> None:
        """Create all Domoticz devices."""
        global _unit_specs, _plugin_ref
        
        _logger.log("Creating devices", DebugLevel.BASIC)
        
        # Store reference to plugin for command handling
        _plugin_ref = self
        
        self._init_available_writes()
        specs = self._build_device_specs()
        
        # Inject CycleTracker into the last_cycle device spec
        # The last_cycle device needs stateful tracking between heartbeats
        for spec in specs:
            if spec.spec_id == 'last_cycle':
                spec.read_args = (self.cycle_tracker,)
                _logger.log("Injected CycleTracker into last_cycle device", DebugLevel.VERBOSE)
                break
        
        # Multi-instance support: unique DeviceID per hardware
        device_id = self._device_id
        
        for spec in specs:
            unit_id = spec.unit_id  # Use explicit unit_id, not position
            name = _translator.get_device_name(spec.spec_id)
            full_name = f"{Parameters['Name']} - {name}"
            
            # Store spec in module-level storage for command handling
            _unit_specs[(device_id, unit_id)] = spec
            
            # Store spec for later use (device updates)
            self._device_specs[unit_id] = spec
            self._command_specs[spec.command][unit_id] = spec
            
            # Add description if available
            description = _translator.get_device_description(spec.spec_id)
            if description:
                spec.device_params['Description'] = description
            
            # Check if device exists
            if device_id not in Devices or unit_id not in Devices[device_id].Units:
                # Create new unit
                unit = LuxtronikUnit(
                    Name=full_name,
                    DeviceID=device_id,
                    Unit=unit_id,
                    **spec.device_params
                )
                unit.Create()
                _logger.log(f"Created device {unit_id} (spec_id={spec.spec_id}): {name}", DebugLevel.DEVICE)
            else:
                # Device exists - check if it should be updated
                existing_unit = Devices[device_id].Units[unit_id]
                current_name = existing_unit.Name
                needs_options_update = False
                needs_properties_update = False
                
                # Smart rename: only rename if current name's translation part
                # matches a known translation (not user-customized)
                # Device names have format: "{HardwareName} - {TranslatedName}"
                if current_name != full_name:
                    # Extract the translation part (after " - ")
                    if ' - ' in current_name:
                        translation_part = current_name.split(' - ', 1)[1]
                    else:
                        translation_part = current_name
                    
                    # Check if translation part is a known translation
                    if _translator.is_known_device_name(translation_part, spec.spec_id):
                        existing_unit.Name = full_name
                        needs_properties_update = True
                        _logger.log(f"Device {unit_id} (spec_id={spec.spec_id}) renamed: {current_name} -> {full_name}", DebugLevel.DEVICE)
                
                # Update description if it's a known translation
                current_description = existing_unit.Description
                new_description = _translator.get_device_description(spec.spec_id)
                
                if current_description != new_description and new_description:
                    if _translator.is_known_description(current_description, spec.spec_id):
                        existing_unit.Description = new_description
                        needs_properties_update = True
                        _logger.log(f"Device {unit_id} (spec_id={spec.spec_id}) description updated", DebugLevel.DEVICE)
                
                # For selector switches: update LevelNames if they're known translations
                if spec.selector_options:
                    current_options = existing_unit.Options
                    if 'LevelNames' in current_options:
                        current_level_names = current_options['LevelNames']
                        new_level_names = _translator.translate_selector_options(spec.selector_options)
                        
                        if current_level_names != new_level_names:
                            # Check if current options are known translations
                            current_items = current_level_names.split('|')
                            all_known = all(
                                _translator.is_known_selector_option(item, opt_key) 
                                for item, opt_key in zip(current_items, spec.selector_options)
                            )
                            
                            if all_known:
                                existing_unit.Options = {
                                    **current_options,
                                    'LevelNames': new_level_names
                                }
                                needs_options_update = True
                                _logger.log(f"Device {unit_id} (spec_id={spec.spec_id}) selector options updated", DebugLevel.DEVICE)
                
                if needs_properties_update or needs_options_update:
                    # DomoticzEx requires UpdateProperties=True to update Name/Description
                    # and UpdateOptions=True to update Options
                    existing_unit.Update(
                        Log=False, 
                        UpdateProperties=needs_properties_update,
                        UpdateOptions=needs_options_update
                    )
                else:
                    _logger.log(f"Device {unit_id} (spec_id={spec.spec_id}) already exists: {current_name}", DebugLevel.DEVICE)
        
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
        
        if device_id not in Devices or unit_id not in Devices[device_id].Units:
            _logger.log(f"Device {unit_id} (spec_id={spec.spec_id}) not found", DebugLevel.DEVICE)
            return False
        
        unit = Devices[device_id].Units[unit_id]
        needs_update, reason, diff = self.update_tracker.needs_update(unit, new_values)
        
        if needs_update:
            if 'nValue' in new_values:
                unit.nValue = new_values['nValue']
            if 'sValue' in new_values:
                unit.sValue = str(new_values['sValue'])
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
                        _logger.log(f"Skipping {spec.spec_id}: gated - {gate_reason}", DebugLevel.VERBOSE)
                    else:
                        _logger.log(f"Skipping {spec.spec_id}: converter returned None", DebugLevel.VERBOSE)
                    continue
                
                if self.update_device(unit_id, new_values):
                    updated_count += 1
                else:
                    unchanged_count += 1
            except Exception as e:
                _logger.error(f"Error updating device {unit_id} (spec_id={spec.spec_id})", exc=e)
        
        # Log summary at BASIC level
        _logger.log(f"{command}: Updated {updated_count}, unchanged {unchanged_count}, gated {gated_count}", DebugLevel.BASIC)
    
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
            'READ_CALCUL': SocketCommand.READ_CALCUL,
            'READ_PARAMS': SocketCommand.READ_PARAMS,
        }
        
        # Phase 1: Fetch all command data on a single connection
        batch = [(code, 0, 0) for code in command_codes.values()]
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
        
        # Phase 2: Update devices with shared data store
        for command in command_codes.keys():
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
        
        if not raw_value or raw_value == '0':
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
        try:
            # Settings dictionary is populated by Domoticz plugin framework
            # ShortLogAddOnlyNewValues: 1 = enabled (recommended), 0 = disabled
            # Note: Settings values are returned as strings
            setting_value = Settings.get("ShortLogAddOnlyNewValues", "0")
            
            # Handle string comparison (Settings returns strings)
            if str(setting_value) == "1":
                _logger.log(
                    "COP Logging: 'Only add newly received values' is ENABLED (recommended)",
                    DebugLevel.BASIC
                )
            else:
                # This is an important warning, always show it
                Domoticz.Status(
                    "COP Warning: For accurate COP averages, enable "
                    "Settings → Log History → 'Only add newly received values to the Log'. "
                    "Currently disabled - stale values will be logged during idle periods."
                )
        except NameError:
            # Settings dictionary not available (older Domoticz version?)
            _logger.log("Settings dictionary not available, skipping COP logging check", DebugLevel.VERBOSE)
        except Exception as e:
            # Other errors - log but don't fail
            _logger.log(f"Could not check COP logging setting: {e}", DebugLevel.VERBOSE)
    
    def onStart(self) -> None:
        """Initialize the plugin."""
        global _logger, _translator
        
        try:
            # Setup debugging
            _logger.level = int(Parameters["Mode6"])
            if _logger.level == DebugLevel.NONE:
                Domoticz.Debugging(0)   # Silence everything
            elif _logger.level == DebugLevel.ALL:
                Domoticz.Debugging(62)  # Plugin Debug() + framework device/connection info
            else:
                Domoticz.Debugging(2)   # Only plugin Debug() calls, no framework noise
            
            _logger.log("Plugin starting", DebugLevel.BASIC)
            
            # Initialize translations
            _translator.load_translations(
                DEVICE_TRANSLATIONS, 
                SELECTOR_OPTIONS, 
                WORKING_MODE_STATUSES
            )
            _translator.set_language(Parameters["Mode3"])
            
            # Note: Domoticz.Register() is now at module level to ensure
            # existing devices use our custom classes with callback support
            
            # Generate unique DeviceID for multi-instance support
            self._device_id = self._get_device_id()
            _logger.log(f"DeviceID: {self._device_id}", DebugLevel.BASIC)
            
            # Initialize connection
            self.connection = ConnectionManager(
                Parameters['Address'],
                int(Parameters['Port'])
            )
            
            # Set heartbeat with validation
            requested_heartbeat = int(Parameters['Mode2'])
            heartbeat = self._validate_heartbeat(requested_heartbeat)
            Domoticz.Heartbeat(heartbeat)
            _logger.log(f"Heartbeat set to {heartbeat}s", DebugLevel.BASIC)
            
            # Configure max COP limit
            self._configure_max_cop(Parameters.get('Mode1', '30'))
            
            # Create devices (this also initializes available_writes)
            self.create_devices()
            
            # Enable writes only for known safe addresses
            # These are the ONLY addresses that can be written to
            allowed_write_addresses = [addr for addr in self.available_writes.keys() if addr != -1]
            self.connection.enable_writes(allowed_write_addresses)
            _logger.log(f"Write protection enabled for {len(allowed_write_addresses)} addresses", DebugLevel.BASIC)
            
            # Initial update
            self.update_all()
            
            _logger.log("Plugin started successfully", DebugLevel.BASIC)
            
            # Check COP logging configuration
            # Settings dictionary is populated by Domoticz plugin framework
            self._check_cop_logging_setting()
            
        except ValueError as e:
            _logger.error(f"Configuration error during plugin start", exc=e)
        except Exception as e:
            _logger.error(f"Plugin start failed", exc=e)
    
    def onStop(self) -> None:
        """Clean up plugin resources."""
        global _plugin_ref, _unit_specs
        
        _logger.log("Plugin stopping", DebugLevel.BASIC)
        
        if self.connection:
            # Disable writes before closing
            self.connection.disable_writes()
            self.connection.close()
        
        # Clear global references
        _plugin_ref = None
        _unit_specs.clear()
        
        _logger.log("Plugin stopped", DebugLevel.BASIC)
    
    def onHeartbeat(self) -> None:
        """Handle periodic updates."""
        _logger.log("Heartbeat triggered", DebugLevel.VERBOSE)
        self.update_all()


# =============================================================================
# Plugin Instance and Callbacks
# =============================================================================
_plugin = LuxtronikPlugin()


def onStart():
    _plugin.onStart()


def onStop():
    _plugin.onStop()


def onHeartbeat():
    _plugin.onHeartbeat()