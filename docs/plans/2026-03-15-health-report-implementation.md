# Health Report Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add automatic health monitoring that accumulates statistics, scores system health across 5 categories, and generates a self-contained HTML report.

**Architecture:** New `health_monitor.py` module with three components (StatsAccumulator, HealthScorer, ReportGenerator). Plugin.py gets minimal integration: import, 2 devices, `feed()` call, save on stop. Extended Domoticz settings for configuration with legacy fallback. See `docs/plans/2026-03-15-health-report-design.md` for full design rationale.

**Tech Stack:** Python (standard library only — json, os, time, math, datetime, tempfile), DomoticzEx framework (plugin integration only)

**Phasing:** Tasks 1-5 are the core module (no Domoticz dependency, testable standalone). Tasks 6-8 require plugin integration and extended Domoticz settings.

---

### Task 1: Welford Statistics and Monthly Buckets

**Files:**
- Create: `health_monitor.py`

**Step 1: Create WelfordAccumulator dataclass**

The building block for all metric tracking. Implements Welford's online algorithm for streaming mean/variance with min/max tracking.

```python
"""Health monitoring for Luxtronik heat pump plugin."""

import json
import math
import os
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any

# Type alias matching plugin.py
DataStore = Dict[str, list]


@dataclass
class WelfordAccumulator:
    """Online statistics accumulator using Welford's algorithm.

    Tracks count, mean, variance, min, max in a single pass.
    Memory: 5 floats per metric. No raw data stored.
    """
    count: int = 0
    mean: float = 0.0
    m2: float = 0.0
    min_val: float = float('inf')
    max_val: float = float('-inf')

    def update(self, value: float) -> None:
        """Add a new observation."""
        self.count += 1
        delta = value - self.mean
        self.mean += delta / self.count
        delta2 = value - self.mean
        self.m2 += delta * delta2
        self.min_val = min(self.min_val, value)
        self.max_val = max(self.max_val, value)

    @property
    def variance(self) -> float:
        """Population variance."""
        if self.count < 2:
            return 0.0
        return self.m2 / self.count

    @property
    def stddev(self) -> float:
        """Population standard deviation."""
        return math.sqrt(self.variance)

    def to_dict(self) -> dict:
        """Serialize for JSON persistence."""
        d = {'count': self.count, 'mean': self.mean, 'm2': self.m2}
        if self.min_val != float('inf'):
            d['min'] = self.min_val
        if self.max_val != float('-inf'):
            d['max'] = self.max_val
        return d

    @classmethod
    def from_dict(cls, d: dict) -> 'WelfordAccumulator':
        """Deserialize from JSON."""
        return cls(
            count=d.get('count', 0),
            mean=d.get('mean', 0.0),
            m2=d.get('m2', 0.0),
            min_val=d.get('min', float('inf')),
            max_val=d.get('max', float('-inf')),
        )
```

**Step 2: Create SuperheatAccumulator with bin tracking**

```python
@dataclass
class SuperheatAccumulator:
    """Superheat statistics with distribution bins.

    Bins: low (0-3K), optimal (3-10K), high (>10K).
    """
    stats: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    bin_low: int = 0      # 0-3K
    bin_optimal: int = 0  # 3-10K
    bin_high: int = 0     # >10K

    def update(self, value: float) -> None:
        self.stats.update(value)
        if value < 3.0:
            self.bin_low += 1
        elif value <= 10.0:
            self.bin_optimal += 1
        else:
            self.bin_high += 1

    @property
    def optimal_pct(self) -> float:
        """Percentage of readings in optimal range."""
        total = self.bin_low + self.bin_optimal + self.bin_high
        if total == 0:
            return 0.0
        return (self.bin_optimal / total) * 100.0

    def to_dict(self) -> dict:
        d = self.stats.to_dict()
        d['bins'] = [self.bin_low, self.bin_optimal, self.bin_high]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> 'SuperheatAccumulator':
        bins = d.get('bins', [0, 0, 0])
        stats = WelfordAccumulator.from_dict(d)
        return cls(stats=stats, bin_low=bins[0], bin_optimal=bins[1], bin_high=bins[2])
```

**Step 3: Create MonthlyBucket container**

```python
@dataclass
class MonthlyBucket:
    """One calendar month of accumulated statistics."""
    month_key: str  # "YYYY-MM"

    # Gated metrics (steady-state only)
    cop_heating: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    cop_dhw: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    cop_total: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    superheat: SuperheatAccumulator = field(default_factory=SuperheatAccumulator)
    subcooling: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    pressure_high: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    pressure_low: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    discharge_temp: WelfordAccumulator = field(default_factory=WelfordAccumulator)

    # Ungated metrics
    source_inlet: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    source_outlet: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    source_delta_t: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    hup_speed: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    vbo_speed: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    compressor_freq: WelfordAccumulator = field(default_factory=WelfordAccumulator)
    outside_temp: WelfordAccumulator = field(default_factory=WelfordAccumulator)

    # Counter snapshots (taken at month end)
    counters: Dict[str, int] = field(default_factory=dict)

    # Health score (computed on report generation)
    health_score: Optional[int] = None
    health_label: Optional[str] = None

    def to_dict(self) -> dict:
        d = {}
        for name in ['cop_heating', 'cop_dhw', 'cop_total', 'subcooling',
                      'pressure_high', 'pressure_low', 'discharge_temp',
                      'source_inlet', 'source_outlet', 'source_delta_t',
                      'hup_speed', 'vbo_speed', 'compressor_freq', 'outside_temp']:
            acc = getattr(self, name)
            if acc.count > 0:
                d[name] = acc.to_dict()
        if self.superheat.stats.count > 0:
            d['superheat'] = self.superheat.to_dict()
        if self.counters:
            d['counters'] = self.counters
        if self.health_score is not None:
            d['health_score'] = self.health_score
            d['health_label'] = self.health_label
        return d

    @classmethod
    def from_dict(cls, month_key: str, d: dict) -> 'MonthlyBucket':
        bucket = cls(month_key=month_key)
        for name in ['cop_heating', 'cop_dhw', 'cop_total', 'subcooling',
                      'pressure_high', 'pressure_low', 'discharge_temp',
                      'source_inlet', 'source_outlet', 'source_delta_t',
                      'hup_speed', 'vbo_speed', 'compressor_freq', 'outside_temp']:
            if name in d:
                setattr(bucket, name, WelfordAccumulator.from_dict(d[name]))
        if 'superheat' in d:
            bucket.superheat = SuperheatAccumulator.from_dict(d['superheat'])
        bucket.counters = d.get('counters', {})
        bucket.health_score = d.get('health_score')
        bucket.health_label = d.get('health_label')
        return bucket
```

**Step 4: Commit**

```bash
git add health_monitor.py
git commit -m "feat: add Welford accumulator and monthly bucket data structures"
```

---

### Task 2: StatsAccumulator — Data Collection Engine

**Files:**
- Modify: `health_monitor.py`

**Step 1: Add protocol address constants**

These mirror `LuxtronikAddress` from plugin.py but are defined locally to keep health_monitor.py independent of the plugin module.

```python
class _Addr:
    """Protocol addresses used by the health monitor.

    Mirrors LuxtronikAddress from plugin.py to keep this module independent.
    """
    # Temperatures (÷10)
    SOURCE_IN_TEMP = 19
    SOURCE_OUT_TEMP = 20
    OUTSIDE_TEMP = 15
    HOT_GAS_TEMP = 14

    # Counters
    COMPRESSOR_RUNTIME = 56
    COMPRESSOR_STARTS = 57
    HEATING_RUNTIME = 64
    DHW_RUNTIME = 65
    COOLING_RUNTIME = 66
    ERROR_COUNT = 105

    # Working mode
    WORKING_MODE = 80
    HEATPUMP_CODE = 78

    # Inverter/LIN bus (÷10)
    SUCTION_TEMP = 176
    DISCHARGE_TEMP = 177
    SUPERHEAT = 178
    HIGH_PRESSURE = 180  # ÷100
    LOW_PRESSURE = 181   # ÷100
    BRINE_PUMP_SPEED = 183

    # Extended firmware
    COMPRESSOR_FREQ = 231       # ÷10
    COMPRESSOR_FREQ_MIN = 237   # ÷10
    EVAPORATING_TEMP = 232      # ÷10
    HEATING_PUMP_SPEED = 241    # ÷10
    HEATING_SPREAD_ACTUAL = 243 # ÷10
    SOURCE_SPREAD_ACTUAL = 240  # ÷10
    CONDENSING_PRESSURE = 252   # ÷100
    HEAT_OUTPUT = 257
    CONDENSING_TEMP = 258       # ÷10
    PASSIVE_COOLING_FLAG = 259
    POWER_TOTAL = 268

    # Subcooling = condensing_temp - liquid_line_temp
    LIQUID_LINE_TEMP = 233      # ÷10 (TFL)
```

**Step 2: Add steady-state check helper**

```python
class StatsAccumulator:
    """Collects per-heartbeat data into monthly buckets.

    Reuses the same steady-state logic as plugin.py's SteadyStateGateMixin:
    compressor must be running at or above minimum target frequency.
    """

    # Minimum readings before considering state "steady"
    MIN_POWER_W = 10.0

    def __init__(self):
        self._buckets: Dict[str, MonthlyBucket] = {}
        self._current_month: str = ''

    @property
    def current_bucket(self) -> Optional[MonthlyBucket]:
        return self._buckets.get(self._current_month)

    @property
    def buckets(self) -> Dict[str, MonthlyBucket]:
        return self._buckets

    def _is_steady_state(self, calc_data: list) -> bool:
        """Check if compressor is at steady-state operating speed."""
        try:
            actual_freq = float(calc_data[_Addr.COMPRESSOR_FREQ]) / 10.0
            min_freq = float(calc_data[_Addr.COMPRESSOR_FREQ_MIN]) / 10.0
            if actual_freq <= 0 or min_freq <= 0:
                return False
            return actual_freq >= min_freq
        except (IndexError, TypeError, ValueError):
            return False

    def _is_passive_cooling(self, calc_data: list) -> bool:
        """Check if passive cooling is active."""
        try:
            return int(calc_data[_Addr.PASSIVE_COOLING_FLAG]) == 1
        except (IndexError, TypeError, ValueError):
            return False
```

**Step 3: Add the feed() method**

```python
    def feed(self, data_store: DataStore) -> None:
        """Process one heartbeat of data.

        Called every heartbeat (10-60s). Accumulates values into
        the current month's bucket. Handles month rollover.
        """
        calc_data = data_store.get('READ_CALCUL', [])
        if not calc_data:
            return

        # Month rollover
        now = datetime.now()
        month_key = now.strftime('%Y-%m')
        if month_key != self._current_month:
            self._rollover(month_key, calc_data)

        bucket = self._buckets[self._current_month]
        steady = self._is_steady_state(calc_data)
        cooling = self._is_passive_cooling(calc_data)

        # Always-sampled metrics
        self._safe_update(bucket.outside_temp, calc_data, _Addr.OUTSIDE_TEMP, 10.0)
        self._safe_update(bucket.source_inlet, calc_data, _Addr.SOURCE_IN_TEMP, 10.0)
        self._safe_update(bucket.source_outlet, calc_data, _Addr.SOURCE_OUT_TEMP, 10.0)

        # Sampled when pumps running (speed > 0)
        try:
            hup = float(calc_data[_Addr.HEATING_PUMP_SPEED]) / 10.0
            if hup > 0:
                bucket.hup_speed.update(hup)
        except (IndexError, TypeError, ValueError):
            pass
        try:
            vbo = float(calc_data[_Addr.BRINE_PUMP_SPEED])
            if vbo > 0:
                bucket.vbo_speed.update(vbo)
        except (IndexError, TypeError, ValueError):
            pass

        # Sampled when compressor running
        try:
            freq = float(calc_data[_Addr.COMPRESSOR_FREQ]) / 10.0
            if freq > 0:
                bucket.compressor_freq.update(freq)
        except (IndexError, TypeError, ValueError):
            pass

        # Source ΔT during operation (pumps running or compressor on)
        if steady or cooling:
            self._safe_update(bucket.source_delta_t, calc_data,
                              _Addr.SOURCE_SPREAD_ACTUAL, 10.0)

        # Gated metrics (steady-state only)
        if not steady:
            return

        # COP calculation (same logic as COPCalculatorConverter)
        try:
            heat_output = float(calc_data[_Addr.HEAT_OUTPUT])
            power_input = float(calc_data[_Addr.POWER_TOTAL])
            if power_input >= self.MIN_POWER_W and heat_output > 100.0:
                cop = heat_output / power_input
                if cop <= 30.0:  # Sanity cap
                    bucket.cop_total.update(cop)
                    mode = int(calc_data[_Addr.WORKING_MODE])
                    if mode == 0:
                        bucket.cop_heating.update(cop)
                    elif mode == 1:
                        bucket.cop_dhw.update(cop)
        except (IndexError, TypeError, ValueError, ZeroDivisionError):
            pass

        # Refrigerant metrics
        self._safe_update(bucket.superheat, calc_data, _Addr.SUPERHEAT, 10.0,
                          is_superheat=True)
        self._safe_update(bucket.discharge_temp, calc_data, _Addr.HOT_GAS_TEMP, 10.0)
        self._safe_update(bucket.pressure_high, calc_data, _Addr.HIGH_PRESSURE, 100.0)
        self._safe_update(bucket.pressure_low, calc_data, _Addr.LOW_PRESSURE, 100.0)

        # Subcooling: condensing_temp - liquid_line_temp
        try:
            cond_t = float(calc_data[_Addr.CONDENSING_TEMP]) / 10.0
            liquid_t = float(calc_data[_Addr.LIQUID_LINE_TEMP]) / 10.0
            subcooling = cond_t - liquid_t
            if 0 <= subcooling <= 30:  # Sanity range
                bucket.subcooling.update(subcooling)
        except (IndexError, TypeError, ValueError):
            pass

    @staticmethod
    def _safe_update(accumulator, calc_data: list, address: int,
                     divider: float = 1.0, is_superheat: bool = False) -> None:
        """Safely read a value and update an accumulator."""
        try:
            value = float(calc_data[address]) / divider
            if is_superheat:
                accumulator.update(value)
            else:
                accumulator.update(value)
        except (IndexError, TypeError, ValueError):
            pass
```

**Step 4: Add month rollover logic**

```python
    def _rollover(self, new_month: str, calc_data: list) -> None:
        """Handle calendar month change.

        Snapshots counters on the old bucket, creates new bucket,
        prunes buckets older than 13 months.
        """
        # Snapshot counters on outgoing bucket
        if self._current_month and self._current_month in self._buckets:
            self._snapshot_counters(self._buckets[self._current_month], calc_data)

        # Create new bucket
        self._current_month = new_month
        if new_month not in self._buckets:
            self._buckets[new_month] = MonthlyBucket(month_key=new_month)

        # Prune: keep only 13 most recent months
        if len(self._buckets) > 13:
            sorted_keys = sorted(self._buckets.keys())
            for old_key in sorted_keys[:-13]:
                del self._buckets[old_key]

    def _snapshot_counters(self, bucket: MonthlyBucket, calc_data: list) -> None:
        """Take counter snapshots at end of month."""
        counter_addrs = {
            'compressor_hours': (_Addr.COMPRESSOR_RUNTIME, 1.0),
            'compressor_starts': (_Addr.COMPRESSOR_STARTS, 1.0),
            'heating_hours': (_Addr.HEATING_RUNTIME, 1.0),
            'dhw_hours': (_Addr.DHW_RUNTIME, 1.0),
            'cooling_hours': (_Addr.COOLING_RUNTIME, 1.0),
            'error_count': (_Addr.ERROR_COUNT, 1.0),
        }
        for name, (addr, div) in counter_addrs.items():
            try:
                bucket.counters[name] = int(float(calc_data[addr]) / div)
            except (IndexError, TypeError, ValueError):
                pass

    def load_buckets(self, buckets_data: dict) -> None:
        """Restore buckets from persisted state."""
        self._buckets = {}
        for month_key, data in buckets_data.items():
            self._buckets[month_key] = MonthlyBucket.from_dict(month_key, data)
        if self._buckets:
            self._current_month = max(self._buckets.keys())

    def to_dict(self) -> dict:
        """Serialize all buckets for persistence."""
        return {key: bucket.to_dict() for key, bucket in self._buckets.items()}
```

**Step 5: Commit**

```bash
git add health_monitor.py
git commit -m "feat: add StatsAccumulator with data collection and month rollover"
```

---

### Task 3: JSON Persistence

**Files:**
- Modify: `health_monitor.py`

**Step 1: Add system type detection constants**

```python
# Heat pump type codes from calc[78] (ID_WEB_Code_WP_akt)
HEATPUMP_CODES = {
    0: "ERC", 1: "SW1", 2: "SW2", 3: "WW1", 4: "WW2",
    5: "L1I", 6: "L2I", 7: "L1A", 8: "L2A", 9: "KSW",
    10: "KLW", 11: "SWC", 12: "LWC", 13: "L2G", 14: "WZS",
    15: "L1I407", 16: "L2I407", 17: "L1A407", 18: "L2A407",
    19: "L2G407", 20: "LWC407", 21: "L1AREV", 22: "L2AREV",
    23: "WWC1", 24: "WWC2", 25: "L2G404", 26: "WZW",
    27: "L1S", 28: "L1H", 29: "L2H", 30: "WZWD", 31: "ERC",
    40: "WWB_20", 41: "LD5", 42: "LD7", 43: "SW 37_45",
    44: "SW 58_69", 45: "SW 29_56", 46: "LD5 (230V)",
    47: "LD7 (230 V)", 48: "LD9", 49: "LD5 REV",
    50: "LD7 REV", 51: "LD5 REV 230V", 52: "LD7 REV 230V",
    53: "LD9 REV 230V", 54: "SW 291", 55: "LW SEC", 56: "HMD 2",
    57: "MSW 4", 58: "MSW 6", 59: "MSW 8", 60: "MSW 10",
    61: "MSW 12", 62: "MSW 14", 63: "MSW 17", 64: "MSW 19",
    65: "MSW 23", 66: "MSW 26", 67: "MSW 30", 68: "MSW 4S",
    69: "MSW 6S", 70: "MSW 8S", 71: "MSW 10S", 72: "MSW 13S",
    73: "MSW 16S", 74: "MSW2-6S", 75: "MSW4-16",
}

AIR_SOURCE_PREFIXES = ('L1', 'L2', 'LW', 'KLW', 'LD', 'HMD')

REFRIGERANT_PROFILES = {
    'r407c': {'discharge_max': 105, 'glide': 5.0, 'subcooling_sensitivity': 1.0},
    'r410a': {'discharge_max': 120, 'glide': 0.1, 'subcooling_sensitivity': 1.0},
    'r32':   {'discharge_max': 130, 'glide': 1.0, 'subcooling_sensitivity': 1.0},
    'r290':  {'discharge_max': 100, 'glide': 0.0, 'subcooling_sensitivity': 1.5},
    'r134a': {'discharge_max': 110, 'glide': 0.0, 'subcooling_sensitivity': 1.0},
}


def detect_system_type(wp_code: int) -> str:
    """Detect ground/air source from heat pump code."""
    code_name = HEATPUMP_CODES.get(wp_code, '')
    for prefix in AIR_SOURCE_PREFIXES:
        if code_name.startswith(prefix):
            return 'air'
    return 'ground'
```

**Step 2: Add HealthMonitor class with load/save**

```python
class HealthMonitor:
    """Main health monitoring coordinator.

    Manages data accumulation, persistence, scoring, and report generation.
    """

    STATE_VERSION = 1
    SAVE_INTERVAL_S = 3600  # Save state every hour

    def __init__(self):
        self.accumulator = StatsAccumulator()
        self.baselines: Dict[str, float] = {}
        self.baseline_month: Optional[str] = None
        self.system_info: Dict[str, str] = {}
        self.last_report: Optional[str] = None
        self.settings: dict = {}
        self._state_path: str = ''
        self._html_path: str = ''
        self._last_save_time: float = 0.0
        self._system_type: str = 'ground'
        self._refrigerant_profile: dict = REFRIGERANT_PROFILES['r407c']

    def load(self, state_dir: str, hw_id: str, settings: dict) -> None:
        """Initialize from persisted state and settings.

        Args:
            state_dir: Directory for state/report files (plugin directory)
            hw_id: HardwareID for multi-instance file naming
            settings: Normalized settings dict from _load_settings()
        """
        self.settings = settings
        self._state_path = os.path.join(state_dir, f'health_state_hw{hw_id}.json')
        self._html_path = os.path.join(state_dir, f'health_hw{hw_id}.html')

        # Refrigerant profile
        ref = settings.get('refrigerant', 'r407c')
        self._refrigerant_profile = REFRIGERANT_PROFILES.get(ref, REFRIGERANT_PROFILES['r407c'])

        # Load persisted state
        self._load_state()
        self._last_save_time = time.monotonic()

    def _load_state(self) -> None:
        """Load state from JSON file. Start fresh if missing or corrupt."""
        try:
            with open(self._state_path, 'r') as f:
                data = json.load(f)

            if data.get('version') != self.STATE_VERSION:
                return  # Incompatible version, start fresh

            self.system_info = data.get('system', {})
            self.baselines = data.get('baselines', {})
            self.baseline_month = self.baselines.get('set_from_month')
            self.last_report = data.get('last_report')
            self.accumulator.load_buckets(data.get('monthly_buckets', {}))
        except (FileNotFoundError, json.JSONDecodeError, KeyError, TypeError):
            pass  # Start fresh — no error, just no history yet

    def save(self) -> None:
        """Persist state to JSON with atomic write."""
        data = {
            'version': self.STATE_VERSION,
            'system': self.system_info,
            'baselines': self.baselines,
            'monthly_buckets': self.accumulator.to_dict(),
            'last_report': self.last_report,
        }

        # Atomic write: temp file + rename
        dir_name = os.path.dirname(self._state_path)
        try:
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp')
            with os.fdopen(fd, 'w') as f:
                json.dump(data, f, indent=None, separators=(',', ':'))
            os.replace(tmp_path, self._state_path)
        except OSError:
            # Clean up temp file on failure
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _maybe_save(self) -> None:
        """Save state if enough time has elapsed since last save."""
        elapsed = time.monotonic() - self._last_save_time
        if elapsed >= self.SAVE_INTERVAL_S:
            self.save()
            self._last_save_time = time.monotonic()

    def feed(self, data_store: DataStore) -> None:
        """Process one heartbeat of data.

        Called from plugin's _update_all_devices after device updates.
        """
        if not self.settings.get('health_enabled', True):
            return

        calc_data = data_store.get('READ_CALCUL', [])

        # Detect system type on first feed (or if override changes)
        override = self.settings.get('system_type_override', 'auto')
        if override != 'auto':
            self._system_type = override
        elif calc_data:
            try:
                wp_code = int(calc_data[_Addr.HEATPUMP_CODE])
                self._system_type = detect_system_type(wp_code)
            except (IndexError, TypeError, ValueError):
                pass

        # Record system info on first feed
        if not self.system_info.get('first_seen'):
            self.system_info['first_seen'] = datetime.now().strftime('%Y-%m-%d')
            if calc_data:
                try:
                    wp_code = int(calc_data[_Addr.HEATPUMP_CODE])
                    self.system_info['model_code'] = HEATPUMP_CODES.get(wp_code, f'Unknown ({wp_code})')
                except (IndexError, TypeError, ValueError):
                    pass

        self.accumulator.feed(data_store)
        self._maybe_auto_baseline()
        self._maybe_save()

    def _maybe_auto_baseline(self) -> None:
        """Auto-set baselines from first full month of data."""
        if self.baseline_month:
            return  # Already set

        # Need at least one completed month (not the current one)
        completed = [k for k in self.accumulator.buckets
                     if k != self.accumulator._current_month]
        if not completed:
            return

        # Use the most recent completed month
        month_key = max(completed)
        bucket = self.accumulator.buckets[month_key]

        if bucket.cop_heating.count > 100:  # Need meaningful sample
            self.baselines['cop_heating_ref'] = bucket.cop_heating.mean
        if bucket.cop_dhw.count > 50:
            self.baselines['cop_dhw_ref'] = bucket.cop_dhw.mean
        if bucket.superheat.stats.count > 100:
            self.baselines['superheat_mean_ref'] = bucket.superheat.stats.mean
        if bucket.subcooling.count > 100:
            self.baselines['subcooling_mean_ref'] = bucket.subcooling.mean
        if bucket.source_inlet.count > 100:
            self.baselines['source_inlet_mean_ref'] = bucket.source_inlet.mean
        if bucket.discharge_temp.count > 100:
            self.baselines['discharge_temp_mean_ref'] = bucket.discharge_temp.mean
        if bucket.hup_speed.count > 100:
            self.baselines['hup_speed_mean_ref'] = bucket.hup_speed.mean
        if bucket.vbo_speed.count > 100:
            self.baselines['vbo_speed_mean_ref'] = bucket.vbo_speed.mean

        self.baselines['set_from_month'] = month_key
        self.baseline_month = month_key
```

**Step 3: Commit**

```bash
git add health_monitor.py
git commit -m "feat: add HealthMonitor with JSON persistence and system detection"
```

---

### Task 4: Health Scoring Engine

**Files:**
- Modify: `health_monitor.py`

**Step 1: Add HealthScorer class**

```python
@dataclass
class SubScore:
    """Individual sub-metric score with explanation."""
    name: str
    score: int  # 0-100
    reason: str
    value: Optional[float] = None


@dataclass
class CategoryScore:
    """One of the 5 scoring categories."""
    name: str
    weight: float
    score: int  # 0-100 (worst sub-score)
    sub_scores: List[SubScore] = field(default_factory=list)

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight


class HealthScorer:
    """Calculates health scores from accumulated statistics.

    5 categories, each scored 0-100. Category score = worst sub-metric.
    Overall score = weighted average of categories.
    """

    @staticmethod
    def _interpolate_score(value: float, thresholds: List[Tuple[float, int]]) -> int:
        """Map a value to a score using threshold breakpoints.

        thresholds: [(boundary, score), ...] ordered from best to worst.
        Returns the score for the first threshold exceeded.
        """
        for boundary, score in thresholds:
            if value <= boundary:
                return score
        return thresholds[-1][1] if thresholds else 0

    @staticmethod
    def _range_score(value: float, optimal_low: float, optimal_high: float,
                     warn_low: float, warn_high: float,
                     concern_low: float, concern_high: float) -> int:
        """Score a value based on how far it is from an optimal range."""
        if optimal_low <= value <= optimal_high:
            return 100
        if warn_low <= value <= warn_high:
            return 70
        if concern_low <= value <= concern_high:
            return 40
        return 0

    def score_refrigerant(self, bucket: MonthlyBucket, baselines: dict,
                          profile: dict) -> CategoryScore:
        """Refrigerant Health (30%)."""
        subs = []

        # Superheat mean
        if bucket.superheat.stats.count > 0:
            sh = bucket.superheat.stats.mean
            s = self._range_score(sh, 4, 8, 3, 10, 2, 12)
            subs.append(SubScore('Superheat mean', s, f'{sh:.1f}K', sh))

        # Superheat optimal %
        if bucket.superheat.stats.count > 0:
            pct = bucket.superheat.optimal_pct
            s = self._interpolate_score(100 - pct, [(40, 100), (60, 70), (75, 40)])
            if 100 - pct > 75:
                s = 0
            subs.append(SubScore('Superheat % optimal', s, f'{pct:.0f}%', pct))

        # Subcooling vs baseline
        sens = profile.get('subcooling_sensitivity', 1.0)
        baseline_sc = baselines.get('subcooling_mean_ref')
        if bucket.subcooling.count > 0 and baseline_sc is not None:
            drop = baseline_sc - bucket.subcooling.mean
            drop_scaled = drop * sens
            if drop_scaled <= 1.0:
                s = 100
            elif drop_scaled <= 2.0:
                s = 70
            elif drop_scaled <= 3.0:
                s = 40
            else:
                s = 0
            subs.append(SubScore('Subcooling vs baseline', s,
                                 f'{drop:+.1f}K (sens={sens})', drop))

        # Pressure ratio
        if bucket.pressure_high.count > 0 and bucket.pressure_low.count > 0:
            if bucket.pressure_low.mean > 0:
                ratio = bucket.pressure_high.mean / bucket.pressure_low.mean
                s = self._range_score(ratio, 2.0, 3.0, 1.8, 3.5, 1.5, 4.0)
                subs.append(SubScore('Pressure ratio', s, f'{ratio:.2f}', ratio))

        if not subs:
            return CategoryScore('Refrigerant Health', 0.30, 100)
        return CategoryScore('Refrigerant Health', 0.30, min(s.score for s in subs), subs)

    def score_efficiency(self, bucket: MonthlyBucket, baselines: dict,
                         year_ago_bucket: Optional[MonthlyBucket]) -> CategoryScore:
        """Efficiency (25%)."""
        subs = []

        for name, acc_name, baseline_key in [
            ('COP heating', 'cop_heating', 'cop_heating_ref'),
            ('COP DHW', 'cop_dhw', 'cop_dhw_ref'),
        ]:
            acc = getattr(bucket, acc_name)
            ref = baselines.get(baseline_key)
            if acc.count > 0 and ref and ref > 0:
                drop_pct = (ref - acc.mean) / ref * 100
                if drop_pct <= 10:
                    s = 100
                elif drop_pct <= 20:
                    s = 70
                elif drop_pct <= 30:
                    s = 40
                else:
                    s = 0
                subs.append(SubScore(f'{name} vs baseline', s,
                                     f'{drop_pct:+.0f}%', drop_pct))

        # YoY comparison
        if year_ago_bucket and year_ago_bucket.cop_heating.count > 0:
            if bucket.cop_heating.count > 0:
                yoy_ref = year_ago_bucket.cop_heating.mean
                if yoy_ref > 0:
                    drop_pct = (yoy_ref - bucket.cop_heating.mean) / yoy_ref * 100
                    if drop_pct <= 10:
                        s = 100
                    elif drop_pct <= 20:
                        s = 70
                    elif drop_pct <= 30:
                        s = 40
                    else:
                        s = 0
                    subs.append(SubScore('COP heating YoY', s,
                                         f'{drop_pct:+.0f}%', drop_pct))

        if not subs:
            return CategoryScore('Efficiency', 0.25, 100)
        return CategoryScore('Efficiency', 0.25, min(s.score for s in subs), subs)

    def score_ground_loop(self, bucket: MonthlyBucket, baselines: dict,
                          year_ago_bucket: Optional[MonthlyBucket]) -> CategoryScore:
        """Ground Loop (20%)."""
        subs = []

        # Source inlet YoY
        if year_ago_bucket and year_ago_bucket.source_inlet.count > 0:
            if bucket.source_inlet.count > 0:
                drop = year_ago_bucket.source_inlet.mean - bucket.source_inlet.mean
                if drop <= 1.0:
                    s = 100
                elif drop <= 2.0:
                    s = 70
                elif drop <= 3.0:
                    s = 40
                else:
                    s = 0
                subs.append(SubScore('Source inlet YoY', s, f'{drop:+.1f}°C', drop))

        # Source ΔT
        if bucket.source_delta_t.count > 0:
            dt = bucket.source_delta_t.mean
            if dt < 4.5:
                s = 100
            elif dt < 5.5:
                s = 70
            elif dt < 6.5:
                s = 40
            else:
                s = 0
            subs.append(SubScore('Source ΔT', s, f'{dt:.1f}K', dt))

        # Pump speed trend
        for name, acc_name, ref_key in [
            ('HUP speed', 'hup_speed', 'hup_speed_mean_ref'),
            ('VBO speed', 'vbo_speed', 'vbo_speed_mean_ref'),
        ]:
            acc = getattr(bucket, acc_name)
            ref = baselines.get(ref_key)
            if acc.count > 0 and ref and ref > 0:
                increase_pct = (acc.mean - ref) / ref * 100
                if increase_pct <= 5:
                    s = 100
                elif increase_pct <= 15:
                    s = 70
                elif increase_pct <= 25:
                    s = 40
                else:
                    s = 0
                subs.append(SubScore(f'{name} trend', s,
                                     f'{increase_pct:+.0f}%', increase_pct))

        if not subs:
            return CategoryScore('Ground Loop', 0.20, 100)
        return CategoryScore('Ground Loop', 0.20, min(s.score for s in subs), subs)

    def score_compressor(self, bucket: MonthlyBucket, baselines: dict,
                         profile: dict) -> CategoryScore:
        """Compressor (15%)."""
        subs = []

        # Avg cycle length (from counters)
        counters = bucket.counters
        hours = counters.get('compressor_hours', 0)
        starts = counters.get('compressor_starts', 0)
        if starts > 0 and hours > 0:
            avg_cycle_h = hours / starts
            if avg_cycle_h > 1.5:
                s = 100
            elif avg_cycle_h > 1.0:
                s = 70
            elif avg_cycle_h > 0.5:
                s = 40
            else:
                s = 0
            subs.append(SubScore('Avg cycle length', s,
                                 f'{avg_cycle_h:.1f}h', avg_cycle_h))

            # Starts per hour
            sph = starts / hours
            if sph < 0.7:
                s = 100
            elif sph < 1.0:
                s = 70
            elif sph < 1.5:
                s = 40
            else:
                s = 0
            subs.append(SubScore('Starts per hour', s, f'{sph:.2f}', sph))

        # Discharge temp vs baseline
        ref = baselines.get('discharge_temp_mean_ref')
        if bucket.discharge_temp.count > 0 and ref is not None:
            rise = bucket.discharge_temp.mean - ref
            if rise <= 3:
                s = 100
            elif rise <= 6:
                s = 70
            elif rise <= 10:
                s = 40
            else:
                s = 0
            subs.append(SubScore('Discharge temp trend', s,
                                 f'{rise:+.1f}°C', rise))

        # Discharge temp vs ceiling
        ceiling = profile.get('discharge_max', 105)
        if bucket.discharge_temp.count > 0:
            pct_of_max = (bucket.discharge_temp.mean / ceiling) * 100
            if pct_of_max < 80:
                s = 100
            elif pct_of_max < 90:
                s = 70
            elif pct_of_max < 95:
                s = 40
            else:
                s = 0
            subs.append(SubScore('Discharge vs ceiling', s,
                                 f'{pct_of_max:.0f}% of {ceiling}°C', pct_of_max))

        if not subs:
            return CategoryScore('Compressor', 0.15, 100)
        return CategoryScore('Compressor', 0.15, min(s.score for s in subs), subs)

    def score_system(self, bucket: MonthlyBucket,
                     prev_bucket: Optional[MonthlyBucket]) -> CategoryScore:
        """System (10%)."""
        subs = []

        # New errors this month
        curr_errors = bucket.counters.get('error_count', 0)
        prev_errors = prev_bucket.counters.get('error_count', 0) if prev_bucket else curr_errors
        new_errors = max(0, curr_errors - prev_errors)
        if new_errors == 0:
            s = 100
        elif new_errors <= 2:
            s = 70
        elif new_errors <= 5:
            s = 40
        else:
            s = 0
        subs.append(SubScore('New errors', s, str(new_errors), float(new_errors)))

        # DHW share
        hours = bucket.counters.get('compressor_hours', 0)
        dhw_hours = bucket.counters.get('dhw_hours', 0)
        if hours > 0:
            dhw_pct = (dhw_hours / hours) * 100
            if dhw_pct < 45:
                s = 100
            elif dhw_pct < 55:
                s = 70
            elif dhw_pct < 65:
                s = 40
            else:
                s = 0
            subs.append(SubScore('DHW share', s, f'{dhw_pct:.0f}%', dhw_pct))

        if not subs:
            return CategoryScore('System', 0.10, 100)
        return CategoryScore('System', 0.10, min(s.score for s in subs), subs)

    def calculate(self, monitor: 'HealthMonitor',
                  month_key: Optional[str] = None) -> Tuple[int, str, List[CategoryScore]]:
        """Calculate overall health score for a month.

        Args:
            monitor: HealthMonitor with buckets, baselines, settings
            month_key: Month to score (default: current month)

        Returns:
            (overall_score, label, [category_scores])
        """
        buckets = monitor.accumulator.buckets
        if month_key is None:
            month_key = monitor.accumulator._current_month
        bucket = buckets.get(month_key)
        if not bucket:
            return (100, 'No data', [])

        # Find year-ago bucket
        try:
            year, month = month_key.split('-')
            yoy_key = f'{int(year)-1}-{month}'
        except ValueError:
            yoy_key = None
        year_ago = buckets.get(yoy_key) if yoy_key else None

        # Find previous month bucket
        sorted_keys = sorted(buckets.keys())
        idx = sorted_keys.index(month_key) if month_key in sorted_keys else -1
        prev_bucket = buckets.get(sorted_keys[idx - 1]) if idx > 0 else None

        # Score each category
        categories = [
            self.score_refrigerant(bucket, monitor.baselines, monitor._refrigerant_profile),
            self.score_efficiency(bucket, monitor.baselines, year_ago),
            self.score_ground_loop(bucket, monitor.baselines, year_ago),
            self.score_compressor(bucket, monitor.baselines, monitor._refrigerant_profile),
            self.score_system(bucket, prev_bucket),
        ]

        # Weighted average (redistribute weight of empty categories)
        active = [c for c in categories if c.sub_scores]
        if not active:
            return (100, 'Insufficient data', categories)

        total_weight = sum(c.weight for c in active)
        overall = sum(c.score * (c.weight / total_weight) for c in active)
        score = int(round(overall))

        # Label
        if score >= 90:
            label = 'Healthy'
        elif score >= 70:
            label = 'Good'
        elif score >= 50:
            label = 'Watch'
        elif score >= 30:
            label = 'Concern'
        else:
            label = 'Critical'

        # Add detail about worst category if not healthy
        if score < 90:
            worst = min(active, key=lambda c: c.score)
            worst_sub = min(worst.sub_scores, key=lambda s: s.score)
            label = f'{label}: {worst_sub.name}'

        return (score, label, categories)
```

**Step 2: Wire scorer into HealthMonitor**

Add to `HealthMonitor.__init__`:

```python
        self.scorer = HealthScorer()
```

Add method to HealthMonitor:

```python
    def generate_report(self) -> Tuple[int, str]:
        """Score current month and generate HTML report.

        Returns:
            (score, summary_text) for the Domoticz text device
        """
        month_key = self.accumulator._current_month
        score, label, categories = self.scorer.calculate(self, month_key)

        # Store score in bucket
        bucket = self.accumulator.buckets.get(month_key)
        if bucket:
            bucket.health_score = score
            bucket.health_label = label

        # Generate HTML
        self._write_html(score, label, categories)

        # Update state
        self.last_report = datetime.now().isoformat()
        self.save()

        # Format for text device: "94 - Healthy (Mar 2026)"
        month_display = datetime.now().strftime('%b %Y')
        summary = f'{score} - {label} ({month_display})'
        return (score, summary)
```

**Step 3: Commit**

```bash
git add health_monitor.py
git commit -m "feat: add HealthScorer with 5 weighted categories"
```

---

### Task 5: HTML Report Generator

**Files:**
- Modify: `health_monitor.py`

**Step 1: Add _write_html method to HealthMonitor**

This generates the full self-contained HTML file with all months. The HTML uses inline CSS and vanilla JS for accordion behavior.

```python
    def _write_html(self, current_score: int, current_label: str,
                    current_categories: List[CategoryScore]) -> None:
        """Generate self-contained HTML report file."""
        sorted_months = sorted(self.accumulator.buckets.keys(), reverse=True)
        if not sorted_months:
            return

        # Score all historical months
        month_scores = {}
        for mk in sorted_months:
            if mk == self.accumulator._current_month:
                month_scores[mk] = (current_score, current_label, current_categories)
            else:
                month_scores[mk] = self.scorer.calculate(self, mk)

        html = self._build_html(sorted_months, month_scores)

        # Atomic write
        dir_name = os.path.dirname(self._html_path)
        try:
            fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix='.tmp.html')
            with os.fdopen(fd, 'w') as f:
                f.write(html)
            os.replace(tmp_path, self._html_path)
        except OSError:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    def _build_html(self, sorted_months: List[str],
                    month_scores: dict) -> str:
        """Build the full HTML string."""
        # Implementation note: This method constructs the HTML using
        # Python string formatting. See design doc Section "Report Output"
        # for the page structure:
        # 1. Header with system info and current score badge
        # 2. Score timeline (12 months)
        # 3. Current month detail (expanded)
        # 4. Previous months (collapsed accordion)
        # 5. Footer
        #
        # The full HTML template is ~200 lines of inline CSS + structure.
        # Build it incrementally in implementation.

        score_colors = {
            'Healthy': '#2e7d32', 'Good': '#558b2f',
            'Watch': '#f9a825', 'Concern': '#ef6c00', 'Critical': '#c62828',
        }

        model = self.system_info.get('model_code', 'Unknown')
        ref = self.settings.get('refrigerant', 'r407c').upper()
        sys_type = self._system_type.replace('_', ' ').title()
        first_seen = self.system_info.get('first_seen', 'Unknown')

        current_month = sorted_months[0] if sorted_months else ''
        current_score, current_label, _ = month_scores.get(current_month, (0, 'No data', []))
        label_base = current_label.split(':')[0].strip()
        badge_color = score_colors.get(label_base, '#757575')

        # Build timeline data
        timeline_html = self._build_timeline(sorted_months, month_scores, score_colors)

        # Build month detail sections
        months_html = ''
        for i, mk in enumerate(sorted_months):
            score, label, categories = month_scores[mk]
            expanded = (i == 0)
            months_html += self._build_month_section(mk, score, label,
                                                      categories, expanded, score_colors)

        return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Heat Pump Health Report</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
         max-width: 900px; margin: 0 auto; padding: 20px; background: #fafafa; color: #333; }}
  .header {{ text-align: center; padding: 20px 0; border-bottom: 2px solid #e0e0e0; margin-bottom: 20px; }}
  .score-badge {{ display: inline-block; padding: 12px 24px; border-radius: 12px;
                  color: white; font-size: 1.4em; font-weight: bold; }}
  .system-info {{ color: #666; font-size: 0.9em; margin-top: 8px; }}
  .timeline {{ display: flex; justify-content: center; gap: 4px; margin: 20px 0; flex-wrap: wrap; }}
  .timeline-bar {{ width: 50px; text-align: center; font-size: 0.7em; }}
  .timeline-bar .bar {{ height: 40px; border-radius: 3px; margin-bottom: 2px;
                        display: flex; align-items: flex-end; justify-content: center; }}
  .timeline-bar .bar span {{ color: white; font-weight: bold; font-size: 0.85em; padding: 2px; }}
  .month-section {{ background: white; border-radius: 8px; margin: 12px 0;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.1); overflow: hidden; }}
  .month-header {{ padding: 14px 18px; cursor: pointer; display: flex;
                   justify-content: space-between; align-items: center;
                   border-bottom: 1px solid #eee; }}
  .month-header:hover {{ background: #f5f5f5; }}
  .month-header .arrow {{ transition: transform 0.2s; }}
  .month-header .arrow.open {{ transform: rotate(90deg); }}
  .month-body {{ padding: 18px; display: none; }}
  .month-body.open {{ display: block; }}
  .categories {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 12px; }}
  .category-card {{ border: 1px solid #e0e0e0; border-radius: 6px; padding: 12px; }}
  .category-card h4 {{ margin-bottom: 6px; display: flex; justify-content: space-between; }}
  .category-card .score-pill {{ padding: 2px 8px; border-radius: 10px; color: white; font-size: 0.85em; }}
  .sub-score {{ font-size: 0.85em; padding: 3px 0; display: flex; justify-content: space-between; }}
  .sub-score .value {{ color: #666; }}
  .counters {{ margin-top: 16px; }}
  .counters table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
  .counters td {{ padding: 4px 8px; border-bottom: 1px solid #eee; }}
  .counters td:last-child {{ text-align: right; }}
  .footer {{ text-align: center; color: #999; font-size: 0.8em; margin-top: 30px; padding-top: 20px;
             border-top: 1px solid #e0e0e0; }}
</style>
</head>
<body>
<div class="header">
  <h1>Heat Pump Health Report</h1>
  <div class="score-badge" style="background:{badge_color}">{current_score} — {current_label}</div>
  <div class="system-info">{model} | {ref} | {sys_type} | Since {first_seen}</div>
</div>

{timeline_html}
{months_html}

<div class="footer">
  Generated {datetime.now().strftime('%Y-%m-%d %H:%M')} |
  Baseline from {self.baseline_month or 'pending'} |
  {len(sorted_months)} months of data
</div>

<script>
document.querySelectorAll('.month-header').forEach(h => {{
  h.addEventListener('click', () => {{
    const body = h.nextElementSibling;
    const arrow = h.querySelector('.arrow');
    body.classList.toggle('open');
    arrow.classList.toggle('open');
  }});
}});
</script>
</body>
</html>'''

    def _build_timeline(self, sorted_months, month_scores, colors):
        """Build the score timeline bar chart."""
        bars = ''
        for mk in reversed(sorted_months[-12:]):
            score, label, _ = month_scores[mk]
            label_base = label.split(':')[0].strip()
            color = colors.get(label_base, '#757575')
            height = max(5, int(score * 0.4))
            short_month = mk[5:]  # "MM"
            bars += (f'<div class="timeline-bar"><div class="bar" '
                     f'style="height:{height}px;background:{color}">'
                     f'<span>{score}</span></div>{short_month}</div>')
        return f'<div class="timeline">{bars}</div>'

    def _build_month_section(self, month_key, score, label, categories,
                              expanded, colors):
        """Build one month's collapsible section."""
        label_base = label.split(':')[0].strip()
        color = colors.get(label_base, '#757575')
        open_class = ' open' if expanded else ''

        # Category cards
        cards = ''
        for cat in categories:
            cat_color = colors.get('Healthy', '#2e7d32')
            if cat.score < 30:
                cat_color = colors['Critical']
            elif cat.score < 50:
                cat_color = colors['Concern']
            elif cat.score < 70:
                cat_color = colors['Watch']

            sub_html = ''
            for sub in cat.sub_scores:
                sub_html += (f'<div class="sub-score"><span>{sub.name}</span>'
                             f'<span class="value">{sub.reason} ({sub.score})</span></div>')
            if not cat.sub_scores:
                sub_html = '<div class="sub-score"><span>No data yet</span></div>'

            cards += (f'<div class="category-card"><h4>{cat.name} '
                      f'<span class="score-pill" style="background:{cat_color}">'
                      f'{cat.score}</span></h4>{sub_html}</div>')

        # Counter summary
        bucket = self.accumulator.buckets.get(month_key)
        counters_html = ''
        if bucket and bucket.counters:
            rows = ''
            for name, val in bucket.counters.items():
                display_name = name.replace('_', ' ').title()
                rows += f'<tr><td>{display_name}</td><td>{val:,}</td></tr>'
            counters_html = (f'<div class="counters"><h4>Counters</h4>'
                             f'<table>{rows}</table></div>')

        return f'''<div class="month-section">
  <div class="month-header">
    <span><b>{month_key}</b> — {label}</span>
    <span><span class="score-pill" style="background:{color}">{score}</span>
    <span class="arrow{open_class}">▶</span></span>
  </div>
  <div class="month-body{open_class}">
    <div class="categories">{cards}</div>
    {counters_html}
  </div>
</div>'''
```

**Step 2: Commit**

```bash
git add health_monitor.py
git commit -m "feat: add HTML report generator with timeline and accordion"
```

---

### Task 6: Plugin Settings Migration

> **Phase 2 begins here.** Extended Domoticz settings PR should be merged before this task.

**Files:**
- Modify: `plugin.py` (XML params block, settings loading)

**Step 1: Update XML params**

Replace the Mode4/Mode5 params with extended settings groups. Keep Mode1-3, Mode6 as-is. Add the two groups from the design doc (Pump Power Compensation, Health Monitor).

Refer to design doc section "XML Definition" for exact XML.

**Step 2: Add _has_extended_settings and _load_settings methods**

Add to `LuxtronikPlugin` class (near `_configure_max_cop`):

```python
    @staticmethod
    def _has_extended_settings() -> bool:
        """Check if Domoticz supports extended plugin settings."""
        try:
            return isinstance(Settings, dict) and len(Settings) > 0
        except NameError:
            return False

    def _load_settings(self) -> dict:
        """Return normalized settings from extended or legacy source."""
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
                'system_type_override': 'auto',
                'refrigerant': 'r407c',
                'report_schedule': 'monthly',
            }
```

**Step 3: Refactor _configure_pump_compensation to use normalized settings**

```python
    def _configure_pump_compensation(self, settings: dict) -> None:
        """Configure pump power compensation from normalized settings."""
        self._pump_compensation_enabled = settings.get('pump_enabled', False)
        self._pump_power_ranges = None

        if not self._pump_compensation_enabled:
            return

        try:
            ranges = {
                'hup_min': settings['hup_min'],
                'hup_max': settings['hup_max'],
                'vbo_min': settings['vbo_min'],
                'vbo_max': settings['vbo_max'],
            }
            if any(v < 0 for v in ranges.values()):
                raise ValueError("Negative power values not allowed")
            if ranges['hup_min'] > ranges['hup_max'] or ranges['vbo_min'] > ranges['vbo_max']:
                raise ValueError("Min must not exceed max")
            self._pump_power_ranges = ranges
            _logger.log(
                f"Pump power compensation enabled: HUP {ranges['hup_min']}-{ranges['hup_max']}W, "
                f"VBO {ranges['vbo_min']}-{ranges['vbo_max']}W", DebugLevel.BASIC)
        except (ValueError, KeyError) as e:
            _logger.error(f"Invalid pump power settings: {e}. Disabling compensation.")
            self._pump_compensation_enabled = False
```

**Step 4: Update onStart to use _load_settings**

Replace the separate Mode4/Mode5 calls with:

```python
            settings = self._load_settings()
            self._configure_pump_compensation(settings)
```

**Step 5: Commit**

```bash
git add plugin.py
git commit -m "feat: add extended settings with legacy fallback for pump and health config"
```

---

### Task 7: Plugin Integration — Devices and Wiring

**Files:**
- Modify: `plugin.py` (imports, __init__, devices, _update_all_devices, onStop)
- Modify: `translations.py` (new device translations)

**Step 1: Add import**

At top of plugin.py, after existing imports:

```python
from health_monitor import HealthMonitor
```

**Step 2: Add health monitor instance to __init__**

In `LuxtronikPlugin.__init__`:

```python
        self.health_monitor = HealthMonitor()
```

**Step 3: Add devices in _build_device_specs**

In Group 14 Diagnostics section (after Unit 202):

```python
            # Unit 210: Health score text device
            DeviceFactory.create_custom_device(
                210, 'health_score', 'READ_CALCUL',
                0, '', used=0, image=13),

            # Unit 211: Generate report button [WRITABLE]
            # Handled via onDeviceModified, not a regular converter
```

Note: Unit 211 needs to be an On/Off switch device. Check how existing writable devices (Unit 13 cooling switch) are created and follow that pattern.

**Step 4: Add translations**

In `translations.py`, add to `DEVICE_TRANSLATIONS`:

```python
    'health_score': {
        Language.ENGLISH: ('Health Score', 'Overall system health score'),
        Language.DUTCH: ('Gezondheid Score', 'Algehele systeemgezondheidsscore'),
        Language.GERMAN: ('Gesundheitswert', 'Gesamter Systemgesundheitswert'),
        Language.POLISH: ('Ocena zdrowia', 'Ogólna ocena stanu systemu'),
        Language.FRENCH: ('Score de santé', 'Score de santé global du système'),
    },
    'generate_report': {
        Language.ENGLISH: ('Generate Report', 'Generate health report'),
        Language.DUTCH: ('Genereer Rapport', 'Genereer gezondheidsrapport'),
        Language.GERMAN: ('Bericht generieren', 'Gesundheitsbericht generieren'),
        Language.POLISH: ('Generuj raport', 'Generuj raport zdrowia'),
        Language.FRENCH: ('Générer un rapport', 'Générer un rapport de santé'),
    },
```

**Step 5: Initialize health monitor in onStart**

After the `_configure_pump_compensation` call:

```python
            # Initialize health monitor
            import os
            plugin_dir = os.path.dirname(os.path.abspath(__file__))
            hw_id = Parameters.get('HardwareID', '0')
            self.health_monitor.load(plugin_dir, hw_id, settings)
            _logger.log(f"Health monitor initialized (system: {self.health_monitor._system_type})",
                        DebugLevel.BASIC)
```

**Step 6: Add feed() call in _update_all_devices**

After the pump compensation line and before Phase 2 device updates:

```python
        # Feed health monitor (only if data was successfully read)
        if 'READ_CALCUL' in data_store:
            self.health_monitor.feed(data_store)
```

**Step 7: Add save() in onStop**

In the existing `onStop` method:

```python
        self.health_monitor.save()
```

**Step 8: Handle Unit 211 button press**

In the writable device handling (onDeviceModified for Unit 211), trigger report generation and update Unit 210:

```python
        # In the appropriate onDeviceModified handler for Unit 211:
        if unit_id == 211:
            score, summary = self.health_monitor.generate_report()
            # Update health score device (Unit 210)
            # Find the device and update its sValue
            _logger.log(f"Health report generated: {summary}", DebugLevel.BASIC)
```

**Step 9: Commit**

```bash
git add plugin.py translations.py
git commit -m "feat: integrate health monitor into plugin lifecycle"
```

---

### Task 8: Test Environment Verification

**Step 1: Restart Domoticz test instance**

```bash
cd /home/martijn/domoticz-test && npm run docker:down && npm run docker:up
```

**Step 2: Verify plugin starts without errors**

- Check Domoticz log for Python errors
- Verify "Health monitor initialized" log message
- Verify new devices (Units 210, 211) are created

**Step 3: Verify data accumulation**

- Let the plugin run for a few heartbeats
- Check that `health_state_hw{id}.json` is created in plugin directory after 1 hour (or temporarily reduce SAVE_INTERVAL_S for testing)

**Step 4: Test report generation**

- Press the Generate Report button (Unit 211)
- Verify `health_hw{id}.html` is created
- Open the HTML file and verify it renders correctly
- Check health score device (Unit 210) shows a score

**Step 5: Test with invalid/missing data**

- Stop the heat pump connection (invalid IP)
- Verify plugin handles gracefully, no accumulator errors
- Reconnect and verify accumulation resumes

**Step 6: Commit final version**

```bash
git add plugin.py health_monitor.py translations.py
git commit -m "chore: verified health monitor in test environment"
```

---

## Notes

- **No test suite exists** for this project — it requires the DomoticzEx runtime. However, `health_monitor.py` is pure Python and CAN be unit tested standalone. Consider adding a `test_health_monitor.py` for the Welford accumulator, scoring engine, and serialization.
- **Phase 1 (Tasks 1-5)** can be implemented and tested without Domoticz. Feed it synthetic data dicts and verify scoring output.
- **Phase 2 (Tasks 6-8)** requires the extended Domoticz settings PR to be merged for full settings UI. The plugin will work without it (legacy fallback with defaults), but the pump power and health monitor configuration won't be visible to users on legacy Domoticz.
- **Air source profile** is designed but scoring uses ground source only in v1. The `detect_system_type()` function and system type override are implemented, but air-specific metrics (defrost, fan speed) are left for a future iteration.
