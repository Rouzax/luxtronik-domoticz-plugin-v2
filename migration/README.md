# Migration from Legacy Plugin

These scripts migrate historical data from the legacy Luxtronik plugin (`luxtronik-domoticz-plugin`) to the new DomoticzEx version (`luxtronik-domoticz-plugin-v2`).

## Prerequisites

- Both plugins installed and configured
- Old plugin: `plugins/luxtronik-domoticz-plugin/` (key: `luxtronik`)
- New plugin: `plugins/luxtronik-domoticz-plugin-v2/` (key: `luxtronikex`)

## Migration Steps

### 1. Backup your database

```bash
sudo systemctl stop domoticz
cp domoticz.db domoticz.db.backup
sudo systemctl start domoticz
```

### 2. Install and configure new plugin

Add new hardware in Domoticz (Setup → Hardware) with a temporary name like "HPNEW". Let it run briefly to create all devices.

### 3. (Optional) Preview migration

```bash
sqlite3 domoticz.db < plugins/luxtronik-domoticz-plugin-v2/migration/discover.sql
```

### 4. Run migration

```bash
sudo systemctl stop domoticz
sqlite3 domoticz.db < plugins/luxtronik-domoticz-plugin-v2/migration/migrate.sql
sudo systemctl start domoticz
```

### 5. Verify and cleanup

1. Check graphs on new plugin devices show historical data
2. Disable/delete the old plugin hardware entry
3. Rename new hardware to your preferred name

## What gets migrated

The migration script automatically handles:

- **Temperature data** - All temperature sensor history and daily aggregates
- **Meter data** - Energy consumption/production history (kWh devices)
- **Percentage data** - Pump speeds, COP values, custom sensors
- **Switch history** - Selector and switch state changes
- **Energy counters** - Cumulative kWh counters are synced to continue seamlessly
- **Hourly statistics** - KWHStats patterns are preserved

## How it works

- **Auto-detects** both plugins by their plugin key (no manual configuration needed)
- Uses **Unit ID mapping** (independent of device names or language settings)
- Only migrates data **older than** new device's first entry (no duplicates)
- Cleans up any artifacts from the new device running before migration

## Unit ID Mapping

| Old Unit | New Unit | Type | Description |
|:--------:|:--------:|------|-------------|
| 1 | 60 | Temperature | Heat supply temp |
| 2 | 61 | Temperature | Heat return temp |
| 3 | 62 | Temperature | Return temp target |
| 4 | 90 | Temperature | Outside temp |
| 5 | 91 | Temperature | Outside temp avg |
| 6 | 80 | Temperature | DHW temp |
| 7 | 15 | Setpoint | DHW temp target |
| 8 | 100 | Temperature | Source inlet temp |
| 9 | 101 | Temperature | Source outlet temp |
| 10 | 120 | Temperature | Circuit 1 temp |
| 11 | 121 | Temperature | Circuit 1 target |
| 12 | 130 | Temperature | Circuit 2 temp |
| 13 | 131 | Temperature | Circuit 2 target |
| 14 | 10 | Selector | Heating mode |
| 15 | 11 | Selector | Hot water mode |
| 16 | 13 | Switch | Cooling |
| 17 | 14 | Setpoint | Temp adjust |
| 18 | 1 | Text | Working mode |
| 19 | 106 | Custom | Source flow |
| 20 | 140 | Custom | Compressor freq |
| 21 | 92 | Temperature | Room temp |
| 22 | 93 | Temperature | Room temp target |
| 23 | 30 | kWh | Power total |
| 24 | 31 | kWh | Power heating |
| 25 | 32 | kWh | Power DHW |
| 26 | 40 | kWh | Heat out total |
| 27 | 41 | kWh | Heat out heating |
| 28 | 42 | kWh | Heat out DHW |
| 29 | 50 | Custom | COP total |
| 30 | 66 | Percentage | Heating pump |
| 31 | 105 | Percentage | Source pump |
| 32 | 160 | Temperature | Hot gas temp |
| 33 | 161 | Temperature | Suction temp |
| 34 | 165 | Custom | Superheat |
| 35 | 166 | Custom | Pressure high |
| 36 | 167 | Custom | Pressure low |
| 37 | 102 | Custom | Source ΔT |
| 38 | 63 | Custom | Heating ΔT |
| 39 | 12 | Selector | DHW Power Mode |
| 40 | 16 | Setpoint | Room temp setpoint |
| 41 | 51 | Custom | COP heating |
| 42 | 52 | Custom | COP DHW |

## Files

| File | Description |
|------|-------------|
| `discover.sql` | Preview device mapping and data counts before migration |
| `migrate.sql` | Perform the full data migration |