"""Simulated flat: lumped heat balance + single-zone moisture balance, driven by real outdoor weather.

Everything here is a documented simplification, not a validated building-physics model.

Moisture balance (one zone, well mixed, hourly, exact exponential step):
    kappa * V * d(rho_i)/dt = G + n * V * (rho_e - rho_i)
with indoor/outdoor absolute humidity rho (g/m3), moisture production G (g/h), volume V, air change rate n
and kappa a hygric buffering factor (surfaces and furnishings take up and release moisture; kappa = 2.5
means the effective air-moisture capacity is 2.5x the air volume; assumption).

Moisture production rates (typical values from building-physics literature, e.g. EN ISO 13788 Annex /
BS 5250 / Hens "Building Physics - Heat, Air and Moisture"; ranges are wide and I did not re-derive them):
    person asleep 35 g/h, awake at home 45 g/h; shower 300 g each; breakfast cooking 100-150 g,
    dinner cooking 600 g; laundry dried indoors 1.5 kg per load released over 12 h; plants, mopping etc 10 g/h.

Heat balance (RC node): C dTi/dt = UA_env (Te-Ti) + UA_nb (20-Ti) + 0.34 n V (Te-Ti) + P + gains with
neighbouring flats held at 20 C and a proportional radiator controller P = clip(Kp (Tset-Ti), 0, Pmax).
Infiltration rises with the indoor-outdoor difference: n_inf = n_ref * max(0.5, dT/20) (assumption).
Incidental ventilation adds 0.1 1/h while someone is awake at home. Airing is a burst of 12 air changes per hour for the stated minutes (cross ventilation), averaged over the hour.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field, replace

import numpy as np
import pandas as pd

from .advice import Reading, advise
from .mould import DEFAULT_SENSITIVITY, mould_index
from .psychro import A_MAGNUS, B_MAGNUS, E0_HPA, RV_FACTOR, abs_humidity
from .sensors import SensorModel
from .surface import frsi_from_measurement, surface_rh

BURST_ACH = 12.0
KAPPA = 2.5
INCIDENTAL_ACH = 0.10  # door and balcony-door openings, bathroom extract fan; only while someone is awake at home
P_MAX = 3000.0
KP = 1500.0  # W/K
GAINS_HOME = 150.0  # W appliances, lighting, people (sensible), when someone is home
T_NEIGHBOUR = 20.0
C_NODE = 6000.0 * 3600.0  # J/K, 6 kWh/K (medium-heavy flat of 60 m2)


def _psat(t: float) -> float:
    """Scalar Magnus saturation pressure (hPa); same constants as psychro.sat_pressure, faster in the hourly loop."""
    return E0_HPA * math.exp(A_MAGNUS * t / (B_MAGNUS + t))


@dataclass(frozen=True)
class Building:
    key: str
    label: str
    volume: float  # m3
    ua_env: float  # W/K to outside through walls and windows
    ua_nb: float  # W/K to neighbouring flats at 20 C
    n_ref: float  # infiltration at dT = 20 K, 1/h
    frsi_corner: float  # temperature factor at the monitored cold corner / thermal bridge


ALTBAU = Building("altbau", "1960s uninsulated brick", 150.0, 60.0, 35.0, 0.50, 0.62)
RENOVATED = Building("renovated", "energy-renovated, tight envelope", 150.0, 15.0, 35.0, 0.12, 0.74)
BUILDINGS = {b.key: b for b in (ALTBAU, RENOVATED)}


@dataclass(frozen=True)
class Behaviour:
    key: str
    label: str
    setpoint_day: float
    setpoint_night: float
    airing: tuple = ()  # (hour, minutes, weekend_only) planned airing events, only if someone is home and awake
    laundry_days: tuple = ()  # weekday numbers (Mon=0) with one 1.5 kg load dried indoors
    wardrobe_penalty: float = 0.0  # fRsi reduction at the monitored corner (furniture against the wall)
    adherence: float = 0.85  # probability a planned airing really happens


BAD = Behaviour("bad", "bad habits", 18.5, 16.0, (), (1, 3, 5), 0.05, 1.0)
TYPICAL = Behaviour("typical", "typical", 20.0, 18.0, ((7, 5, False), (20, 5, False)), (5,), 0.0, 0.85)
GOOD = Behaviour(
    "good",
    "good airing",
    20.5,
    19.0,
    ((7, 10, False), (12, 8, True), (19, 10, False), (22, 8, False)),
    (),
    0.0,
    0.85,
)
BEHAVIOURS = {b.key: b for b in (BAD, TYPICAL, GOOD)}


def airing_minutes_per_day(beh: Behaviour) -> float:
    """Planned airing minutes on an average day (weekend-only events count 2/7)."""
    return sum(m * (2 / 7 if wk else 1.0) for _, m, wk in beh.airing)


@dataclass
class AdvicePolicy:
    """Closed loop: a sensor reading goes through the advice engine and the tenant follows it with some probability."""

    mode: str = "corner"  # "corner": surface-side sensor gives fRsi; "room": room sensor with assumed fRsi
    compliance: float = 0.7
    frsi_assumed: float = 0.70
    seed: int = 7
    air_minutes: int = 8
    sensor: SensorModel = field(default_factory=SensorModel)

    def reset(self, n: int):
        self.rng = np.random.default_rng(self.seed)
        self.gap = self.sensor.gap_mask(n, self.rng)
        self.last_air = -99
        self.bump_until = -1
        self.bump = 0.0
        self.over80 = 0
        self.since_data = 0
        self.last_good = None
        self.n_advice = 0

    def step(self, i: int, ctx: dict) -> tuple[float, float]:
        """Return (extra airing minutes, setpoint bump K) for hour i from the previous hour's state."""
        if i >= self.bump_until:
            self.bump = 0.0
        if ctx is None:
            return 0.0, self.bump
        if self.gap[i]:
            self.since_data += 1
        else:
            self.since_data = 0
            t_m, rh_m = self.sensor.observe(np.array([ctx["t_in"]]), np.array([ctx["rh_in"]]), self.rng)
            t_c, _ = self.sensor.observe(np.array([ctx["t_surf"] + 0.3]), np.array([50.0]), self.rng)
            frsi = self.frsi_assumed
            if self.mode == "corner" and abs(t_m[0] - ctx["te"]) >= 5.0:
                frsi = float(np.clip(frsi_from_measurement(t_c[0], t_m[0], ctx["te"]), 0.2, 0.99))
            self.last_good = (float(t_m[0]), float(rh_m[0]), frsi)
        if self.last_good is None:
            return 0.0, self.bump
        t_in, rh_in, frsi = self.last_good
        srh = float(surface_rh(t_in, rh_in, ctx["te"], frsi))
        self.over80 = self.over80 + 1 if srh >= 80.0 else 0
        r = Reading(t_in, rh_in, ctx["te"], ctx["rhe"], frsi, 0.0, self.over80, self.since_data)
        items = advise(r)
        codes = {a.code for a in items}
        extra = 0.0
        if "air_now" in codes and ctx["awake_home"] and i - self.last_air >= 3:
            self.n_advice += 1
            if self.rng.random() < self.compliance:
                extra = float(self.air_minutes)
                self.last_air = i
        if "heat_up" in codes and self.bump == 0.0 and self.rng.random() < self.compliance:
            dk = next(a.params["dk"] for a in items if a.code == "heat_up")
            self.bump = min(float(dk), 2.0)
            self.bump_until = i + 24
        return extra, self.bump


def _production(i, h, dow, beh, laundry_g):
    weekday = dow < 5
    home = not (weekday and 8 <= h < 17)
    asleep = h >= 23 or h < 7
    awake_home = home and not asleep
    g = 10.0
    if asleep:
        g += 70.0
    elif awake_home:
        g += 90.0
    if h == 7 and weekday:
        g += 600.0 + 100.0
    elif h == 9 and not weekday:
        g += 600.0 + 150.0
    if h == 18:
        g += 600.0
    if h == 12 and not weekday:
        g += 400.0
    g += laundry_g[i]
    return g, home, awake_home


def _laundry_series(idx, beh):
    arr = np.zeros(len(idx))
    dows, hrs = idx.day_of_week.to_numpy(), idx.hour.to_numpy()
    for i in range(len(idx)):
        if int(dows[i]) in beh.laundry_days and int(hrs[i]) == (10 if dows[i] >= 5 else 18):
            arr[i : i + 12] += 125.0
    return arr


def simulate(
    weather: pd.DataFrame,
    bld: Building,
    beh: Behaviour,
    policy: AdvicePolicy | None = None,
    seed: int = 0,
    sensitivity: str = DEFAULT_SENSITIVITY,
    setpoint_offset: float = 0.0,
    extra_air_min_per_day: float = 0.0,
) -> pd.DataFrame:
    """Hourly simulation over the weather index. Returns one row per hour (end-of-hour state)."""
    rng = np.random.default_rng(seed)
    idx = weather.index
    n = len(idx)
    te_arr = weather["temp_c"].to_numpy()
    rhe_arr = weather["rh_pct"].to_numpy()
    ahe_arr = abs_humidity(te_arr, rhe_arr)
    laundry_g = _laundry_series(idx, beh)
    hours_arr = idx.hour.to_numpy()
    dow_arr = idx.day_of_week.to_numpy()
    frsi = bld.frsi_corner - beh.wardrobe_penalty
    ti = beh.setpoint_day - 0.5
    ah_i = float(ahe_arr[0]) + 2.0
    if policy:
        policy.reset(n)
    ctx = None
    rows = np.zeros((n, 9))
    for i in range(n):
        h, dow = int(hours_arr[i]), int(dow_arr[i])
        te, ahe = float(te_arr[i]), float(ahe_arr[i])
        g, home, awake_home = _production(i, h, dow, beh, laundry_g)
        minutes = 0.0
        if awake_home:
            for hh, mm, wk_only in beh.airing:
                if hh == h and (not wk_only or dow >= 5) and rng.random() < beh.adherence:
                    minutes += mm
            if extra_air_min_per_day and h in (7, 19):
                minutes += extra_air_min_per_day / 2.0
        bump = 0.0
        if policy:
            extra, bump = policy.step(i, ctx)
            minutes += extra
        minutes = min(minutes, 30.0)
        set_t = (beh.setpoint_night if (h >= 23 or h < 6) else beh.setpoint_day) + bump + setpoint_offset
        n_inf = bld.n_ref * max(0.5, (ti - te) / 20.0)
        n_eff = n_inf + (INCIDENTAL_ACH if awake_home else 0.0) + BURST_ACH * minutes / 60.0
        # thermal: 6 sub-steps of 10 min
        p_sum = 0.0
        for _ in range(6):
            p = min(max(KP * (set_t - ti), 0.0), P_MAX)
            q = (
                bld.ua_env * (te - ti)
                + bld.ua_nb * (T_NEIGHBOUR - ti)
                + 0.34 * n_eff * bld.volume * (te - ti)
                + p
                + (GAINS_HOME if home else 50.0)
            )
            ti += 600.0 * q / C_NODE
            p_sum += p
        # moisture
        ah_eq = ahe + g / (bld.volume * n_eff)
        ah_i = ah_eq + (ah_i - ah_eq) * math.exp(-n_eff / KAPPA)
        ah_sat = RV_FACTOR * _psat(ti) / (ti + 273.15)
        ah_i = min(ah_i, 0.98 * ah_sat)
        rh_in = 100.0 * ah_i / ah_sat
        t_surf = te + frsi * (ti - te)
        e_i = ah_i * (ti + 273.15) / RV_FACTOR
        rh_s = 100.0 * e_i / _psat(t_surf)
        rows[i] = (ti, rh_in, ah_i, t_surf, rh_s, n_eff, p_sum / 6.0, g, minutes)
        ctx = {"t_in": ti, "rh_in": rh_in, "t_surf": t_surf, "te": te, "rhe": float(rhe_arr[i]), "awake_home": awake_home}
        # next hour's "awake_home" is needed for the policy; recompute cheaply
        j = min(i + 1, n - 1)
        nh_h, nh_d = int(hours_arr[j]), int(dow_arr[j])
        ctx["awake_home"] = (not (nh_d < 5 and 8 <= nh_h < 17)) and not (nh_h >= 23 or nh_h < 7)
    df = pd.DataFrame(
        rows,
        index=idx,
        columns=["t_in", "rh_in", "ah_in", "t_surf", "rh_surf", "n_eff", "p_heat_w", "moisture_g_h", "airing_min"],
    )
    df["t_out"] = te_arr
    df["rh_out"] = rhe_arr
    df["ah_out"] = ahe_arr
    df["frsi"] = frsi
    df["mould_idx"] = mould_index(df["t_surf"].to_numpy(), df["rh_surf"].to_numpy(), sensitivity)
    return df


def summarize(df: pd.DataFrame) -> dict:
    """Headline numbers of one simulated winter."""
    day_max = df["mould_idx"].resample("D").max()
    rh_s = df["rh_surf"]
    return {
        "max_mould_idx": float(df["mould_idx"].max()),
        "final_mould_idx": float(df["mould_idx"].iloc[-1]),
        "days_m_ge_1": int((day_max >= 1.0).sum()),
        "days_m_ge_3": int((day_max >= 3.0).sum()),
        "hours_rh_surf_ge_80": int((rh_s >= 80.0).sum()),
        "days_rule80_7d": int(
            (rh_s.rolling(7 * 24, min_periods=84).mean().resample("D").max() >= 80.0).sum()
        ),
        "mean_rh_in": float(df["rh_in"].mean()),
        "mean_t_in": float(df["t_in"].mean()),
        "min_rh_in": float(df["rh_in"].min()),
        "max_rh_in": float(df["rh_in"].max()),
        "heating_kwh": float(df["p_heat_w"].sum() / 1000.0),
        "airing_min_per_day": float(df["airing_min"].sum() / (len(df) / 24.0)),
    }


def with_behaviour(beh: Behaviour, **kw) -> Behaviour:
    return replace(beh, **kw)
