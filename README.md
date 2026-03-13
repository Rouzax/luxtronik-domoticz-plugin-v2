# Luxtronik Heat Pump Controller Plugin for Domoticz

## Overview

The Luxtronik plugin for Domoticz provides socket communication with Luxtronik-based heat pump controllers. Built on the **DomoticzEx framework**, this version features multi-instance support, intelligent COP tracking with steady-state gating, robust security with write protection, and comprehensive multi-language support. Building on the work of [ajarzyn](https://github.com/ajarzyn/domoticz-luxtronic2), this refactored version brings enhanced reliability and maintainability.

Also published on the [Domoticz Forum](https://forum.domoticz.com/viewtopic.php?p=44176)

## Features

- **DomoticzEx Framework:**  
  Modern plugin architecture with improved device management, callback support, and multi-instance capability.

- **Real-Time Monitoring:**  
  Retrieve live data from heat pump sensors including temperature, pressure, power consumption, compressor metrics, and more.
  
- **Multi-Instance Support:**  
  Run multiple plugin instances for homes with more than one heat pump. Each instance uses a unique DeviceID derived from HardwareID for complete isolation.

- **Intelligent COP Tracking:**  
  Separate COP (Coefficient of Performance) measurements for heating mode, DHW (domestic hot water) mode, and combined total. Values are only reported during active heating cycles with steady-state gating to prevent idle readings from skewing efficiency statistics.

- **Smart Device Updates:**  
  Update tracker that only sends changes immediately while graphing devices resend values every ~2 minutes when unchanged, ensuring accurate long-term trend analysis without excessive database writes.

- **Secure Write Protection:**  
  All write operations are validated against an explicit allowlist of safe addresses. Unknown or unauthorized write attempts are blocked to protect the heat pump's EEPROM.

- **Stable Device IDs:**  
  Devices use HardwareID-based identifiers that never change, even when renaming hardware or changing IP addresses. This prevents orphaned devices and ensures reliable automation rules.

- **Intelligent Name Updates:**  
  Device names and selector options update automatically when changing languages, but user customizations are preserved. Only names matching known translations are updated.

- **Configurable Update Interval:**  
  The heartbeat interval is validated and clamped to a safe range of 10-60 seconds for stability.

- **Multi-Language Support:**  
  Available languages include:
  - English
  - Polish
  - Dutch
  - German
  - French

- **Granular Debug Logging:**  
  Multiple debug levels for efficient troubleshooting:
  - **None:** Errors only
  - **Basic:** Lifecycle events, summaries, write confirmations
  - **Device:** Device updates and state changes
  - **Comms:** Connection handling, protocol messages, commands
  - **Verbose:** Tracker details, data conversion internals
  - **All:** Everything enabled

## Requirements

- Domoticz home automation system (2024.4+ recommended for full DomoticzEx support)
- A Luxtronik-based heat pump controller with network access
- Python 3.x

## Installation

1. **Navigate to the Domoticz plugins directory**:
   ```sh
   cd /path/to/domoticz/plugins
   ```

2. **Clone the repository**:
   ```sh
   git clone https://github.com/Rouzax/luxtronik-domoticz-plugin-v2.git luxtronik-domoticz-plugin-v2
   ```
   
3. **Restart Domoticz**:
   ```sh
   sudo systemctl restart domoticz.service
   ```

4. **Enable the plugin**:
   - In Domoticz, navigate to **Setup** → **Hardware**
   - Add a new hardware device and select **Luxtronik Heat Pump Controller v2**
   - Enter the configuration details
   - Click **Add**
  
## Screenshots

<details>
<summary>Click to expand screenshots</summary>

### Utility Devices
![Utility Devices](https://github.com/user-attachments/assets/2e36ea32-a578-4e54-835f-b9cfd6835e24)

### Temperature Devices
![Temperature Devices](https://github.com/user-attachments/assets/2f9d1438-6572-4afe-9de3-2fe99d69ca8e)

### Switch Devices
![Switch Devices](https://github.com/user-attachments/assets/fa9195f6-0780-49e6-961f-196bc92405cb)

</details>

## Configuration

| Parameter       | Description                                         | Default     |
|-----------------|-----------------------------------------------------|-------------|
| Address         | IP address of the Luxtronik controller              | `127.0.0.1` |
| Port            | TCP port of the controller                          | `8889`      |
| Max COP Value   | Maximum COP to accept; higher values are discarded as measurement artifacts. Leave empty to disable | `30`        |
| Update Interval | Data update interval in seconds (clamped to 10-60) | `20`        |
| Language        | Interface language                                  | `English`   |
| Pump Power Compensation | Add estimated circulation pump power to compressor reading for more accurate COP | `Off` |
| Pump Power Ranges (W) | HUP min, HUP max, VBO min, VBO max — pump power range in watts | `2,60,3,140` |
| Debug Level     | Debug log level for troubleshooting                 | `None`      |

### COP Accuracy Recommendation

For accurate COP averages over time, enable the following Domoticz setting:

**Settings → Log History → 'Only add newly received values to the Log'**

When disabled (default), Domoticz fills in the last received value every 5 minutes even when the heat pump is idle, skewing COP averages. When enabled, no values are logged during idle periods, giving accurate daily/monthly efficiency averages.

> **Note:** This is a system-wide Domoticz setting that affects all devices, not just this plugin.

The controller's power reading only measures compressor power. Enable **Pump Power Compensation** to include estimated circulation pump power for true system COP. The default pump power ranges match the WZSV 92K3M — check your manual for other models.

### Security Notes

- The Luxtronik protocol uses plain TCP without encryption (hardware limitation)
- Keep your heat pump on a trusted LAN/VLAN; do not expose to the internet
- Use a VPN if remote access is required

## Created Devices

The plugin creates 66 devices organized into 14 logical groups. Devices marked with `Used=0` are created but set to unused by default—enable them in Domoticz if needed.

### Device Groups Overview

| Group | Units | Description | Count |
|-------|-------|-------------|-------|
| 1 | 1 | Status Overview | 1 |
| 2 | 10-16 | User Controls *(all writable)* | 7 |
| 3 | 30-32 | Power Input | 3 |
| 4 | 40-42 | Heat Output | 3 |
| 5 | 50-52 | Efficiency (COP) | 3 |
| 6 | 60-67 | Heating Circuit | 8 |
| 7 | 80 | DHW | 1 |
| 8 | 90-93 | Environment | 4 |
| 9 | 100-106 | Source Circuit | 7 |
| 10 | 120-131 | Mixing Circuits | 4 |
| 11 | 140-144 | Compressor | 5 |
| 12 | 160-170 | Refrigerant Circuit | 11 |
| 13 | 180-185 | Statistics & Counters | 6 |
| 14 | 200-202 | Diagnostics | 3 |

---

### Group 1: Status Overview (Unit 1)

| Unit | Device | Description |
|------|--------|-------------|
| 1 | Working mode | Current operating state text (Heating, DHW, Cooling, Idle) |

---

### Group 2: User Controls (Units 10-16) — ALL WRITABLE

All control devices are consolidated in this group for easy access.

| Unit | Device | Description |
|------|--------|-------------|
| 10 | Heating mode | Selector: Automatic, 2nd heat source, Party, Holidays, Off |
| 11 | Hot water mode | Selector: Automatic, 2nd heat source, Party, Holidays, Off |
| 12 | DHW Power Mode | Selector: Normal, Luxury |
| 13 | Cooling | On/Off switch |
| 14 | Temp adjust | Heating curve adjustment (-5 to +5°C) *(unused by default)* |
| 15 | DHW temp target | Hot water target setpoint (30-65°C) *(unused by default)* |
| 16 | Room temp setpoint | Room temperature setpoint (15-30°C) |

---

### Group 3: Power Input (Units 30-32)

Electrical power consumption from the grid.

| Unit | Device | Description |
|------|--------|-------------|
| 30 | Power total | Total electrical consumption (kWh meter) |
| 31 | Power heating | Consumption during heating mode only |
| 32 | Power DHW | Consumption during DHW mode only |

---

### Group 4: Heat Output (Units 40-42)

Thermal energy delivered to the building.

| Unit | Device | Description |
|------|--------|-------------|
| 40 | Heat out total | Total thermal energy produced (kWh meter) |
| 41 | Heat out heating | Heat output during heating mode |
| 42 | Heat out DHW | Heat output during DHW mode |

---

### Group 5: Efficiency (Units 50-52)

Coefficient of Performance measurements. **Gated**: only updates during steady-state operation.

| Unit | Device | Description |
|------|--------|-------------|
| 50 | COP total | Overall system efficiency (heat out ÷ power in) |
| 51 | COP heating | Efficiency for heating mode only |
| 52 | COP DHW | Efficiency for DHW mode only |

---

### Group 6: Heating Circuit (Units 60-67)

Complete heating circuit monitoring including temperatures, spreads, pump, and flow.

| Unit | Device | Description |
|------|--------|-------------|
| 60 | Heat supply temp | Flow temperature to heating system |
| 61 | Heat return temp | Return temperature from heating system |
| 62 | Return temp target | Calculated target return temperature |
| 63 | Heating ΔT | Temperature difference (supply - return), **gated** (also updates during passive cooling) |
| 64 | Heating ΔT target | Controller's ΔT setpoint *(unused by default)* |
| 65 | Heating ΔT actual | Controller's measured ΔT *(unused by default)* |
| 66 | Heating pump | Circulation pump speed (%) |
| 67 | Heating flow | Flow rate through heating circuit (l/h) *(unused by default)* |

---

### Group 7: DHW (Unit 80)

Domestic hot water tank temperature.

| Unit | Device | Description |
|------|--------|-------------|
| 80 | DHW temp | Current hot water temperature |

---

### Group 8: Environment (Units 90-93)

Outdoor and room temperature sensors.

| Unit | Device | Description |
|------|--------|-------------|
| 90 | Outside temp | Ambient outdoor temperature |
| 91 | Outside temp avg | Time-averaged outdoor temperature *(unused by default)* |
| 92 | Room temp | Current room temperature sensor |
| 93 | Room temp target | Room temperature target *(unused by default)* |

---

### Group 9: Source Circuit (Units 100-106)

Ground loop / brine circuit monitoring including temperatures, spreads, pump, and flow.

| Unit | Device | Description |
|------|--------|-------------|
| 100 | Source inlet temp | Temperature from ground/well source |
| 101 | Source outlet temp | Temperature returning to ground/well |
| 102 | Source ΔT | Source temperature difference, **gated** (also updates during passive cooling) |
| 103 | Source ΔT target | Controller's source ΔT setpoint *(unused by default)* |
| 104 | Source ΔT actual | Controller's measured source ΔT *(unused by default)* |
| 105 | Source pump | Brine circulation pump speed (%) |
| 106 | Source flow | Flow rate through source circuit (l/h) |

---

### Group 10: Mixing Circuits (Units 120-131)

Optional mixing valve circuits for zone control.

| Unit | Device | Description |
|------|--------|-------------|
| 120 | Circuit 1 temp | Mixing circuit 1 current temp *(unused by default)* |
| 121 | Circuit 1 target | Mixing circuit 1 target temp *(unused by default)* |
| 130 | Circuit 2 temp | Mixing circuit 2 current temp *(unused by default)* |
| 131 | Circuit 2 target | Mixing circuit 2 target temp *(unused by default)* |

---

### Group 11: Compressor (Units 140-144)

Compressor operational metrics.

| Unit | Device | Description |
|------|--------|-------------|
| 140 | Compressor freq | Current compressor speed (Hz) |
| 141 | Compressor target freq | Controller's target frequency *(unused by default)* |
| 142 | Compressor min freq | Minimum allowed frequency *(unused by default)* |
| 143 | Compressor max freq | Maximum allowed frequency *(unused by default)* |
| 144 | Compressor capacity | Load relative to maximum (%), **gated** |

---

### Group 12: Refrigerant Circuit (Units 160-167)

Refrigerant temperatures and pressures.

| Unit | Device | Description |
|------|--------|-------------|
| 160 | Hot gas temp | Compressor discharge temperature |
| 161 | Suction temp | Compressor inlet temperature |
| 162 | Discharge temp | Discharge line temperature |
| 163 | Evaporating temp | Refrigerant evaporation point |
| 164 | Liquid line temp | Liquid line temperature before EEV |
| 165 | Superheat | Refrigerant superheat (K), **gated** |
| 166 | Pressure high | High-side pressure (bar), **gated** |
| 167 | Pressure low | Low-side pressure (bar), **gated** |
| 168 | Condensing temp | Condensing temperature from firmware, **gated** *(unused by default)* |
| 169 | Subcooling | Condensing temp − liquid line temp (K), **gated** *(unused by default)* |
| 170 | Condensing pressure | Condensing pressure from firmware (bar), **gated** *(unused by default)* |

---

### Group 13: Statistics & Counters (Units 180-185)

Lifetime statistics and runtime counters.

| Unit | Device | Description |
|------|--------|-------------|
| 180 | Compressor hours | Lifetime operating hours |
| 181 | Compressor starts | Total start count |
| 182 | Compressor last cycle | Duration of last completed cycle (minutes) |
| 183 | Heating runtime | Total heating mode runtime *(unused by default)* |
| 184 | DHW runtime | Total DHW mode runtime *(unused by default)* |
| 185 | Cooling runtime | Total cooling mode runtime *(unused by default)* |

---

### Group 14: Diagnostics (Units 200-201)

System health indicators.

| Unit | Device | Description |
|------|--------|-------------|
| 200 | Error count | Number of stored errors *(unused by default)* |
| 201 | Cooling permitted | Whether cooling is currently allowed *(unused by default)* |
| 202 | Cooling release | Countdown timer until cooling is permitted (HH:MM:SS) *(unused by default)* |

---

### Notes on Gated Devices

Devices marked **gated** only update during steady-state compressor operation (when actual frequency ≥ minimum target frequency). This prevents meaningless readings from skewing statistical averages when the system is idle or ramping up. Temperature difference devices (Units 63, 102) also update during passive cooling, since circulation pumps are active and ΔT values remain physically meaningful.

### Reserved Unit Ranges

Each group has reserved unit numbers for future expansion:
- Units 2-9, 17-29, 33-39, 43-49, 53-59, 68-79, 81-89, 94-99, 107-119, 122-129, 132-139, 145-159, 171-179, 186-199, 203-209

## Debugging

Enable debug levels in the plugin configuration:

| Level | Output | Use Case |
|-------|--------|----------|
| None | Errors only | Normal operation |
| Basic | Status() messages | Lifecycle tracking, visible in Domoticz log |
| Basic + Device | + device changes | Troubleshoot device updates |
| Basic + Comms | + connection/protocol | Network issues, command failures |
| Basic + Device + Comms | Both above | General troubleshooting |
| All | Everything | Deep debugging |

Debug messages appear in the Domoticz log (**Setup → Log**). BASIC level messages also appear in the hardware status.

## Troubleshooting

### Connection Issues
- Verify the Luxtronik controller is reachable: `ping <ip-address>`
- Check the correct port (default: 8889)
- Ensure no firewall blocks the connection

### Timeout Warnings
If the update interval exceeds 30 seconds, Domoticz may show timeout warnings. This is expected behavior—the plugin continues to function correctly.

### Missing Devices
After adding the plugin, devices are created automatically. If devices appear missing:
1. Check **Setup → Devices** for unused devices
2. Enable devices by setting them to "Used"
3. Check the debug log for creation errors

### Device Names Not Translating
Device names only update automatically if they match a known translation. User-customized names are preserved. To reset to translated names, delete the device—it will be recreated on the next heartbeat.

### COP Values Seem Wrong
1. Enable "Only add newly received values" in Domoticz settings
2. Ensure you're looking at periods when the heat pump was actively running
3. COP is only logged during steady-state operation (compressor at target speed)
4. Adjust the Max COP Value setting if legitimate readings are being filtered (default 30), or leave it empty to disable filtering

### Write Commands Not Working
The plugin validates all write operations against an allowlist. Check the debug log for "WRITE BLOCKED" messages. Only the control devices (units 10-16) support write operations.

## Migration from Legacy Plugin

The new plugin uses a different key (`luxtronikex` vs `luxtronik`), allowing both plugins to run simultaneously during migration. 

See [`migration/README.md`](migration/README.md) for detailed instructions and SQL scripts.

### Quick Migration

```bash
# 1. Backup
sudo systemctl stop domoticz
cp domoticz.db domoticz.db.backup
sudo systemctl start domoticz

# 2. Install new plugin, add hardware in Domoticz as "HPNEW" or whatever name

# 3. Migrate (auto-detects both plugins)
sudo systemctl stop domoticz
sqlite3 domoticz.db < plugins/luxtronik-domoticz-plugin-v2/migration/migrate.sql
sudo systemctl start domoticz

# 4. Verify graphs, then disable old plugin and rename new one
```

## Files

| File | Purpose |
|------|---------|
| `plugin.py` | Main plugin code with DomoticzEx framework integration |
| `translations.py` | Multi-language translations for device names and descriptions |
| `README.md` | This documentation file |
| `migration/` | Migration tools for upgrading from legacy plugin |
| `migration/README.md` | Migration instructions |
| `migration/discover.sql` | Preview device mappings and data counts |
| `migration/migrate.sql` | Migrate historical data from legacy plugin |


### Development Notes

- The plugin uses the DomoticzEx framework (`import DomoticzEx`)
- Device Unit IDs are organized into 14 logical groups (see `_build_device_specs()`)
- Write operations require addresses to be in `available_writes` dictionary
- Gated converters check compressor frequency before reporting values (temperature difference converters also pass during passive cooling)
- Translations use `spec_id` as the lookup key

## Changelog

### Version 2.0.4
- Pump power compensation: estimates HUP/VBO circulation pump power from speed percentages and adds it to the compressor power reading for more accurate system COP
- Configurable pump power ranges (Mode5) with defaults for WZSV 92K3M

### Version 2.0.3
- New refrigerant diagnostics: condensing temperature, subcooling, condensing pressure (all gated, unused by default)
- New cooling release countdown timer (HH:MM:SS format, unused by default)
- Audit fixes for steady-state gating, refrigerant sensors, and robustness

### Version 2.0.2
- Temperature difference devices (heating ΔT, brine ΔT) now also update during passive cooling

### Version 2.0.1
- Single-connection refactor: heartbeat reads (READ_CALCUL + READ_PARAMS) now share one TCP connection instead of two separate connect/close cycles
- Configurable max COP limit to filter transient measurement spikes
- Fixed TCP partial read vulnerability in socket communication (`_recv_exact`)
- Fixed retry logic: MAX_RETRIES=1 actually meant zero retries (now MAX_ATTEMPTS=2)
- Clean up `_unit_specs` on plugin stop for consistent teardown
- Removed dead `onCommand` pass-through (DomoticzEx dispatches to Unit directly)

### Version 2.0.0
- **Breaking:** New plugin key `luxtronikex` (allows side-by-side installation with legacy)
- Complete refactor to DomoticzEx framework
- Multi-instance support with HardwareID-based device IDs (`luxtronikex_hw{id}`)
- Write protection with explicit address allowlist
- Steady-state gating for COP and pressure readings
- Intelligent device name updates preserving user customizations
- Heartbeat validation (clamped to 10-60 seconds)
- Added compressor runtime, start count, capacity utilization
- Added refrigerant temperatures (evaporating, condensing, discharge)
- Added spread target/actual devices for heating and source circuits
- COP logging setting check with user notification
- Enhanced debug levels (Basic, Device, Comms, Verbose)
- SQL migration scripts for historical data transfer

### Previous Versions
See the original repository for earlier changelog entries.
https://github.com/Rouzax/luxtronik-domoticz-plugin
