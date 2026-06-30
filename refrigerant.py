"""Refrigerant saturation properties for derived refrigerant-side metrics.

Pure module (no DomoticzEx dependency) so it is unit-testable offline.

`t_sat(p_bar)` maps an ABSOLUTE pressure (bar) to the saturation temperature (C) by
linear interpolation over a per-refrigerant table, clamped at the table edges.

Data source
-----------
Tables digitised from the Fluidtool saturation-table exports
(https://fluidtool.com/docs/wiki/r407c-pressure-temperature-chart), saved locally as
`_temp/R407C-saturation.csv` and `_temp/R410A-saturation.csv` (2026-06-30). Each row is
the **saturated-liquid (bubble) line**: temperature Tsat and its bubble-point pressure P.

Glide note: R410A is near-azeotropic (glide ~0.1 K), so bubble == dew for our purposes.
R407C is zeotropic (~5-6 K glide), so this is the bubble line: correct as the saturation
reference for SUBCOOLING (T_sat(HD) - liquid line), while "condensing temperature" reported
from it sits ~glide below the dew point. A dew-line table can be added later for a
dew-based condensing temperature if needed.

Pressure basis (gauge vs absolute) of the controller's HD/ND readings is unverified; see
the plan's calibration step before trusting subcooling.
"""
from typing import Dict, List, Optional, Tuple

# (pressure_bar_abs, saturation_temp_C), ascending by pressure. Bubble line.
_R407C: List[Tuple[float, float]] = [
    (0.2351, -70.0), (0.3205, -65.0), (0.4298, -60.0), (0.5673, -55.0),
    (0.7383, -50.0), (0.948, -45.0), (1.2025, -40.0), (1.508, -35.0),
    (1.8713, -30.0), (2.2993, -25.0), (2.7994, -20.0), (3.3793, -15.0),
    (4.047, -10.0), (4.8107, -5.0), (5.6789, 0.0), (6.6604, 5.0),
    (7.7641, 10.0), (8.9993, 15.0), (10.3755, 20.0), (11.9024, 25.0),
    (13.5899, 30.0), (15.4484, 35.0), (17.4886, 40.0), (19.7216, 45.0),
    (22.1588, 50.0), (24.8122, 55.0), (27.6945, 60.0), (30.8184, 65.0),
    (34.1967, 70.0), (37.8396, 75.0), (41.7435, 80.0),
]

_R410A: List[Tuple[float, float]] = [
    (0.3562, -70.0), (0.4823, -65.0), (0.6424, -60.0), (0.8426, -55.0),
    (1.0898, -50.0), (1.3913, -45.0), (1.755, -40.0), (2.1893, -35.0),
    (2.7031, -30.0), (3.3057, -25.0), (4.0069, -20.0), (4.8168, -15.0),
    (5.746, -10.0), (6.8057, -5.0), (8.0071, 0.0), (9.3621, 5.0),
    (10.883, 10.0), (12.5827, 15.0), (14.4745, 20.0), (16.5725, 25.0),
    (18.8915, 30.0), (21.4471, 35.0), (24.2564, 40.0), (27.3376, 45.0),
    (30.7107, 50.0), (34.3984, 55.0), (38.4265, 60.0), (42.8262, 65.0),
]


class RefrigerantProperties:
    """Saturation curve for one refrigerant (pressure -> temperature)."""

    def __init__(self, name: str, pt_table: List[Tuple[float, float]]) -> None:
        self.name = name
        self._p = [p for p, _ in pt_table]
        self._t = [t for _, t in pt_table]

    def t_sat(self, p_bar: float) -> float:
        """Saturation temperature (C) at absolute pressure p_bar, clamped at table edges."""
        p = self._p
        t = self._t
        if p_bar <= p[0]:
            return t[0]
        if p_bar >= p[-1]:
            return t[-1]
        for i in range(1, len(p)):
            if p_bar <= p[i]:
                p0, p1 = p[i - 1], p[i]
                t0, t1 = t[i - 1], t[i]
                return t0 + (t1 - t0) * (p_bar - p0) / (p1 - p0)
        return t[-1]  # unreachable (guarded above)


DEFAULT = "R407C"

REFRIGERANTS: Dict[str, RefrigerantProperties] = {
    "R407C": RefrigerantProperties("R407C", _R407C),
    "R410A": RefrigerantProperties("R410A", _R410A),
}


def get(name: Optional[str]) -> RefrigerantProperties:
    """Return the RefrigerantProperties for `name` (case-insensitive), R407C as fallback."""
    return REFRIGERANTS.get((name or "").strip().upper(), REFRIGERANTS[DEFAULT])
