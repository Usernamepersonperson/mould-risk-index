"""Interior surface temperature at a thermal bridge and the resulting surface relative humidity.

Temperature factor (ISO 13788 concept, also used in DIN 4108-2 and SIA 180 style checks):

    fRsi = (theta_si - theta_e) / (theta_i - theta_e)

so the inside surface temperature is  theta_si = theta_e + fRsi * (theta_i - theta_e).
For a plain wall fRsi = 1 - U * Rsi with Rsi = 0.25 m2K/W (standard internal surface resistance). At a
corner or a slab edge the local fRsi is lower than the plain-wall value.

ISO 13788 itself is paywalled. Public explanations of the same formulas:
  - Wikipedia "Temperature factor" (https://en.wikipedia.org/wiki/Temperature_factor)
  - DIN 4108-2 (fRsi >= 0.70, i.e. 12.6 C surface temperature at 20 C / 50 % indoors and -5 C outdoors)
    and UK BRE guidance (fRsi >= 0.75 for housing) are quoted widely in open literature.
    Which threshold applies in a Swiss lease dispute is a legal and SIA question this project does not answer.

The vapour pressure at the surface is taken equal to the room air vapour pressure (steady state, no
local moisture source), so surface RH = e_air / e_sat(theta_si).
"""

from __future__ import annotations

import numpy as np

from .psychro import A_MAGNUS, B_MAGNUS, E0_HPA, rh_from_vapour, vapour_pressure

RSI = 0.25  # m2K/W, standard internal surface resistance (horizontal heat flow)


def frsi_plain_wall(u_value, rsi=RSI):
    """fRsi of an undisturbed wall from its U-value (W/m2K)."""
    if u_value < 0:
        raise ValueError("U-value must be >= 0")
    return 1.0 - u_value * rsi


def surface_temperature(theta_i, theta_e, frsi):
    """Inside surface temperature (deg C) for given fRsi."""
    ti = np.asarray(theta_i, dtype=float)
    te = np.asarray(theta_e, dtype=float)
    return te + frsi * (ti - te)


def frsi_from_measurement(theta_si, theta_i, theta_e):
    """Estimate fRsi from simultaneous surface, indoor and outdoor temperatures (needs |dT| >= 5 K)."""
    d = theta_i - theta_e
    if abs(d) < 5.0:
        raise ValueError("indoor-outdoor difference below 5 K: fRsi estimate is meaningless")
    return (theta_si - theta_e) / d


def surface_rh(theta_i, rh_i, theta_e, frsi):
    """Relative humidity (%) at the inside surface; > 100 means surface condensation."""
    e = vapour_pressure(theta_i, rh_i)
    return rh_from_vapour(e, surface_temperature(theta_i, theta_e, frsi))


def min_surface_temperature(theta_i, rh_i, rh_limit=80.0):
    """Lowest surface temperature (deg C) that keeps surface RH at or below rh_limit."""
    e = vapour_pressure(theta_i, rh_i) / (rh_limit / 100.0)
    g = np.log(e / E0_HPA)
    return B_MAGNUS * g / (A_MAGNUS - g)


def frsi_required(theta_i, rh_i, theta_e, rh_limit=80.0):
    """Minimum fRsi so that surface RH stays at or below rh_limit (critical temperature factor)."""
    th = min_surface_temperature(theta_i, rh_i, rh_limit)
    return (th - theta_e) / (np.asarray(theta_i, dtype=float) - theta_e)


def setpoint_raise_needed(theta_i, rh_i, theta_e, frsi, target_rh=75.0, max_raise=3.0, step=0.5):
    """Smallest setpoint raise (K, multiple of step) that brings surface RH under target_rh.

    Assumes the room vapour pressure stays unchanged. Returns 0.0 if already below target and None
    if max_raise is not enough.
    """
    if float(surface_rh(theta_i, rh_i, theta_e, frsi)) <= target_rh:
        return 0.0
    e = float(vapour_pressure(theta_i, rh_i))
    k = step
    while k <= max_raise + 1e-9:
        ti2 = theta_i + k
        rh2 = float(rh_from_vapour(e, ti2))
        if float(surface_rh(ti2, rh2, theta_e, frsi)) <= target_rh:
            return k
        k += step
    return None
