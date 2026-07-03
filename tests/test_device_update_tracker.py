"""Tests for DeviceUpdateTracker."""

from device_update_tracker import DeviceUpdateTracker


class FakeUnit:
    def __init__(self, uid=1, type_=80, subtype=0, nvalue=0, svalue=""):
        self.ID, self.Type, self.SubType = uid, type_, subtype
        self.nValue, self.sValue = nvalue, svalue


def test_nvalue_change_detected():
    t = DeviceUpdateTracker()
    changed, reason, _ = t.needs_update(FakeUnit(nvalue=0), {"nValue": 1})
    assert changed and reason == "Values changed"


def test_svalue_formatting_not_a_change():
    # Use a non-graphing type (244): a graphing device with no value change
    # falls into the periodic-refresh branch ("Interval update" on the first
    # call, then "Next update in Ns"), never "No changes". The plain
    # "No changes" reason is only reachable for non-graphing devices, which is
    # what this test exercises.
    t = DeviceUpdateTracker()
    changed, reason, _ = t.needs_update(FakeUnit(type_=244, svalue="23.40"), {"sValue": "23.4"})
    assert not changed and reason == "No changes"


def test_svalue_real_change_detected():
    t = DeviceUpdateTracker()
    changed, _, _ = t.needs_update(FakeUnit(svalue="23.4"), {"sValue": "24.1"})
    assert changed


def test_non_graphing_no_periodic_update():
    t = DeviceUpdateTracker()
    u = FakeUnit(type_=244, svalue="1")  # switch type, non-graphing
    changed, reason, _ = t.needs_update(u, {"sValue": "1"})
    assert not changed and reason == "No changes"


def test_graphing_periodic_refresh(monkeypatch):
    import device_update_tracker as m

    t = DeviceUpdateTracker()
    u = FakeUnit(type_=80, svalue="5")
    times = iter([1000.0, 1000.0 + m.DeviceUpdateTracker.GRAPH_UPDATE_INTERVAL + 1])
    monkeypatch.setattr(m.time, "monotonic", lambda: next(times))
    t.needs_update(u, {"sValue": "5"})  # first call seeds last-update time
    changed, reason, _ = t.needs_update(u, {"sValue": "5"})  # interval elapsed
    assert changed and reason == "Interval update"
