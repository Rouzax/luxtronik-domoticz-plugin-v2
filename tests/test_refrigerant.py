"""Tests for the refrigerant saturation module.

Reference points come from the Fluidtool R407C/R410A saturated-liquid (bubble) tables
(see refrigerant.py source note). t_sat maps absolute pressure (bar) -> saturation
temperature (C) by linear interpolation, clamped at the table edges.
"""
import pytest

import refrigerant


# --- exact table points (pressure -> temperature) ---

def test_r407c_known_points():
    r = refrigerant.get("R407C")
    assert r.t_sat(5.6789) == pytest.approx(0.0, abs=0.05)
    assert r.t_sat(17.4886) == pytest.approx(40.0, abs=0.05)
    assert r.t_sat(24.8122) == pytest.approx(55.0, abs=0.05)


def test_r410a_known_points():
    r = refrigerant.get("R410A")
    assert r.t_sat(8.0071) == pytest.approx(0.0, abs=0.05)
    assert r.t_sat(24.2564) == pytest.approx(40.0, abs=0.05)


# --- linear interpolation between points ---

def test_r407c_interpolates_midpoint():
    # midway (in pressure) between (17.4886->40) and (19.7216->45) is exactly 42.5 C
    r = refrigerant.get("R407C")
    p_mid = (17.4886 + 19.7216) / 2
    assert r.t_sat(p_mid) == pytest.approx(42.5, abs=0.01)


def test_monotonic_increasing():
    r = refrigerant.get("R407C")
    temps = [r.t_sat(p) for p in (3.0, 6.0, 12.0, 18.0, 25.0, 30.0)]
    assert temps == sorted(temps)
    assert len(set(temps)) == len(temps)  # strictly increasing


# --- clamping at table edges ---

def test_clamps_below_and_above_range():
    r = refrigerant.get("R407C")
    assert r.t_sat(0.01) == pytest.approx(-70.0)   # below min pressure -> min temp
    assert r.t_sat(999.0) == pytest.approx(80.0)    # above max pressure -> max temp


# --- selection / fallback ---

def test_get_is_case_insensitive():
    assert refrigerant.get("r407c").name == "R407C"


def test_unknown_refrigerant_falls_back_to_r407c():
    r = refrigerant.get("R1234zz-unknown")
    assert r.name == "R407C"


def test_default_when_empty():
    assert refrigerant.get("").name == "R407C"
    assert refrigerant.get(None).name == "R407C"
