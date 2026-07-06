"""Device specification table for the Luxtronik plugin.

Builds the full list of DeviceSpec entries that define every Domoticz
device the plugin creates, with stable Unit IDs and the DeviceFactory
calls that wire each one to its Luxtronik protocol address.
"""

from typing import List

from addresses import LuxtronikAddress
from device_factory import DeviceFactory
from device_spec import DeviceSpec


def build_device_specs() -> List[DeviceSpec]:
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
      168-170 : Retired (legacy condensing/subcooling)
      171-174 : Refrigerant metrics (lift, approach, discharge headroom, compression ratio)
      175-179 : Reserved

    Group 13: Statistics & Counters (180-199)
    ─────────────────────────────────────────
      180-185 : Runtime counters and cycle tracking
      186-199 : Reserved for future statistics

    Group 14: Diagnostics (200-209)
    ───────────────────────────────
      200-201 : Error count and status flags
      202-209 : Reserved for future diagnostics
    """
    heating_mode_options = ["Automatic", "2nd heat source", "Party", "Holidays", "Off"]
    dhw_power_options = ["Normal", "Luxury"]

    return [
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 1: STATUS OVERVIEW (Units 1-9)
        # ═══════════════════════════════════════════════════════════════════
        # Unit 1: Current operating mode status text
        DeviceFactory.create_text_device(
            1,
            "working_mode",
            "READ_CALCUL",
            LuxtronikAddress.WORKING_MODE,
            LuxtronikAddress.POWER_TOTAL,
            0.1,
            used=1,
            image=15,
        ),
        # Units 2-9: Reserved for future status devices
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 2: USER CONTROLS (Units 10-29)
        # All writable devices in one place - the "control panel"
        # ═══════════════════════════════════════════════════════════════════
        # Unit 10: Heating operation mode selector switch [WRITABLE]
        DeviceFactory.create_selector_device(
            10,
            "heating_mode",
            "READ_PARAMS",
            LuxtronikAddress.HEATING_MODE,
            heating_mode_options,
            [0, 1, 2, 3, 4],
            LuxtronikAddress.HEATING_MODE,
            used=1,
        ),
        # Unit 11: Hot water operation mode selector switch [WRITABLE]
        DeviceFactory.create_selector_device(
            11,
            "hot_water_mode",
            "READ_PARAMS",
            LuxtronikAddress.HOT_WATER_MODE,
            heating_mode_options,
            [0, 1, 2, 3, 4],
            LuxtronikAddress.HOT_WATER_MODE,
            used=1,
            image=11,
        ),
        # Unit 12: DHW Power Mode selector switch [WRITABLE]
        DeviceFactory.create_selector_device(
            12,
            "dhw_power_mode",
            "READ_PARAMS",
            LuxtronikAddress.DHW_POWER_MODE,
            dhw_power_options,
            [0, 1],
            LuxtronikAddress.DHW_POWER_MODE,
            used=1,
            image=11,
        ),
        # Unit 13: Cooling mode enable/disable switch [WRITABLE]
        DeviceFactory.create_switch_device(
            13, "cooling_enabled", "READ_PARAMS", LuxtronikAddress.COOLING_ENABLED, used=1
        ),
        # Unit 14: Temperature offset adjustment [WRITABLE]
        DeviceFactory.create_setpoint_device(
            14,
            "temp_offset",
            "READ_PARAMS",
            LuxtronikAddress.TEMP_OFFSET,
            min_val="-5",
            max_val="5",
            used=0,
        ),
        # Unit 15: Domestic hot water target temperature setting [WRITABLE]
        DeviceFactory.create_setpoint_device(
            15,
            "dhw_temp_target",
            "READ_PARAMS",
            LuxtronikAddress.DHW_TEMP_TARGET,
            min_val="30",
            max_val="65",
            used=0,
        ),
        # Unit 16: Actual room temperature set-point [WRITABLE]
        DeviceFactory.create_setpoint_device(
            16,
            "room_temp_setpoint",
            "READ_PARAMS",
            LuxtronikAddress.ROOM_TEMP_SETPOINT,
            min_val="15",
            max_val="30",
            used=1,
        ),
        # Units 17-29: Reserved for future controls
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 3: POWER INPUT (Units 30-39)
        # Electrical consumption tracking
        # ═══════════════════════════════════════════════════════════════════
        # Unit 30: Total electrical power consumption
        DeviceFactory.create_power_device(
            30, "power_total", "READ_CALCUL", LuxtronikAddress.POWER_TOTAL, used=1
        ),
        # Unit 31: Heating mode electrical power consumption
        DeviceFactory.create_split_power_device(
            31,
            "power_heating",
            "READ_CALCUL",
            LuxtronikAddress.POWER_TOTAL,
            LuxtronikAddress.WORKING_MODE,
            [0],
            used=1,
        ),
        # Unit 32: Hot water mode electrical power consumption
        DeviceFactory.create_split_power_device(
            32,
            "power_dhw",
            "READ_CALCUL",
            LuxtronikAddress.POWER_TOTAL,
            LuxtronikAddress.WORKING_MODE,
            [1],
            used=1,
        ),
        # Units 33-39: Reserved for future power metrics
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 4: HEAT OUTPUT (Units 40-49)
        # Thermal energy delivery tracking
        # ═══════════════════════════════════════════════════════════════════
        # Unit 40: Total heat output power
        DeviceFactory.create_power_device(
            40,
            "heat_out_total",
            "READ_CALCUL",
            LuxtronikAddress.HEAT_OUTPUT,
            generated=True,
            used=1,
        ),
        # Unit 41: Heating mode heat output power
        DeviceFactory.create_split_power_device(
            41,
            "heat_out_heating",
            "READ_CALCUL",
            LuxtronikAddress.HEAT_OUTPUT,
            LuxtronikAddress.WORKING_MODE,
            [0],
            generated=True,
            used=1,
            image=15,
        ),
        # Unit 42: Hot water mode heat output power
        DeviceFactory.create_split_power_device(
            42,
            "heat_out_dhw",
            "READ_CALCUL",
            LuxtronikAddress.HEAT_OUTPUT,
            LuxtronikAddress.WORKING_MODE,
            [1],
            generated=True,
            used=1,
            image=15,
        ),
        # Units 43-49: Reserved for future heat output metrics
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 5: EFFICIENCY (Units 50-59)
        # COP and efficiency metrics
        # ═══════════════════════════════════════════════════════════════════
        # Unit 50: Overall system COP (Coefficient of Performance)
        # Filtered to only log during active heating or DHW modes
        DeviceFactory.create_cop_device(
            50,
            "cop_total",
            "READ_CALCUL",
            LuxtronikAddress.HEAT_OUTPUT,
            LuxtronikAddress.POWER_TOTAL,
            allowed_modes=[0, 1],
            used=1,
        ),  # Heating + DHW modes
        # Unit 51: COP for heating mode only
        # Only logs when system is in heating mode (mode 0) at steady-state
        DeviceFactory.create_cop_device(
            51,
            "cop_heating",
            "READ_CALCUL",
            LuxtronikAddress.HEAT_OUTPUT,
            LuxtronikAddress.POWER_TOTAL,
            allowed_modes=[0],
            used=1,
        ),  # Heating mode only
        # Unit 52: COP for DHW (domestic hot water) mode only
        # Only logs when system is in DHW mode (mode 1) at steady-state
        DeviceFactory.create_cop_device(
            52,
            "cop_dhw",
            "READ_CALCUL",
            LuxtronikAddress.HEAT_OUTPUT,
            LuxtronikAddress.POWER_TOTAL,
            allowed_modes=[1],
            used=1,
        ),  # DHW mode only
        # Units 53-59: Reserved for future efficiency metrics
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 6: HEATING CIRCUIT (Units 60-79)
        # All heating circuit devices together
        # ═══════════════════════════════════════════════════════════════════
        # --- Temperatures (Units 60-65) ---
        # Unit 60: Heat supply/flow temperature sensor
        DeviceFactory.create_temperature_device(
            60, "heat_supply_temp", "READ_CALCUL", LuxtronikAddress.HEAT_SUPPLY_TEMP, used=1
        ),
        # Unit 61: Return temperature sensor from heating system
        DeviceFactory.create_temperature_device(
            61, "heat_return_temp", "READ_CALCUL", LuxtronikAddress.HEAT_RETURN_TEMP, used=1
        ),
        # Unit 62: Calculated target return temperature
        DeviceFactory.create_temperature_device(
            62, "return_temp_target", "READ_CALCUL", LuxtronikAddress.RETURN_TEMP_TARGET, used=1
        ),
        # Unit 63: Heating temperature difference (Supply - Return)
        # Gated: ΔT approaches zero as distribution loop equilibrates when idle
        DeviceFactory.create_temp_diff_device(
            63,
            "heating_temp_diff",
            "READ_CALCUL",
            [LuxtronikAddress.HEAT_SUPPLY_TEMP, LuxtronikAddress.HEAT_RETURN_TEMP],
            gated=True,
            used=1,
        ),
        # Unit 64: Controller's heating circuit spread target (ΔT setpoint)
        DeviceFactory.create_custom_device(
            64,
            "heating_spread_target",
            "READ_CALCUL",
            LuxtronikAddress.HEATING_SPREAD_TARGET,
            "K",
            divider=10,
            used=0,
            precision="0.1",
        ),
        # Unit 65: Controller's heating circuit spread actual (measured ΔT)
        DeviceFactory.create_custom_device(
            65,
            "heating_spread_actual",
            "READ_CALCUL",
            LuxtronikAddress.HEATING_SPREAD_ACTUAL,
            "K",
            divider=10,
            used=0,
            precision="0.1",
        ),
        # --- Pump and Flow (Units 66-67) ---
        # Unit 66: Heating circulation pump speed percentage
        DeviceFactory.create_percentage_device(
            66, "heating_pump_speed", "READ_CALCUL", LuxtronikAddress.HEATING_PUMP_SPEED, used=1
        ),
        # Unit 67: Heating circuit flow rate measurement (hidden by default)
        # Note: This measures flow through the HUP pump circuit (water side)
        # Used for thermal power calculation via heat meter (WMZ)
        DeviceFactory.create_custom_device(
            67,
            "heating_flow",
            "READ_CALCUL",
            LuxtronikAddress.HEATING_FLOW,
            "L/h",
            used=0,
            image=35,
        ),
        # Units 68-79: Reserved for future heating circuit devices
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 7: DHW (Units 80-89)
        # Domestic hot water system
        # ═══════════════════════════════════════════════════════════════════
        # Unit 80: Domestic hot water current temperature
        DeviceFactory.create_temperature_device(
            80, "dhw_temp", "READ_CALCUL", LuxtronikAddress.DHW_TEMP, used=1
        ),
        # Units 81-89: Reserved for future DHW devices
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 8: ENVIRONMENT (Units 90-99)
        # Outdoor and room temperatures
        # ═══════════════════════════════════════════════════════════════════
        # Unit 90: Outside ambient temperature sensor
        DeviceFactory.create_temperature_device(
            90, "outside_temp", "READ_CALCUL", LuxtronikAddress.OUTSIDE_TEMP, used=1
        ),
        # Unit 91: Average outside temperature over time
        DeviceFactory.create_temperature_device(
            91, "outside_temp_avg", "READ_CALCUL", LuxtronikAddress.OUTSIDE_TEMP_AVG, used=0
        ),
        # Unit 92: Room temperature sensor reading
        DeviceFactory.create_temperature_device(
            92, "room_temp", "READ_CALCUL", LuxtronikAddress.ROOM_TEMP, used=1
        ),
        # Unit 93: Room temperature setpoint (read-only display)
        DeviceFactory.create_temperature_device(
            93, "room_temp_target", "READ_CALCUL", LuxtronikAddress.ROOM_TEMP_TARGET, used=0
        ),
        # Units 94-99: Reserved for future environmental devices
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 9: SOURCE CIRCUIT (Units 100-119)
        # Ground/brine loop - complete circuit in one group
        # ═══════════════════════════════════════════════════════════════════
        # --- Temperatures (Units 100-104) ---
        # Unit 100: Source inlet temperature (from ground/well)
        DeviceFactory.create_temperature_device(
            100, "source_in_temp", "READ_CALCUL", LuxtronikAddress.SOURCE_IN_TEMP, used=1
        ),
        # Unit 101: Source outlet temperature (to ground/well)
        DeviceFactory.create_temperature_device(
            101, "source_out_temp", "READ_CALCUL", LuxtronikAddress.SOURCE_OUT_TEMP, used=1
        ),
        # Unit 102: Brine temperature difference (Source in - Source out)
        # Gated: ΔT approaches zero as source loop equilibrates when idle
        DeviceFactory.create_temp_diff_device(
            102,
            "brine_temp_diff",
            "READ_CALCUL",
            [LuxtronikAddress.SOURCE_IN_TEMP, LuxtronikAddress.SOURCE_OUT_TEMP],
            gated=True,
            used=1,
        ),
        # Unit 103: Controller's source circuit spread target (ΔT setpoint)
        DeviceFactory.create_custom_device(
            103,
            "source_spread_target",
            "READ_CALCUL",
            LuxtronikAddress.SOURCE_SPREAD_TARGET,
            "K",
            divider=10,
            used=0,
            precision="0.1",
        ),
        # Unit 104: Controller's source circuit spread actual (measured ΔT)
        DeviceFactory.create_custom_device(
            104,
            "source_spread_actual",
            "READ_CALCUL",
            LuxtronikAddress.SOURCE_SPREAD_ACTUAL,
            "K",
            divider=10,
            used=0,
            precision="0.1",
        ),
        # --- Pump and Flow (Units 105-106) ---
        # Unit 105: Brine/well circulation pump speed percentage
        DeviceFactory.create_percentage_device(
            105, "brine_pump_speed", "READ_CALCUL", LuxtronikAddress.BRINE_PUMP_SPEED, used=1
        ),
        # Unit 106: Source/brine circuit flow rate measurement
        # Note: This measures flow through the VBO pump circuit (brine side)
        DeviceFactory.create_custom_device(
            106,
            "source_flow",
            "READ_CALCUL",
            LuxtronikAddress.SOURCE_FLOW,
            "l/h",
            used=1,
            image=35,
        ),
        # Units 107-119: Reserved for future source circuit devices
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 10: MIXING CIRCUITS (Units 120-139)
        # Multi-zone heating support
        # ═══════════════════════════════════════════════════════════════════
        # --- Mixing Circuit 1 (Units 120-129) ---
        # Unit 120: Mixing circuit 1 current temperature
        DeviceFactory.create_temperature_device(
            120, "mc1_temp", "READ_CALCUL", LuxtronikAddress.MC1_TEMP, used=0
        ),
        # Unit 121: Mixing circuit 1 target temperature
        DeviceFactory.create_temperature_device(
            121, "mc1_temp_target", "READ_CALCUL", LuxtronikAddress.MC1_TEMP_TARGET, used=0
        ),
        # Units 122-129: Reserved for MC1 expansion
        # --- Mixing Circuit 2 (Units 130-139) ---
        # Unit 130: Mixing circuit 2 current temperature
        DeviceFactory.create_temperature_device(
            130, "mc2_temp", "READ_CALCUL", LuxtronikAddress.MC2_TEMP, used=0
        ),
        # Unit 131: Mixing circuit 2 target temperature
        DeviceFactory.create_temperature_device(
            131, "mc2_temp_target", "READ_CALCUL", LuxtronikAddress.MC2_TEMP_TARGET, used=0
        ),
        # Units 132-139: Reserved for MC2 expansion
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 11: COMPRESSOR (Units 140-159)
        # Compressor operation and performance
        # ═══════════════════════════════════════════════════════════════════
        # Unit 140: Compressor frequency/speed
        DeviceFactory.create_custom_device(
            140,
            "compressor_freq",
            "READ_CALCUL",
            LuxtronikAddress.COMPRESSOR_FREQ,
            "Hz",
            used=1,
        ),
        # Unit 141: Controller target compressor frequency (hidden by default)
        # Compare to actual frequency to see controller tracking
        DeviceFactory.create_custom_device(
            141,
            "target_frequency",
            "READ_CALCUL",
            LuxtronikAddress.TARGET_FREQUENCY,
            "Hz",
            used=0,
        ),
        # Unit 142: Minimum frequency target (hidden by default)
        # Used in COP gating logic to detect steady-state operation
        DeviceFactory.create_custom_device(
            142,
            "min_frequency",
            "READ_CALCUL",
            LuxtronikAddress.COMPRESSOR_FREQ_MIN,
            "Hz",
            used=0,
        ),
        # Unit 143: Maximum frequency limit (hidden by default)
        # System capacity ceiling, used for capacity utilization calculation
        DeviceFactory.create_custom_device(
            143,
            "max_frequency",
            "READ_CALCUL",
            LuxtronikAddress.COMPRESSOR_FREQ_MAX,
            "Hz",
            used=0,
        ),
        # Unit 144: Compressor capacity utilization percentage
        # Shows current load relative to maximum capability
        # Gated: only updates during steady-state operation
        DeviceFactory.create_capacity_device(
            144,
            "compressor_capacity",
            "READ_CALCUL",
            LuxtronikAddress.COMPRESSOR_FREQ,
            LuxtronikAddress.COMPRESSOR_FREQ_MAX,
            used=1,
        ),
        # Unit 145: Frequency headroom (target minus actual compressor frequency)
        # Gated: only reports while compressor is running (actual > 0)
        DeviceFactory.create_freq_headroom_device(
            145,
            "freq_headroom",
            "READ_CALCUL",
            LuxtronikAddress.TARGET_FREQUENCY,
            LuxtronikAddress.COMPRESSOR_FREQ,
        ),
        # Units 146-159: Reserved for future compressor devices
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 12: REFRIGERANT CIRCUIT (Units 160-179)
        # Refrigerant temperatures and pressures
        # ═══════════════════════════════════════════════════════════════════
        # --- Temperatures (Units 160-165) ---
        # Unit 160: Hot gas temperature monitoring (compressor outlet)
        DeviceFactory.create_temperature_device(
            160, "hot_gas_temp", "READ_CALCUL", LuxtronikAddress.HOT_GAS_TEMP, used=1
        ),
        # Unit 161: Compressor suction temperature (entering compressor)
        DeviceFactory.create_temperature_device(
            161, "suction_temp", "READ_CALCUL", LuxtronikAddress.SUCTION_TEMP, used=1
        ),
        # Unit 162: Compressor body heating temperature (LIN inverter sensor)
        # Not discharge-line gas; measures the compressor housing heat rejection.
        DeviceFactory.create_temperature_device(
            162,
            "compressor_heating_temp",
            "READ_CALCUL",
            LuxtronikAddress.COMPRESSOR_HEATING_TEMP,
            used=1,
        ),
        # Unit 163: Evaporating temperature (refrigerant evaporation point)
        # Gated: meaningless during idle and passive cooling (refrigerant values)
        DeviceFactory.create_custom_device(
            163,
            "evaporating_temp",
            "READ_CALCUL",
            LuxtronikAddress.EVAPORATING_TEMP,
            "°C",
            divider=10,
            gated=True,
            precision="0.1",
            used=1,
        ),
        # Unit 164: Condensing temperature (controller's saturation temp, calc[233])
        # Same address as liquid line but confirmed as controller-computed condensing temp.
        # Gated: meaningless during idle and passive cooling (refrigerant values)
        DeviceFactory.create_custom_device(
            164,
            "condensing_temp",
            "READ_CALCUL",
            LuxtronikAddress.CONDENSING_TEMP_CALC,
            "°C",
            divider=10,
            gated=True,
            precision="0.1",
            used=1,
        ),
        # Unit 165: Superheat monitoring
        # Gated: stale readings during idle corrupt operating averages
        DeviceFactory.create_custom_device(
            165,
            "superheat",
            "READ_CALCUL",
            LuxtronikAddress.SUPERHEAT,
            "K",
            divider=10,
            gated=True,
            used=1,
        ),
        # --- Pressures (Units 166-167) ---
        # Unit 166: High pressure monitoring
        # Gated: equilibrates to ambient when off, not operationally meaningful
        DeviceFactory.create_custom_device(
            166,
            "high_pressure",
            "READ_CALCUL",
            LuxtronikAddress.HIGH_PRESSURE,
            "bar",
            divider=100,
            gated=True,
            used=1,
        ),
        # Unit 167: Low pressure monitoring
        # Gated: equilibrates to ambient when off, not operationally meaningful
        DeviceFactory.create_custom_device(
            167,
            "low_pressure",
            "READ_CALCUL",
            LuxtronikAddress.LOW_PRESSURE,
            "bar",
            divider=100,
            gated=True,
            used=1,
        ),
        # Units 168-170: Retired (calc[258] condensing temp, subcooling, condensing pressure).
        # Replaced by calc[233] condensing temp on unit 164 and calc-based lift/approach.
        # Unit 171: Refrigerant lift (condensing temp - evaporating temp)
        # Uses calc[233] condensing temp directly (no P-T curve conversion).
        # Gated: only meaningful during steady-state compressor operation
        DeviceFactory.create_temp_diff_device(
            171,
            "refrigerant_lift",
            "READ_CALCUL",
            [LuxtronikAddress.CONDENSING_TEMP_CALC, LuxtronikAddress.EVAPORATING_TEMP],
            divider=10,
            gated=True,
        ),
        # Unit 172: Condensing-supply ΔT (condensing temp - heat supply water temp).
        # Signed: positive = water below condensing (condenser headroom, normal in
        # low-temp heating); negative = desuperheat-dominated (high water temps / DHW,
        # where the discharge gas heats the leaving water above the condensing temp).
        # TVL (calc[10]) is the condenser-outlet water, before the 3-way valve, so this
        # is the same physical reference in heating and DHW. Uses calc[233] directly.
        # Gated: only meaningful during steady-state compressor operation.
        DeviceFactory.create_temp_diff_device(
            172,
            "condensing_supply_delta",
            "READ_CALCUL",
            [LuxtronikAddress.CONDENSING_TEMP_CALC, LuxtronikAddress.HEAT_SUPPLY_TEMP],
            divider=10,
            gated=True,
        ),
        # Unit 173: Discharge headroom (T-HG max setpoint - actual hot gas temp)
        # Margin remaining before the hot-gas trip limit is reached (~115 C).
        # Gated: only meaningful during steady-state compressor operation
        DeviceFactory.create_discharge_headroom_device(
            173,
            "discharge_headroom",
            "READ_CALCUL",
            LuxtronikAddress.HOT_GAS_MAX_SETPOINT,
            LuxtronikAddress.HOT_GAS_TEMP,
        ),
        # Unit 174: Compression ratio (HD / ND on absolute pressures)
        # Rising ratio over time flags refrigerant-circuit degradation.
        # Gated: only meaningful during steady-state compressor operation
        DeviceFactory.create_compression_ratio_device(
            174,
            "compression_ratio",
            "READ_CALCUL",
            LuxtronikAddress.HIGH_PRESSURE,
            LuxtronikAddress.LOW_PRESSURE,
            used=1,
        ),
        # Units 175-179: Reserved for future refrigerant devices
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 13: STATISTICS & COUNTERS (Units 180-199)
        # Operational history and lifetime tracking
        # ═══════════════════════════════════════════════════════════════════
        # Unit 180: Lifetime compressor operating hours
        # Useful for maintenance scheduling
        DeviceFactory.create_runtime_device(
            180,
            "compressor_runtime",
            "READ_CALCUL",
            LuxtronikAddress.COMPRESSOR_RUNTIME,
            used=1,
            image=21,
        ),
        # Unit 181: Total compressor start count
        # Indicates cycling behavior and compressor wear
        DeviceFactory.create_counter_device(
            181,
            "compressor_starts",
            "READ_CALCUL",
            LuxtronikAddress.COMPRESSOR_STARTS,
            "starts",
            used=1,
        ),
        # Unit 182: Duration of last completed compressor cycle
        # Updates only when a cycle completes (sparse updates)
        DeviceFactory.create_last_cycle_device(
            182,
            "last_cycle",
            "READ_CALCUL",
            LuxtronikAddress.CURRENT_CYCLE_TIME,
            used=1,
            image=21,
        ),
        # Unit 183: Total operating hours in heating mode (hidden by default)
        DeviceFactory.create_runtime_device(
            183,
            "heating_runtime",
            "READ_CALCUL",
            LuxtronikAddress.HEATING_RUNTIME,
            used=0,
            image=21,
        ),
        # Unit 184: Total operating hours in hot water mode (hidden by default)
        DeviceFactory.create_runtime_device(
            184, "dhw_runtime", "READ_CALCUL", LuxtronikAddress.DHW_RUNTIME, used=0, image=21
        ),
        # Unit 185: Total operating hours in passive cooling mode (hidden by default)
        DeviceFactory.create_runtime_device(
            185,
            "cooling_runtime",
            "READ_CALCUL",
            LuxtronikAddress.COOLING_RUNTIME,
            used=0,
            image=21,
        ),
        # Units 186-199: Reserved for future statistics
        # ═══════════════════════════════════════════════════════════════════
        # GROUP 14: DIAGNOSTICS (Units 200-209)
        # Error tracking and status flags
        # ═══════════════════════════════════════════════════════════════════
        # Unit 200: Error count in controller memory (hidden by default)
        # Quick health indicator - check logs if count increases
        DeviceFactory.create_counter_device(
            200,
            "error_count",
            "READ_CALCUL",
            LuxtronikAddress.ERROR_COUNT,
            "errors",
            used=0,
            image=13,
        ),
        # Unit 201: Cooling permitted status (hidden by default)
        # Read-only indicator showing if passive cooling is currently released
        # Based on outdoor temperature and settings - not user controllable
        DeviceFactory.create_status_switch_device(
            201,
            "cooling_permitted",
            "READ_CALCUL",
            LuxtronikAddress.COOLING_PERMITTED,
            used=0,
            image=16,
        ),
        # Unit 202: Cooling release countdown timer
        # Shows remaining time before cooling mode is permitted
        DeviceFactory.create_custom_device(
            202,
            "cooling_release_timer",
            "READ_CALCUL",
            LuxtronikAddress.COOLING_RELEASE_TIMER,
            "min",
            divider=60,
            used=0,
            image=21,
        ),
        # Units 203-209: Reserved for future diagnostics
    ]
