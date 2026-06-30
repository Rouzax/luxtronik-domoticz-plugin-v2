"""
Protocol constants for the Luxtronik heat-pump plugin.

Extracted from plugin.py so that other modules (refrigerant.py, future modules)
can import constants without pulling in the full plugin runtime.
"""


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
    LIQUID_LINE_TEMP = 233         # TFL - Liquid refrigerant temp before expansion valve
    TARGET_FREQUENCY = 236         # ID_WEB_Freq_VD_Soll - controller target frequency
    COMPRESSOR_FREQ_MIN = 237      # ID_WEB_Freq_VD_Min - minimum frequency target
    COMPRESSOR_FREQ_MAX = 238      # Freq_VD_Max - maximum frequency
    SOURCE_SPREAD_TARGET = 239     # VBO_Temp_Spread_Soll
    SOURCE_SPREAD_ACTUAL = 240     # VBO_Temp_Spread_Ist
    HEATING_PUMP_SPEED = 241
    HEATING_SPREAD_TARGET = 242    # HUP_Temp_Spread_Soll
    HEATING_SPREAD_ACTUAL = 243    # HUP_Temp_Spread_Ist
    CONDENSING_PRESSURE = 252       # Condensing pressure (bar/100) - from firmware
    HOT_GAS_MAX_SETPOINT = 252      # T-HG max: hot-gas trip setpoint (~115 C on this unit); same address as CONDENSING_PRESSURE
    HEAT_OUTPUT = 257
    CONDENSING_TEMP = 258           # Condensing temperature (°C/10) - from firmware
    PASSIVE_COOLING_FLAG = 259
    COOLING_RELEASE_TIMER = 260     # Cooling release countdown timer (seconds)
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
    SETTLING_SECONDS = 120  # Steady-state settling time before gated values are trusted
