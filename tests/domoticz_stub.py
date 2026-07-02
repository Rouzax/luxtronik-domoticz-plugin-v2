"""Minimal DomoticzEx fake for unit-testing the domoticz_api seam.

Models only what the seam touches: logging/Debugging/Heartbeat call recording,
and a Unit/Devices/Units structure whose Unit.Create() registers into Devices.
A fuller stub (onStart/onHeartbeat integration) is deferred to refactor step 4.
"""

calls = {"status": [], "debug": [], "error": [], "debugging": [], "heartbeat": []}
Devices = {}


def reset():
    for v in calls.values():
        v.clear()
    Devices.clear()


class _Device:
    def __init__(self, device_id):
        self.DeviceID = device_id
        self.Units = {}


class Unit:
    def __init__(self, Name="", DeviceID="", Unit=0, **params):
        self.Name = Name
        self.DeviceID = DeviceID
        self.Unit = Unit
        self.params = params
        self.nValue = 0
        self.sValue = ""
        self.updated = False

    def Create(self):
        Devices.setdefault(self.DeviceID, _Device(self.DeviceID)).Units[self.Unit] = self

    def Update(self, **kwargs):
        self.updated = True


def Status(message):
    calls["status"].append(message)


def Debug(message):
    calls["debug"].append(message)


def Error(message):
    calls["error"].append(message)


def Debugging(mask):
    calls["debugging"].append(mask)


def Heartbeat(seconds):
    calls["heartbeat"].append(seconds)
