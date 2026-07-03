"""Device specification factory for the Luxtronik plugin.

Extracted from plugin.py. Builds DeviceSpec instances for every device kind
the plugin creates, wiring each one to its read/write converter. Runs only
inside create_devices (post-onStart-bridge), so context.translator is live
at runtime.
"""

from typing import List, Optional

import context
from converters import (
    AvailableWritesConverter,
    BooleanSwitchConverter,
    CapacityConverter,
    CommandToNumberConverter,
    CompressionRatioConverter,
    COPCalculatorConverter,
    DischargeHeadroomConverter,
    FloatConverter,
    FreqHeadroomConverter,
    GatedFloatConverter,
    GatedTempDiffConverter,
    InstantPowerConverter,
    InstantPowerSplitConverter,
    IntegerValueConverter,
    LastCycleConverter,
    LevelWithDividerConverter,
    NumberConverter,
    RuntimeHoursConverter,
    SelectorSwitchConverter,
    TempDiffConverter,
    TextStateConverter,
)
from device_spec import DeviceSpec


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
    _freq_headroom_converter = FreqHeadroomConverter()
    _compression_ratio_converter = CompressionRatioConverter()
    _discharge_headroom_converter = DischargeHeadroomConverter()

    @classmethod
    def create_temperature_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        divider: float = 10,
        used: int = 1,
    ) -> DeviceSpec:
        """Create a temperature sensor device specification."""
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._float_converter,
            read_args=(divider,),
            device_params={"TypeName": "Temperature", "Used": used},
        )

    @classmethod
    def create_custom_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        unit: str,
        divider: float = 1,
        used: int = 1,
        gated: bool = False,
        precision: str = "1",
        image: Optional[int] = None,
    ) -> DeviceSpec:
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
        params = {"TypeName": "Custom", "Used": used, "Options": {"Custom": f"{precision};{unit}"}}
        if image is not None:
            params["Image"] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=converter,
            read_args=(divider,),
            device_params=params,
        )

    @classmethod
    def create_setpoint_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        divider: float = 10,
        write_divider: float = 0.1,
        min_val: str = "-5",
        max_val: str = "5",
        step: str = "0.5",
        used: int = 0,
    ) -> DeviceSpec:
        """Create a setpoint device specification."""
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._float_converter,
            read_args=(divider,),
            device_params={
                "Type": 242,
                "Subtype": 1,
                "Used": used,
                "Options": {
                    "ValueStep": step,
                    "ValueMin": min_val,
                    "ValueMax": max_val,
                    "ValueUnit": "°C",
                },
            },
            write_converter=LevelWithDividerConverter(write_divider),
        )

    @classmethod
    def create_selector_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        options: List[str],
        mapping: List[int],
        writes_idx: int,
        used: int = 1,
        image: int = 15,
    ) -> DeviceSpec:
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
                "TypeName": "Selector Switch",
                "Image": image,
                "Used": used,
                "Options": {
                    "LevelActions": "|" * len(options),
                    "LevelNames": context.translator.translate_selector_options(options),
                    "LevelOffHidden": "false",
                    "SelectorStyle": "1",
                },
            },
            write_converter=AvailableWritesConverter(10, writes_idx),
            selector_options=options,  # Store for language change updates
        )

    @classmethod
    def create_switch_device(
        cls, unit_id: int, spec_id: str, command: str, address: int, used: int = 1, image: int = 16
    ) -> DeviceSpec:
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
            device_params={"TypeName": "Switch", "Image": image, "Used": used},
            write_converter=cls._command_to_number,
        )

    @classmethod
    def create_power_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        used: int = 1,
        generated: bool = False,
        image: Optional[int] = None,
    ) -> DeviceSpec:
        """Create a power meter device specification.

        Args:
            generated: If True, sets Switchtype=4 for energy export display
            image: Optional icon image number. If None, defaults to 15 for generated meters
        """
        params = {"TypeName": "kWh", "Used": used, "Options": {"EnergyMeterMode": "1"}}
        if generated:
            params["Switchtype"] = 4
            params["Image"] = image if image is not None else 15
        elif image is not None:
            params["Image"] = image

        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._instant_power_converter,
            read_args=(),
            device_params=params,
        )

    @classmethod
    def create_split_power_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        state_idx: int,
        valid_states: List[int],
        used: int = 1,
        generated: bool = False,
        image: Optional[int] = None,
    ) -> DeviceSpec:
        """Create a split power meter device specification.

        Args:
            generated: If True, sets Switchtype=4 for energy export display
            image: Optional icon image number. If None, defaults to 15 for generated meters
        """
        params = {"TypeName": "kWh", "Used": used, "Options": {"EnergyMeterMode": "1"}}
        if generated:
            params["Switchtype"] = 4
            params["Image"] = image if image is not None else 15
        elif image is not None:
            params["Image"] = image

        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._instant_power_split_converter,
            read_args=([state_idx, valid_states],),
            device_params=params,
        )

    @classmethod
    def create_cop_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        heat_idx: int,
        power_idx: int,
        used: int = 1,
        allowed_modes: Optional[List[int]] = None,
    ) -> DeviceSpec:
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
            device_params={"TypeName": "Custom", "Used": used, "Options": {"Custom": "1;COP"}},
        )

    @classmethod
    def create_text_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        power_idx: int,
        power_threshold: float,
        used: int = 1,
        image: Optional[int] = None,
    ) -> DeviceSpec:
        """Create a text status device specification.

        Args:
            image: Optional icon image number
        """
        params = {"TypeName": "Text", "Used": used}
        if image is not None:
            params["Image"] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._text_state_converter,
            read_args=([power_idx, power_threshold],),
            device_params=params,
        )

    @classmethod
    def create_percentage_device(
        cls, unit_id: int, spec_id: str, command: str, address: int, used: int = 1
    ) -> DeviceSpec:
        """Create a percentage device specification."""
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._float_converter,
            read_args=(1,),
            device_params={"TypeName": "Percentage", "Used": used},
        )

    @classmethod
    def create_temp_diff_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        indices: List[int],
        divider: float = 10,
        used: int = 1,
        gated: bool = False,
    ) -> DeviceSpec:
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
            device_params={"TypeName": "Custom", "Used": used, "Options": {"Custom": "1;K"}},
        )

    @classmethod
    def create_runtime_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        used: int = 1,
        image: Optional[int] = None,
    ) -> DeviceSpec:
        """Create a runtime hours device specification.

        Converts seconds from controller to hours for display.
        Used for compressor lifetime runtime tracking.

        Args:
            image: Optional icon image number
        """
        params = {"TypeName": "Custom", "Used": used, "Options": {"Custom": "1;h"}}
        if image is not None:
            params["Image"] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._runtime_hours_converter,
            read_args=(),
            device_params=params,
        )

    @classmethod
    def create_counter_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        unit_label: str = "count",
        used: int = 1,
        image: Optional[int] = None,
    ) -> DeviceSpec:
        """Create a counter device specification.

        Displays integer counts like compressor starts.

        Args:
            image: Optional icon image number
        """
        params = {"TypeName": "Custom", "Used": used, "Options": {"Custom": f"1;{unit_label}"}}
        if image is not None:
            params["Image"] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._integer_value_converter,
            read_args=(),
            device_params=params,
        )

    @classmethod
    def create_capacity_device(
        cls, unit_id: int, spec_id: str, command: str, actual_idx: int, max_idx: int, used: int = 1
    ) -> DeviceSpec:
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
            device_params={"TypeName": "Custom", "Used": used, "Options": {"Custom": "1;%"}},
        )

    @classmethod
    def create_last_cycle_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        used: int = 1,
        image: Optional[int] = None,
    ) -> DeviceSpec:
        """Create a last cycle duration device specification.

        Tracks cycle completions and displays duration in minutes.
        Requires a CycleTracker instance to be passed during updates.
        Note: The tracker is passed in the read_args and must be set up
        by the plugin after initialization.

        Args:
            image: Optional icon image number
        """
        params = {"TypeName": "Custom", "Used": used, "Options": {"Custom": "1;min"}}
        if image is not None:
            params["Image"] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._last_cycle_converter,
            read_args=(None,),  # Placeholder - tracker set during plugin init
            device_params=params,
        )

    @classmethod
    def create_status_switch_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        address: int,
        used: int = 1,
        image: Optional[int] = None,
    ) -> DeviceSpec:
        """Create a read-only status switch device specification.

        Shows on/off status based on controller flag without write capability.
        Used for status indicators like cooling_permitted.

        Args:
            image: Optional icon image number
        """
        params = {"Type": 244, "Subtype": 73, "Switchtype": 0, "Used": used}
        if image is not None:
            params["Image"] = image
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=address,
            read_converter=cls._boolean_switch_converter,
            read_args=(),
            device_params=params,
            # No write_converter - this is read-only
        )

    @classmethod
    def create_freq_headroom_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        target_addr: int,
        actual_addr: int,
        used: int = 1,
    ) -> DeviceSpec:
        """Create a frequency headroom device (target minus actual compressor frequency).

        Uses FreqHeadroomConverter: target_addr - actual_addr in Hz.
        Gated to compressor-on (actual > 0); no settling requirement.
        Unit is Hz.

        Args:
            target_addr: Controller target frequency address
            actual_addr: Actual compressor frequency address
        """
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=[target_addr, actual_addr],
            read_converter=cls._freq_headroom_converter,
            read_args=(),
            device_params={"TypeName": "Custom", "Used": used, "Options": {"Custom": "1;Hz"}},
        )

    @classmethod
    def create_compression_ratio_device(
        cls, unit_id: int, spec_id: str, command: str, hp_addr: int, np_addr: int, used: int = 1
    ) -> DeviceSpec:
        """Create a compression ratio device (HD / ND on absolute pressures).

        Uses CompressionRatioConverter: (hp_addr/100 + atm) / (np_addr/100 + atm).
        Gated to steady-state compressor operation.
        Dimensionless ratio (no unit suffix).

        Args:
            hp_addr: High-pressure gauge address (raw value / 100 = bar gauge)
            np_addr: Low-pressure gauge address (raw value / 100 = bar gauge)
        """
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=[hp_addr, np_addr],
            read_converter=cls._compression_ratio_converter,
            read_args=(),
            device_params={"TypeName": "Custom", "Used": used, "Options": {"Custom": "1;"}},
        )

    @classmethod
    def create_discharge_headroom_device(
        cls,
        unit_id: int,
        spec_id: str,
        command: str,
        setpoint_addr: int,
        sensor_addr: int,
        used: int = 1,
    ) -> DeviceSpec:
        """Create a discharge headroom device (hot-gas trip setpoint minus hot-gas temp).

        Uses DischargeHeadroomConverter: setpoint_addr/10 - sensor_addr/10 (K).
        Gated to steady-state compressor operation only (no passive-cooling bypass).
        Unit is Kelvin (temperature margin).

        Args:
            setpoint_addr: T-HG max setpoint address (raw value / 10 = deg C)
            sensor_addr: Hot-gas temperature address (raw value / 10 = deg C)
        """
        return DeviceSpec(
            unit_id=unit_id,
            spec_id=spec_id,
            command=command,
            address=[setpoint_addr, sensor_addr],
            read_converter=cls._discharge_headroom_converter,
            read_args=(10,),
            device_params={"TypeName": "Custom", "Used": used, "Options": {"Custom": "1;K"}},
        )
