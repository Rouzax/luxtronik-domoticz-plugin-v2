"""Device specification dataclasses for the Luxtronik plugin."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from converters import DataConverter, WriteConverter


@dataclass
class Field:
    """Represents a writable field with allowed values."""

    name: str = "Unknown"
    values: List[int] = field(default_factory=list)

    def get_name(self) -> str:
        return self.name

    def get_val(self) -> List[int]:
        return self.values


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
