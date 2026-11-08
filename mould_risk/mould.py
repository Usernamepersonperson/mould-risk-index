"""Mould growth risk models.

1. Isopleth threshold (germination limit). The critical RH below which spores do not germinate on a
   *very sensitive* substrate is the lowest-isopleth fit used in the VTT model:
       RHcrit(T) = -0.00267 T^3 + 0.160 T^2 - 3.13 T + 100   (0 <= T <= 20 C), 80 % above 20 C.
   Source: Ojanen T., Viitanen H., Peuhkuri R., Lahdesmaki K., Vinha J., Salminen K. (2010),
   "Mold growth modeling of building structures using sensitivity classes of materials",
   Proc. ASHRAE Buildings XI. Sedlbauer's LIM isopleths (Fraunhofer IBP, 2001) have the same shape.

2. VTT mould index (dynamic). Hukka A., Viitanen H. (1999) "A mathematical model of mould growth on
   wooden material", Wood Science and Technology 33, 475-485; extended with sensitivity classes by
   Ojanen et al. (2010) and Viitanen and Ojanen (2007). M runs 0..6:
       0 none, 1 first microscopic growth, 2 moderate (microscope), 3 first visible, 4 clearly visible,
       5 coverage > 50 %, 6 full coverage.
   Growth rate (per day)   dM/dt = k1 * k2 / (7 exp(-0.68 ln T - 13.9 ln RH + 0.14 W - 0.33 SQ + 66.02))
   k1 = 1 for M < 1, else 2 / (t3 / t1 - 1) with t1 the weeks to M=1 above and
        t3 = exp(-0.74 ln T - 12.72 ln RH + 0.06 W + 61.50) weeks to M=3,
   k2 = max(1 - exp(2.3 (M - Mmax)), 0), Mmax = A + B x - C x^2, x = (RHcrit - RH)/(RHcrit - 100).
   Sensitivity classes (A, B, C): very sensitive (1, 7, 2), sensitive (0, 6, 1), medium resistant (0, 5, 1.5),
   resistant (0, 3, 1). The W / SQ terms describe timber (0 = pine, 0 = sawn); for painted plaster they
   are set to 0 and the class constants carry the material sensitivity.
   Decline when RH < RHcrit: -0.00133 /h for the first 6 h, 0 until 24 h, -0.000667 /h afterwards.
   Constants were implemented from the published formulas as I read them; check against the paper before
   relying on absolute values (see README, "What is not verified yet").
   RH_CLASS_OFFSET (germination threshold: 80 % at 20 C for the two sensitive classes, 85 % for the resistant ones, as I recall the paper)
   and the choice of the "sensitive" class for painted interior walls are assumptions of this project.

3. Simple rule: surface RH >= 80 % sustained (rolling mean over a window of days). The ISO 13788 /
   DIN 4108-2 criterion uses the monthly mean surface RH < 80 %.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

SENSITIVITY = {
    "very_sensitive": (1.0, 7.0, 2.0),
    "sensitive": (0.0, 6.0, 1.0),
    "medium_resistant": (0.0, 5.0, 1.5),
    "resistant": (0.0, 3.0, 1.0),
}
RH_CLASS_OFFSET = {"very_sensitive": 0.0, "sensitive": 0.0, "medium_resistant": 5.0, "resistant": 5.0}
# Painted plaster / wallpaper: "sensitive" class (project assumption); "very_sensitive" is run as a sensitivity check.
DEFAULT_SENSITIVITY = "sensitive"


def rh_crit(t_c: float, sensitivity: str = DEFAULT_SENSITIVITY) -> float:
    """Critical (germination) RH in % at temperature t (deg C)."""
    if t_c > 20.0:
        base = 80.0
    else:
        t = max(float(t_c), 0.0)
        base = -0.00267 * t**3 + 0.160 * t**2 - 3.13 * t + 100.0
    return min(base + RH_CLASS_OFFSET[sensitivity], 99.0)


def isopleth_exceeded(t_c, rh_pct, sensitivity: str = DEFAULT_SENSITIVITY):
    """Boolean array: RH above the germination limit at that temperature (and T > 0)."""
    t = np.asarray(t_c, dtype=float)
    rh = np.asarray(rh_pct, dtype=float)
    crit = np.array([rh_crit(x, sensitivity) for x in t.ravel()]).reshape(t.shape)
    return (rh >= crit) & (t > 0.0)


def t_m1_weeks(t_c: float, rh_pct: float, w: float = 0.0, sq: float = 0.0) -> float:
    """Weeks to mould index 1 at constant conditions (VTT regression)."""
    return math.exp(-0.68 * math.log(t_c) - 13.9 * math.log(rh_pct) + 0.14 * w - 0.33 * sq + 66.02)


def t_m3_weeks(t_c: float, rh_pct: float, w: float = 0.0) -> float:
    """Weeks to mould index 3 at constant conditions (VTT regression)."""
    return math.exp(-0.74 * math.log(t_c) - 12.72 * math.log(rh_pct) + 0.06 * w + 61.50)


def growth_rate_per_day(m: float, t_c: float, rh_pct: float, sensitivity: str = DEFAULT_SENSITIVITY) -> float:
    """dM/dt in 1/day for conditions at or above the germination limit."""
    a, b, c = SENSITIVITY[sensitivity]
    rc = rh_crit(t_c, sensitivity)
    rh = min(rh_pct, 100.0)
    if rh <= rc or t_c <= 0.0:
        return 0.0
    t1 = t_m1_weeks(min(t_c, 50.0), rh)
    t3 = t_m3_weeks(min(t_c, 50.0), rh)
    k1 = 1.0 if m < 1.0 else 2.0 / max(t3 / t1 - 1.0, 0.01)
    x = (rc - rh) / (rc - 100.0)
    m_max = a + b * x - c * x * x
    k2 = max(1.0 - math.exp(2.3 * (m - m_max)), 0.0)
    return k1 * k2 / (7.0 * t1)


def mould_index(
    t_c,
    rh_pct,
    sensitivity: str = DEFAULT_SENSITIVITY,
    dt_hours: float = 1.0,
    m0: float = 0.0,
    max_hold_hours: int = 6,
):
    """Integrate the VTT mould index along a surface temperature / RH series.

    NaN samples (sensor data gaps) are held for up to max_hold_hours, then skipped (index frozen).
    Returns a numpy array of M at every step.
    """
    t = np.asarray(t_c, dtype=float)
    rh = np.asarray(rh_pct, dtype=float)
    if t.shape != rh.shape:
        raise ValueError("temperature and RH series must have the same length")
    out = np.empty(t.size)
    m = float(m0)
    dry_h = 0.0
    last_t = last_rh = float("nan")
    hold = 0
    dt_d = dt_hours / 24.0
    for i in range(t.size):
        ti, ri = t[i], rh[i]
        if math.isnan(ti) or math.isnan(ri):
            hold += 1
            if hold > max_hold_hours or math.isnan(last_t):
                out[i] = m
                continue
            ti, ri = last_t, last_rh
        else:
            hold = 0
            last_t, last_rh = ti, ri
        ri = min(ri, 100.0)
        if ri > rh_crit(ti, sensitivity) and ti > 0.0:
            dry_h = 0.0
            m += growth_rate_per_day(m, ti, ri, sensitivity) * dt_d
        else:
            dry_h += dt_hours
            if dry_h <= 6.0:
                m -= 0.00133 * dt_hours
            elif dry_h > 24.0:
                m -= 0.000667 * dt_hours
        m = min(max(m, 0.0), 6.0)
        out[i] = m
    return out


def rule_80(surface_rh: pd.Series, window_days: int = 7, limit: float = 80.0) -> pd.Series:
    """Simple rule: rolling mean of hourly surface RH >= limit over window_days. Returns boolean series."""
    win = window_days * 24
    return surface_rh.rolling(win, min_periods=win // 2).mean() >= limit


def monthly_mean_rule(surface_rh: pd.Series, limit: float = 80.0) -> pd.Series:
    """ISO 13788 / DIN 4108-2 style: calendar-month mean surface RH; True where the month fails."""
    return surface_rh.groupby([surface_rh.index.year, surface_rh.index.month]).mean() >= limit


def run_lengths(flag, min_len: int):
    """Start and end (inclusive) indices of runs of True with length >= min_len."""
    f = np.asarray(flag, dtype=bool)
    runs = []
    start = None
    for i, v in enumerate(f):
        if v and start is None:
            start = i
        if (not v) and start is not None:
            if i - start >= min_len:
                runs.append((start, i - 1))
            start = None
    if start is not None and f.size - start >= min_len:
        runs.append((start, f.size - 1))
    return runs
