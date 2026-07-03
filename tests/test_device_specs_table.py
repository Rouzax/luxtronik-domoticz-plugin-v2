from device_spec import DeviceSpec
from device_specs_table import build_device_specs


def test_returns_nonempty_list_of_devicespec():
    specs = build_device_specs()
    assert isinstance(specs, list) and len(specs) > 0
    assert all(isinstance(s, DeviceSpec) for s in specs)


def test_all_unit_ids_unique():
    specs = build_device_specs()
    unit_ids = [s.unit_id for s in specs]
    assert len(unit_ids) == len(set(unit_ids)), "duplicate unit_id in device spec table"
