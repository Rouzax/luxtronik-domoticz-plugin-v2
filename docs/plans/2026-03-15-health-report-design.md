# Auto Health Report — Design Document

## Overview

Automatic health monitoring and reporting for the Luxtronik heat pump plugin. Accumulates real-time statistics into monthly buckets, scores system health across 5 weighted categories, and generates self-contained HTML reports.

## Architecture

**Approach:** Separate module (`health_monitor.py`) alongside plugin.py, following the `translations.py` pattern.

**Components:**
- `StatsAccumulator` — collects per-heartbeat data into monthly buckets using Welford's online algorithm
- `HealthScorer` — calculates category scores from accumulated stats
- `ReportGenerator` — produces self-contained HTML reports

**Integration:** Plugin.py gets minimal changes — import, 2 new devices, `feed()` call in heartbeat, save on stop.

## Plugin Settings Architecture

### Dual-mode: Extended Settings with Legacy Fallback

The Domoticz extended plugin settings PR adds support for `<group>`, `type="number"`, `type="boolean"`, `visible_when`, and `<slider>` fields. Settings are accessed via a `Settings` JSON dict (separate from `Parameters`).

Legacy Domoticz silently ignores `<group>` elements — no errors.

**Strategy:**
- Core settings (Address, Port, Mode1-3, Mode6) remain as legacy params — they work fine
- Pump power compensation moves to extended settings only (drop Mode4/Mode5)
- Health monitor configuration uses extended settings only
- Legacy Domoticz: health monitor runs with defaults and auto-detection, no pump power compensation UI

**Detection:**
```python
def _has_extended_settings(self) -> bool:
    try:
        return isinstance(Settings, dict) and len(Settings) > 0
    except NameError:
        return False
```

### XML Definition

```xml
<params>
    <!-- Core settings (legacy, always work) -->
    <param field="Address" label="Heat Pump IP Address" width="200px" required="true" default="127.0.0.1"/>
    <param field="Port" label="Heat Pump Port" width="60px" required="true" default="8889"/>
    <param field="Mode1" label="Max COP Value" width="75px" required="false" default="30"/>
    <param field="Mode2" label="Update Interval" width="150px" required="true" default="20"/>
    <param field="Mode3" label="Language" width="150px">...</param>
    <param field="Mode6" label="Debug Level" width="150px">...</param>

    <!-- Extended: Pump Power Compensation -->
    <group label="Pump Power Compensation">
        <param field="PumpCompEnabled" type="boolean"
               label="Enable Pump Power Compensation" default="false"/>
        <param field="HUPMin" type="number" label="HUP Min (W)"
               min="0" max="500" default="2" visible_when="PumpCompEnabled=true"/>
        <param field="HUPMax" type="number" label="HUP Max (W)"
               min="0" max="500" default="60" visible_when="PumpCompEnabled=true"/>
        <param field="VBOMin" type="number" label="VBO Min (W)"
               min="0" max="500" default="3" visible_when="PumpCompEnabled=true"/>
        <param field="VBOMax" type="number" label="VBO Max (W)"
               min="0" max="500" default="140" visible_when="PumpCompEnabled=true"/>
    </group>

    <!-- Extended: Health Monitor -->
    <group label="Health Monitor">
        <param field="HealthEnabled" type="boolean"
               label="Enable Health Monitoring" default="true"/>
        <param field="SystemTypeOverride" label="System Type Override"
               visible_when="HealthEnabled=true">
            <options>
                <option label="Auto-detect" value="auto" default="true"/>
                <option label="Ground Source (Brine)" value="ground"/>
                <option label="Air Source" value="air"/>
            </options>
        </param>
        <param field="Refrigerant" label="Refrigerant"
               visible_when="HealthEnabled=true">
            <options>
                <option label="R407C" value="r407c" default="true"/>
                <option label="R410A" value="r410a"/>
                <option label="R32" value="r32"/>
                <option label="R290 (Propane)" value="r290"/>
                <option label="R134a" value="r134a"/>
            </options>
        </param>
        <param field="ReportSchedule" label="Report Schedule"
               visible_when="HealthEnabled=true">
            <options>
                <option label="Monthly" value="monthly" default="true"/>
                <option label="Quarterly" value="quarterly"/>
            </options>
        </param>
    </group>
</params>
```

### Settings Normalization

```python
def _load_settings(self) -> dict:
    if self._has_extended_settings():
        return {
            'pump_enabled': Settings.get('PumpCompEnabled', 'false') == 'true',
            'hup_min': float(Settings.get('HUPMin', '2')),
            'hup_max': float(Settings.get('HUPMax', '60')),
            'vbo_min': float(Settings.get('VBOMin', '3')),
            'vbo_max': float(Settings.get('VBOMax', '140')),
            'health_enabled': Settings.get('HealthEnabled', 'true') == 'true',
            'system_type_override': Settings.get('SystemTypeOverride', 'auto'),
            'refrigerant': Settings.get('Refrigerant', 'r407c'),
            'report_schedule': Settings.get('ReportSchedule', 'monthly'),
        }
    else:
        return {
            'pump_enabled': False,
            'hup_min': 2, 'hup_max': 60,
            'vbo_min': 3, 'vbo_max': 140,
            'health_enabled': True,
            'system_type_override': 'auto',  # Auto-detect from calc[78]
            'refrigerant': 'r407c',
            'report_schedule': 'monthly',
        }
```

## System Type Auto-Detection

The heat pump type code at `calc[78]` (`ID_WEB_Code_WP_akt`) identifies the system. The naming convention encodes the source type:

| Code prefix | Meaning | System type |
|-------------|---------|-------------|
| SW, SWC | Sole/Wasser (Brine/Water) | Ground source |
| WW, WWC, WWB | Wasser/Wasser (Water/Water) | Ground source |
| WZS, WZSD | WZSV series | Ground source |
| WZW, WZWD | WZW series | Ground source |
| MSW | MSW series | Ground source |
| KSW | Kompakt Sole/Wasser | Ground source |
| L1x, L2x | Luft (Air) single/dual | Air source |
| LW, LWC | Luft/Wasser (Air/Water) | Air source |
| KLW | Kompakt Luft/Wasser | Air source |
| LD | Luft Direkt | Air source |
| HMD | Air source variant | Air source |

Suffixes: `407` = R407C refrigerant, `REV` = reversible (cooling capable), `S` = silent variant.

**Detection logic:** Match code name prefix against known patterns. Default to ground source for unknown codes (safer — ground source scoring is less dependent on outdoor temp normalization).

**Override:** User can override via `SystemTypeOverride` dropdown (default: "Auto-detect"). Override is stored in settings; auto-detect result is logged at startup for transparency.

**Refrigerant:** Not reliably detectable from protocol (only some codes have the `407` suffix). User selects via dropdown. Default R407C.

## Refrigerant Profiles

Most health scoring is relative (vs baseline, % change, year-over-year). However, a few metrics benefit from refrigerant-specific parameters:

```python
REFRIGERANT_PROFILES = {
    'r407c': {'discharge_max': 105, 'glide': 5.0, 'subcooling_sensitivity': 1.0},
    'r410a': {'discharge_max': 120, 'glide': 0.1, 'subcooling_sensitivity': 1.0},
    'r32':   {'discharge_max': 130, 'glide': 1.0, 'subcooling_sensitivity': 1.0},
    'r290':  {'discharge_max': 100, 'glide': 0.0, 'subcooling_sensitivity': 1.5},
    'r134a': {'discharge_max': 110, 'glide': 0.0, 'subcooling_sensitivity': 1.0},
}
```

### What each parameter does

**`discharge_max` (°C):** Absolute discharge temperature ceiling. Added as a sub-metric in the Compressor category. Approaching this limit indicates compressor stress regardless of baseline trends. Different refrigerants have different thermal decomposition limits.

| Refrigerant | Discharge ceiling | Why |
|-------------|-------------------|-----|
| R407C | 105°C | Lower thermal stability |
| R410A | 120°C | Higher pressure, hotter operation |
| R32 | 130°C | Highest discharge temps of common refrigerants |
| R290 | 100°C | Conservative limit for flammable refrigerant |
| R134a | 110°C | Moderate |

**`glide` (K):** Temperature glide between bubble point and dew point. Affects interpretation of superheat and subcooling:
- Superheat is measured against dew point (suction side)
- Subcooling is measured against bubble point (liquid side)
- R407C has ~5K glide — the controller may or may not account for this internally
- Used in report text to contextualize readings, and for pressure-temperature consistency checks

**`subcooling_sensitivity`:** Multiplier on subcooling drop thresholds. Systems with smaller refrigerant charges (R290 propane systems typically have very low charge due to flammability limits) are more sensitive to charge loss. A 1K subcooling drop on an R290 system is more concerning than on a large R407C charge.

### Impact on scoring

| Category | What changes per refrigerant |
|----------|------------------------------|
| Refrigerant Health | Subcooling drop thresholds scaled by `subcooling_sensitivity` |
| Compressor | Discharge temp absolute ceiling from `discharge_max` |
| Report text | Glide context, refrigerant-specific interpretation notes |
| All other metrics | Universal — relative comparisons, no refrigerant dependency |

### Scoring: Discharge Temperature Ceiling (added to Compressor category)

| Sub-metric | 100 | 70 | 40 | 0 |
|-----------|-----|----|----|---|
| Discharge temp vs ceiling | <80% of max | 80-90% | 90-95% | >95% |

Example for R407C (max 105°C): 100 = <84°C, 70 = 84-95°C, 40 = 95-100°C, 0 = >100°C

### Scoring: Subcooling (adjusted)

Base thresholds scaled by `subcooling_sensitivity`:

| Sub-metric | 100 | 70 | 40 | 0 |
|-----------|-----|----|----|---|
| Subcooling vs baseline | Within 1K/s | 1-2K/s drop | 2-3K/s drop | >3K/s drop |

Where `s` = `subcooling_sensitivity`. For R290 (s=1.5): 100 = within 0.67K, 70 = 0.67-1.33K drop, etc.

## Data Collection

Every heartbeat, the plugin feeds relevant values to the accumulator. Only steady-state readings are sampled for gated metrics.

### Tracked Metrics (per monthly bucket)

| Metric | Aggregation | Source | Gated? |
|--------|------------|--------|--------|
| COP heating/DHW/total | min, max, mean, count, stddev | heat_output / power_total | Yes |
| Superheat | min, max, mean, count, bins (0-3K, 3-10K, 10K+) | calc[165] | Yes |
| Subcooling | min, max, mean, count | calc[169] | Yes |
| High/low pressure | min, max, mean | calc[166], calc[167] | Yes |
| Discharge temp | min, max, mean | calc[160] | Yes |
| Source inlet/outlet | min, max, mean | calc[19], calc[20] | No |
| Source ΔT | min, max, mean | calc[102] | During operation |
| HUP/VBO speed | min, max, mean | calc[241], calc[183] | When >0 |
| Compressor frequency | min, max, mean | calc[140] | When >0 |
| Outside temp | min, max, mean | calc[90] | No |

### Counter Snapshots (at month rollover)

| Counter | Source |
|---------|--------|
| Compressor hours | calc[56] |
| Compressor starts | calc[57] |
| Heating/DHW/Cooling hours | calc[64,65,66] |
| Error count | calc[105] |

### Running Statistics

Welford's online algorithm: one pass, no raw data stored. Each metric needs count, mean, M2 (for stddev), min, max. Superheat adds 3 bin counters. ~20 metrics × 5 values × 13 months ≈ 1300 numbers total.

## Persistence

**File:** `health_state_hw{HardwareID}.json` alongside plugin.py (per-instance to support multi-instance setups)

**Structure:**
```json
{
  "version": 1,
  "system": {
    "model": "WZSV 92K3M",
    "first_seen": "2026-03-14"
  },
  "baselines": {
    "cop_heating_ref": 11.4,
    "superheat_mean_ref": 5.6,
    "source_inlet_mean_ref": 13.3,
    "set_from_month": "2026-12"
  },
  "monthly_buckets": {
    "2026-03": {
      "cop_heating": {"count": 4523, "mean": 11.2, "m2": 234.5, "min": 8.1, "max": 16.2},
      "superheat": {"count": 4523, "mean": 5.8, "m2": 89.2, "min": 1.2, "max": 12.1, "bins": [498, 3012, 1013]},
      "counters": {"compressor_hours": 9102, "compressor_starts": 3801}
    }
  },
  "last_report": "2026-03-01T00:00:00"
}
```

**Behaviors:**
- Save frequency: hourly
- Bucket rollover: on calendar month change, finalize and snapshot counters
- Retention: 13 months (oldest pruned when 14th appears)
- Baselines: auto-set from first full month, can be re-baselined
- Corruption resilience: write to temp file, atomic rename; corrupt/missing → start fresh

## Health Scoring

5 weighted categories, each scored 0-100. Category score = worst sub-metric. Overall = weighted average.

### Refrigerant Health (30%)

| Sub-metric | 100 (healthy) | 70 (watch) | 40 (concern) | 0 (critical) |
|-----------|--------------|------------|--------------|--------------|
| Superheat mean | 4-8 K | 3-4 or 8-10 K | 2-3 or 10-12 K | <2 or >12 K |
| Superheat % in optimal range | >60% | 40-60% | 25-40% | <25% |
| Subcooling vs baseline | Within 1K | 1-2K drop | 2-3K drop | >3K drop |
| Pressure ratio | 2.0-3.0 | 1.8-2.0 or 3.0-3.5 | 1.5-1.8 or 3.5-4.0 | <1.5 or >4.0 |

### Efficiency (25%)

| Sub-metric | 100 | 70 | 40 | 0 |
|-----------|-----|----|----|---|
| COP heating vs baseline | Within 10% | 10-20% drop | 20-30% drop | >30% drop |
| COP DHW vs baseline | Within 10% | 10-20% drop | 20-30% drop | >30% drop |
| COP heating vs same month last year | Within 10% | 10-20% drop | 20-30% drop | >30% drop |

### Ground Loop (20%)

| Sub-metric | 100 | 70 | 40 | 0 |
|-----------|-----|----|----|---|
| Source inlet vs same month last year | Within 1°C | 1-2°C drop | 2-3°C drop | >3°C drop |
| Source ΔT mean | <4.5 K | 4.5-5.5 K | 5.5-6.5 K | >6.5 K |
| Pump speed trend (HUP+VBO) | Stable (±5%) | 5-15% increase | 15-25% increase | >25% increase |

### Compressor (15%)

| Sub-metric | 100 | 70 | 40 | 0 |
|-----------|-----|----|----|---|
| Avg cycle length | >1.5 h | 1.0-1.5 h | 0.5-1.0 h | <0.5 h |
| Starts per runtime hour | <0.7 | 0.7-1.0 | 1.0-1.5 | >1.5 |
| Discharge temp vs baseline | Within 3°C | 3-6°C rise | 6-10°C rise | >10°C rise |
| Discharge temp vs ceiling | <80% of max | 80-90% | 90-95% | >95% (refrigerant-specific) |

### System (10%)

| Sub-metric | 100 | 70 | 40 | 0 |
|-----------|-----|----|----|---|
| New errors this month | 0 | 1-2 | 3-5 | >5 |
| DHW share of runtime | <45% | 45-55% | 55-65% | >65% |

### Score Interpretation

| Score | Label | Color |
|-------|-------|-------|
| 90-100 | Healthy | Green |
| 70-89 | Good | Green |
| 50-69 | Watch | Yellow |
| 30-49 | Concern | Orange |
| 0-29 | Critical | Red |

### Missing Data

Metrics without data are excluded; remaining sub-metrics reweighted. Entire categories without data have their weight redistributed proportionally.

### System Type Profiles

**Ground source:** All 5 categories active as described above.

**Air source:** Ground Loop category replaces source-specific metrics with:
- COP vs outdoor temp normalization (instead of flat baseline comparison)
- Defrost frequency tracking (replaces source temp YoY)
- Fan speed trending (replaces VBO pump speed)

Refrigerant pressure thresholds are refrigerant-specific but superheat/subcooling ranges are broadly similar across types.

## Report Output

### Single HTML File

One self-contained file — `health_hw{HardwareID}.html` alongside plugin.py — regenerated from the state JSON on every report trigger. Contains all months in one browsable page. No external dependencies, inline CSS/JS.

The HTML is a **view**, not the data store. If `health.html` is corrupted or deleted, it's regenerated from the JSON with no data loss. The JSON is the single source of truth.

**Page structure:**
1. Header — system info, current score with color badge
2. Score timeline — compact chart showing 12 months of health scores (trend at a glance)
3. Current month — full detail expanded by default
   - Score breakdown: 5 category cards with score, trend arrow (↑↓→), worst sub-metric
   - Detail sections: one per category with data, thresholds, recommended actions
   - Counter summary: runtime deltas, cycle stats
4. Previous months — collapsible accordion sections, click to expand any month
5. Footer — generation time, settings used, data coverage

**File size:** ~50-100KB for 13 months of data with inline styling. Trivial.

### Domoticz Devices

**Unit 210 — Health Score (text device, Group 14: Diagnostics)**
Shows: `94 - Healthy (Mar 2026)` or `62 - Watch: Superheat drifting high (Mar 2026)`
Numeric prefix enables graphing the score over time.

**Unit 211 — Generate Report (On/Off button, Group 14: Diagnostics, writable)**
User clicks On → report regenerates from JSON → device resets to Off.

### Triggers

- Scheduled: 1st of each month (or quarter), first heartbeat
- On-demand: Unit 211 button press
- Both regenerate the full `health.html` from current JSON state

## Integration with plugin.py

### Changes Required

1. `import json, os` and `from health_monitor import HealthMonitor`
2. Two new devices in `_build_device_specs()` (Units 210, 211)
3. `HealthMonitor` instance in `__init__`
4. `health_monitor.load()` in `onStart`
5. `health_monitor.feed(data_store)` after device updates in `_update_all_devices`
6. `health_monitor.save()` in `onStop`
7. Unit 211 `onDeviceModified` triggers `health_monitor.generate_report()`
8. Settings normalization via `_load_settings()` with extended/legacy detection
9. Remove Mode4/Mode5 params from XML (pump compensation moves to extended settings only)

### Interface

```python
class HealthMonitor:
    def load(self, state_dir: str, settings: dict) -> None: ...
    def feed(self, data_store: DataStore) -> None: ...
    def generate_report(self) -> Tuple[int, str]: ...  # (score, summary_text)
    def save(self) -> None: ...
```

## Migration

When upgrading from legacy to extended Domoticz:
- Mode4/Mode5 pump compensation settings are lost
- User re-enables in new UI (5 seconds — tick checkbox, defaults are correct)
- Health monitor starts fresh with data accumulation
- No migration code needed

## Performance (Raspberry Pi safe)

The health monitor is designed to be lightweight enough for low-powered devices like Raspberry Pi 3/4.

### Per-heartbeat: `feed()` — ~50μs

- ~20 floating point min/max comparisons
- ~20 Welford online updates (3 multiplications + 2 additions each)
- 3 superheat bin counter increments
- 1 steady-state check (already computed by plugin, reused)

For comparison: the TCP socket read to the heat pump takes 50-200ms. The stats work is 1000x cheaper.

### Hourly: `save()` — ~5-10ms

JSON serialize ~1300 numbers, write ~10KB file with atomic rename.

### Monthly: `generate_report()` — ~0.5-2s

HTML generation with inline CSS, score calculations across 13 months, string formatting. This is the heaviest operation but happens at most once per month (or on button press).

### Memory: ~40-50KB resident

- ~1300 numbers × 8 bytes = ~10KB (monthly buckets)
- HTML template strings: ~20-30KB
- Trivial on any Pi with 1+ GB RAM

### Heartbeat Guard

The `feed()` call should be skipped if the current heartbeat had a connection failure (no valid data to accumulate). This prevents recording garbage and avoids adding latency to an already-slow error recovery cycle.

```python
# In _update_all_devices, only feed if data was successfully read
if 'READ_CALCUL' in data_store:
    self.health_monitor.feed(data_store)
```

The hourly save and report generation happen at the end of the heartbeat, after all device updates. Even the worst case (2s report generation on a slow Pi) adds negligible time to a heartbeat that already takes 5-10s for TCP communication.

## Notes

- R407C refrigerant (1.25 kg charge) — default thresholds based on WZSV 92K3M baseline data
- System type auto-detected from calc[78] (HeatpumpCode), with manual override available
- Refrigerant selected by user (not reliably detectable from protocol)
- Pump speed trending covers both HUP and VBO under Ground Loop category
- Air source profile is designed but not implemented in v1 — ground source only initially
- Controller is used across many brands (Alpha InnoTec, Novelan, Siemens, etc.) — auto-detection covers all
