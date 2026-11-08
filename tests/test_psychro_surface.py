"""Numeric checks against widely published values (Magnus / dew point tables, DIN 4108-2 style 12.6 C)."""

import numpy as np
import pytest

from mould_risk.psychro import abs_humidity, dew_point, rh_from_abs, rh_from_vapour, sat_pressure, vapour_pressure
from mould_risk.surface import (
    frsi_from_measurement,
    frsi_plain_wall,
    frsi_required,
    min_surface_temperature,
    setpoint_raise_needed,
    surface_rh,
    surface_temperature,
)


def test_sat_pressure_20c_matches_tables():
    assert sat_pressure(20.0) == pytest.approx(23.39, rel=0.005)


def test_sat_pressure_0c():
    assert sat_pressure(0.0) == pytest.approx(6.112, rel=0.002)


def test_sat_pressure_minus10_over_water():
    assert sat_pressure(-10.0) == pytest.approx(2.86, rel=0.01)


def test_dew_point_20_50_is_9_3():
    assert dew_point(20.0, 50.0) == pytest.approx(9.3, abs=0.1)


def test_dew_point_20_60_is_12():
    assert dew_point(20.0, 60.0) == pytest.approx(12.0, abs=0.15)


def test_dew_point_25_60_is_16_7():
    assert dew_point(25.0, 60.0) == pytest.approx(16.7, abs=0.15)


def test_dew_point_at_saturation_equals_temperature():
    for t in (-5.0, 5.0, 18.0, 30.0):
        assert dew_point(t, 100.0) == pytest.approx(t, abs=1e-6)


def test_dew_point_rejects_zero_rh():
    with pytest.raises(ValueError):
        dew_point(20.0, 0.0)


def test_abs_humidity_saturated_20c():
    assert abs_humidity(20.0, 100.0) == pytest.approx(17.3, abs=0.15)


def test_abs_humidity_half():
    assert abs_humidity(20.0, 50.0) == pytest.approx(8.65, abs=0.1)


def test_abs_humidity_roundtrip():
    ah = abs_humidity(21.0, 47.0)
    assert rh_from_abs(ah, 21.0) == pytest.approx(47.0, abs=1e-6)


def test_vectorised_inputs():
    rh = rh_from_vapour(vapour_pressure(np.array([10.0, 20.0]), np.array([50.0, 50.0])), np.array([10.0, 20.0]))
    assert rh == pytest.approx([50.0, 50.0])


def test_frsi_plain_wall_from_u_value():
    assert frsi_plain_wall(1.2) == pytest.approx(0.70)
    assert frsi_plain_wall(0.2) == pytest.approx(0.95)


def test_frsi_negative_u_rejected():
    with pytest.raises(ValueError):
        frsi_plain_wall(-0.1)


def test_surface_temperature_formula():
    assert surface_temperature(20.0, -5.0, 0.70) == pytest.approx(12.5)
    assert surface_temperature(20.0, -5.0, 1.0) == pytest.approx(20.0)
    assert surface_temperature(20.0, -5.0, 0.0) == pytest.approx(-5.0)


def test_din_4108_2_critical_surface_temperature():
    # 20 C / 50 % room air, 80 % surface RH limit -> the widely quoted 12.6 C
    assert min_surface_temperature(20.0, 50.0, 80.0) == pytest.approx(12.6, abs=0.1)


def test_required_frsi_is_about_0_70_at_minus_5():
    assert frsi_required(20.0, 50.0, -5.0, 80.0) == pytest.approx(0.70, abs=0.01)


def test_surface_rh_equals_room_rh_when_frsi_one():
    assert surface_rh(20.0, 55.0, -3.0, 1.0) == pytest.approx(55.0)


def test_surface_rh_at_frsi_070():
    assert 79.0 < surface_rh(20.0, 50.0, -5.0, 0.70) < 82.0


def test_frsi_from_measurement_roundtrip():
    ts = surface_temperature(21.0, 1.0, 0.66)
    assert frsi_from_measurement(ts, 21.0, 1.0) == pytest.approx(0.66)


def test_frsi_from_measurement_needs_delta():
    with pytest.raises(ValueError):
        frsi_from_measurement(18.0, 20.0, 17.0)


def test_setpoint_raise_zero_when_dry_enough():
    assert setpoint_raise_needed(21.0, 40.0, 0.0, 0.8) == 0.0


def test_setpoint_raise_positive_and_effective():
    dk = setpoint_raise_needed(19.0, 55.0, 0.0, 0.70, target_rh=75.0)
    assert dk is not None and dk > 0
    e = float(vapour_pressure(19.0, 55.0))
    assert surface_rh(19.0 + dk, float(rh_from_vapour(e, 19.0 + dk)), 0.0, 0.70) <= 75.0


def test_setpoint_raise_none_when_hopeless():
    assert setpoint_raise_needed(18.0, 85.0, -5.0, 0.55) is None
