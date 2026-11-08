import math

import numpy as np
import pandas as pd
import pytest

from mould_risk.mould import (
    growth_rate_per_day,
    isopleth_exceeded,
    monthly_mean_rule,
    mould_index,
    rh_crit,
    rule_80,
    run_lengths,
    t_m1_weeks,
    t_m3_weeks,
)


def test_rh_crit_endpoints_of_published_polynomial():
    assert rh_crit(0.0, "very_sensitive") == pytest.approx(99.0, abs=1.0)  # capped below 100
    assert rh_crit(10.0, "very_sensitive") == pytest.approx(82.03, abs=0.05)
    assert rh_crit(20.0, "very_sensitive") == pytest.approx(80.04, abs=0.05)
    assert rh_crit(25.0, "very_sensitive") == 80.0


def test_rh_crit_decreases_with_temperature_up_to_16():
    vals = [rh_crit(t, "very_sensitive") for t in range(0, 17, 2)]
    assert all(a >= b for a, b in zip(vals, vals[1:], strict=False))


def test_resistant_class_needs_more_humidity():
    assert rh_crit(15.0, "resistant") > rh_crit(15.0, "very_sensitive")


def test_isopleth_exceeded_vectorised():
    out = isopleth_exceeded([20.0, 20.0, -2.0], [85.0, 70.0, 99.0])
    assert out.tolist() == [True, False, False]


def test_t_m1_evaluates_regression_formula():
    # exp(-0.68 ln 20 - 13.9 ln 97 + 66.02) = 1.49 weeks for pine at 20 C / 97 % RH
    assert t_m1_weeks(20.0, 97.0) == pytest.approx(1.49, abs=0.02)


def test_t_m3_slower_than_t_m1():
    assert t_m3_weeks(20.0, 97.0) > t_m1_weeks(20.0, 97.0)


def test_growth_is_zero_below_limit_and_freezing():
    assert growth_rate_per_day(0.0, 20.0, 70.0) == 0.0
    assert growth_rate_per_day(0.0, -1.0, 99.0) == 0.0


def test_time_to_index_one_matches_regression_time():
    n = 24 * 28
    m = mould_index(np.full(n, 20.0), np.full(n, 97.0), "very_sensitive")
    first = int(np.argmax(m >= 1.0))
    t1_hours = t_m1_weeks(20.0, 97.0) * 7 * 24
    assert first == pytest.approx(t1_hours, rel=0.10)


def test_no_growth_in_dry_conditions():
    m = mould_index(np.full(24 * 60, 20.0), np.full(24 * 60, 60.0))
    assert m.max() == 0.0


def test_no_growth_below_zero_even_when_saturated():
    m = mould_index(np.full(24 * 30, -3.0), np.full(24 * 30, 100.0))
    assert m.max() == 0.0


def test_growth_monotone_in_humidity():
    n = 24 * 40
    lo = mould_index(np.full(n, 18.0), np.full(n, 85.0))[-1]
    hi = mould_index(np.full(n, 18.0), np.full(n, 95.0))[-1]
    assert hi > lo > 0.0


def test_index_is_bounded_0_to_6():
    m = mould_index(np.full(24 * 365, 25.0), np.full(24 * 365, 100.0), "very_sensitive")
    assert 0.0 <= m.min() and m.max() <= 6.0


def test_decline_is_slow_and_never_negative():
    wet = np.full(24 * 30, 20.0), np.full(24 * 30, 96.0)
    dry_t, dry_rh = np.full(24 * 30, 20.0), np.full(24 * 30, 50.0)
    m = mould_index(np.r_[wet[0], dry_t], np.r_[wet[1], dry_rh])
    peak = m[24 * 30 - 1]
    assert peak > 0.5
    assert 0.0 <= m[-1] < peak
    assert m[24 * 30 + 24 * 3] > 0.8 * peak  # a few dry days barely help


def test_nan_gap_is_held_then_frozen():
    t = np.full(48, 20.0)
    rh = np.full(48, 96.0)
    rh[10:30] = np.nan
    m = mould_index(t, rh)
    assert not np.isnan(m).any()
    assert m[16] > m[9]  # first 6 h of the gap are held (growth continues)
    assert m[29] == pytest.approx(m[16])  # then frozen
    assert m[47] > m[29]


def test_shape_mismatch_rejected():
    with pytest.raises(ValueError):
        mould_index([20.0, 20.0], [90.0])


def test_rule_80_rolling_mean():
    idx = pd.date_range("2026-01-01", periods=24 * 20, freq="h", tz="Europe/Zurich")
    s = pd.Series(np.r_[np.full(24 * 10, 60.0), np.full(24 * 10, 85.0)], index=idx)
    r = rule_80(s, window_days=3)
    assert not r.iloc[24 * 5]
    assert r.iloc[-1]


def test_monthly_mean_rule():
    idx = pd.date_range("2026-01-01", "2026-02-28 23:00", freq="h", tz="Europe/Zurich")
    s = pd.Series(np.where(idx.month == 1, 85.0, 60.0), index=idx)
    r = monthly_mean_rule(s)
    assert r.tolist() == [True, False]


def test_run_lengths():
    f = [0, 1, 1, 1, 0, 1, 0, 1, 1]
    assert run_lengths(f, 2) == [(1, 3), (7, 8)]
    assert run_lengths(f, 4) == []
    assert run_lengths([], 1) == []


def test_rh_crit_is_finite_for_cold_values():
    assert math.isfinite(rh_crit(-20.0))
