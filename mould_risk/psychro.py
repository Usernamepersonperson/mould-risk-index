"""Moist-air basics: Magnus saturation pressure, dew point, absolute humidity.

Magnus constants: Alduchov and Eskridge (1996), "Improved Magnus form approximation of saturation
vapor pressure", J. Appl. Meteorol. 35, 601-609 (the 17.625 / 243.04 / 6.1094 set). Valid about -40..50 C.
All saturation pressures are over liquid water, which is what mould and condensation models use.
"""

from __future__ import annotations

import numpy as np

A_MAGNUS = 17.625
B_MAGNUS = 243.04  # deg C
E0_HPA = 6.1094  # hPa at 0 C
RV_FACTOR = 216.7  # g K / hPa / m3: absolute humidity = 216.7 * e / T (ideal gas, water vapour)


def sat_pressure(t_c):
    """Saturation vapour pressure over water in hPa."""
    t = np.asarray(t_c, dtype=float)
    return E0_HPA * np.exp(A_MAGNUS * t / (B_MAGNUS + t))


def vapour_pressure(t_c, rh_pct):
    """Partial vapour pressure in hPa from air temperature and relative humidity (%)."""
    return np.asarray(rh_pct, dtype=float) / 100.0 * sat_pressure(t_c)


def rh_from_vapour(e_hpa, t_c):
    """Relative humidity (%) of air with vapour pressure e at temperature t (can exceed 100)."""
    return 100.0 * np.asarray(e_hpa, dtype=float) / sat_pressure(t_c)


def dew_point_from_vapour(e_hpa):
    """Dew point in deg C from vapour pressure in hPa."""
    g = np.log(np.asarray(e_hpa, dtype=float) / E0_HPA)
    return B_MAGNUS * g / (A_MAGNUS - g)


def dew_point(t_c, rh_pct):
    """Dew point in deg C (Magnus inverse). RH must be > 0."""
    rh = np.asarray(rh_pct, dtype=float)
    if np.any(rh <= 0):
        raise ValueError("relative humidity must be > 0 for a dew point")
    return dew_point_from_vapour(vapour_pressure(t_c, rh))


def abs_humidity(t_c, rh_pct):
    """Absolute humidity in g/m3."""
    t = np.asarray(t_c, dtype=float)
    return RV_FACTOR * vapour_pressure(t, rh_pct) / (t + 273.15)


def rh_from_abs(ah_gm3, t_c):
    """Relative humidity (%) from absolute humidity (g/m3) at temperature t."""
    t = np.asarray(t_c, dtype=float)
    e = np.asarray(ah_gm3, dtype=float) * (t + 273.15) / RV_FACTOR
    return rh_from_vapour(e, t)
