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

This shows:
- Device mappings (old unit → new unit)
- **kWh counter comparison** (critical for correct graphs!)
- Historical data counts to be migrated

### 4. Run migration

```bash
sudo systemctl stop domoticz
sqlite3 domoticz.db < plugins/luxtronik-domoticz-plugin-v2/migration/migrate.sql
sudo systemctl start domoticz
```

### 5. Verify and cleanup

1. Check graphs on new plugin devices show historical data
2. **Important:** Verify kWh device monthly/yearly charts show correct values (not flat lines or negative values)
3. Disable/delete the old plugin hardware entry
4. Rename new hardware to your preferred name

## How it works

### Data Migration

- **Auto-detects** both plugins by their plugin key (no manual configuration)
- Uses **Unit ID mapping** (independent of device names or language)
- Only migrates data **older than** new device's first entry (no duplicates)
- Migrates: Temperature, Meter (kWh), Percentage, and LightingLog tables
- Migrates both short-term data and Calendar (daily aggregate) data

### kWh Counter Synchronization (Critical!)

For kWh devices (power consumption and heat output), Domoticz stores a cumulative energy counter in the device's `sValue` field:

```
sValue = "instant_power;cumulative_energy_wh"
Example: "3500.0;2279919.35" = 3500W instant, 2,279,919 Wh cumulative
```

**Problem:** When a new device is created, its counter starts at 0. But migrated Calendar data has counters in the millions (Wh accumulated over months/years). When Domoticz calculates daily usage:

```
Today's counter:     2,278 Wh (new device, fresh start)
Yesterday's counter: 2,233,455 Wh (from migrated data)
Calculated usage:    -2,231,177 Wh  ← WRONG!
```

**Solution:** The migration script copies `sValue` from old devices to new devices, so the counter continues from where it left off:

```
Today's counter:     2,279,919 Wh (synced from old device)
Yesterday's counter: 2,233,455 Wh (from migrated data)
Calculated usage:    46,464 Wh  ← CORRECT!
```

### Unit ID Mapping

The migration uses fixed Unit ID mapping (independent of language/device names):

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
| **23** | **30** | **kWh** | **Power total** |
| **24** | **31** | **kWh** | **Power heating** |
| **25** | **32** | **kWh** | **Power DHW** |
| **26** | **40** | **kWh** | **Heat out total** |
| **27** | **41** | **kWh** | **Heat out heating** |
| **28** | **42** | **kWh** | **Heat out DHW** |
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

**Bold** = kWh devices that require counter synchronization

## Troubleshooting

### Monthly/Yearly graphs show flat line at 0 or negative values

This happens when the kWh counter wasn't synced. Run this SQL to check:

```sql
-- Show kWh device counters for both plugins
SELECT 
    h.Extra AS Plugin,
    d.ID AS Idx,
    d.Name,
    d.sValue
FROM DeviceStatus d
INNER JOIN Hardware h ON d.HardwareID = h.ID
WHERE h.Extra IN ('luxtronik', 'luxtronikex')
  AND d.Type = 243 AND d.SubType = 29
ORDER BY d.Unit, h.Extra;
```

If new plugin devices show small counter values (< 10,000) while old devices show large values (> 1,000,000), run the migration script again to sync.

### Manual counter sync (if needed)

```sql
-- Example: Sync heat output heating counter
-- Replace OLD_IDX and NEW_IDX with actual device IDs

UPDATE DeviceStatus 
SET sValue = (SELECT sValue FROM DeviceStatus WHERE ID = OLD_IDX)
WHERE ID = NEW_IDX;
```

## Files

| File | Description |
|------|-------------|
| `discover.sql` | Preview device mapping, counter comparison, and data counts |
| `migrate.sql` | Perform data migration AND counter synchronization |