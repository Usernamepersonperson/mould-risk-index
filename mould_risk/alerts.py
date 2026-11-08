"""Sensor view of a simulated flat, alert episodes, and false-alarm accounting.

Alert levels (all on the estimated wall-surface RH at the monitored spot):
    watch     >= 75 % for 3 consecutive hours
    warn      >= 80 % for 3 consecutive hours
    critical  VTT mould index >= 1
Episodes closer than `merge_gap` hours are merged into one.

False alarm (episode level): a warn episode with no hour of true surface RH >= 80 % within 3 h before
or after it. Missed event: a true >= 80 % run of 3 h or more with no warn episode touching it.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .mould import DEFAULT_SENSITIVITY, mould_index, run_lengths
from .psychro import abs_humidity, sat_pressure, vapour_pressure
from .sensors import SensorModel, apply_gaps, coverage, fill_short_gaps

SETUPS = ("room_generic", "room_known", "corner")
GENERIC_FRSI = 0.70
CORNER_OFFSET_K = 0.3  # corner sensor reads air 0.3 K warmer than the wall surface


def merge_runs(runs: list[tuple[int, int]], merge_gap: int) -> list[tuple[int, int]]:
    out: list[tuple[int, int]] = []
    for s, e in runs:
        if out and s - out[-1][1] - 1 <= merge_gap:
            out[-1] = (out[-1][0], e)
        else:
            out.append((s, e))
    return out


def episodes(flag, min_hours: int, merge_gap: int = 6) -> list[tuple[int, int]]:
    return merge_runs(run_lengths(np.nan_to_num(np.asarray(flag, dtype=float)) > 0, min_hours), merge_gap)


def sensor_view(df: pd.DataFrame, nominal_frsi: float, setup: str, seed: int = 0, model: SensorModel | None = None,
                gaps: bool = True, sensitivity: str = DEFAULT_SENSITIVITY) -> pd.DataFrame:
    """What the monitor would estimate from cheap sensor readings of a simulated flat."""
    if setup not in SETUPS:
        raise ValueError(f"unknown setup {setup!r}")
    model = model or SensorModel()
    rng = np.random.default_rng(seed)
    n = len(df)
    t_m, rh_m = model.observe(df["t_in"].to_numpy(), df["rh_in"].to_numpy(), rng)
    mask = model.gap_mask(n, rng) if gaps else np.zeros(n, dtype=bool)
    t_s = fill_short_gaps(apply_gaps(pd.Series(t_m, df.index), mask))
    rh_s = fill_short_gaps(apply_gaps(pd.Series(rh_m, df.index), mask))
    te = df["t_out"]
    out = pd.DataFrame({"t_in_est": t_s, "rh_in_est": rh_s})
    if setup == "corner":
        tc_true = df["t_surf"].to_numpy() + CORNER_OFFSET_K
        e_true = vapour_pressure(df["t_in"].to_numpy(), df["rh_in"].to_numpy())
        rh_c_true = 100.0 * e_true / sat_pressure(tc_true)
        tc_m, rhc_m = model.observe(tc_true, rh_c_true, rng)
        tc = fill_short_gaps(apply_gaps(pd.Series(tc_m, df.index), mask))
        rhc = fill_short_gaps(apply_gaps(pd.Series(rhc_m, df.index), mask))
        out["t_surf_est"] = tc - CORNER_OFFSET_K
        out["rh_surf_est"] = rhc * sat_pressure(tc.to_numpy()) / sat_pressure((tc - CORNER_OFFSET_K).to_numpy())
    else:
        frsi = GENERIC_FRSI if setup == "room_generic" else nominal_frsi
        out["t_surf_est"] = te + frsi * (out["t_in_est"] - te)
        e = vapour_pressure(out["t_in_est"].to_numpy(), out["rh_in_est"].to_numpy())
        out["rh_surf_est"] = 100.0 * e / sat_pressure(out["t_surf_est"].to_numpy())
    out["ah_in_est"] = abs_humidity(out["t_in_est"].to_numpy(), out["rh_in_est"].to_numpy())
    out["m_est"] = mould_index(out["t_surf_est"].to_numpy(), out["rh_surf_est"].to_numpy(), sensitivity)
    out["coverage_pct"] = coverage(out["rh_in_est"])
    return out


def count_alerts(rh_surf: pd.Series, m: np.ndarray | pd.Series) -> dict:
    rh = rh_surf.to_numpy()
    return {
        "watch": len(episodes(rh >= 75.0, 3)),
        "warn": len(episodes(rh >= 80.0, 3)),
        "critical": len(episodes(np.asarray(m) >= 1.0, 1, merge_gap=24)),
    }


def evaluate_sensing(df: pd.DataFrame, view: pd.DataFrame, tol: int = 3) -> dict:
    """Hour-level and episode-level accuracy of the estimated surface RH >= 80 % state against the simulation truth."""
    truth = (df["rh_surf"] >= 80.0).to_numpy()
    est = (view["rh_surf_est"] >= 80.0).fillna(False).to_numpy()
    valid = view["rh_surf_est"].notna().to_numpy()
    tp = int((truth & est & valid).sum())
    fp = int((~truth & est & valid).sum())
    fn = int((truth & ~est & valid).sum())
    est_eps = episodes(est, 3)
    truth_eps = episodes(truth, 3)
    false_alarm = 0
    for s, e in est_eps:
        lo, hi = max(s - tol, 0), min(e + tol + 1, truth.size)
        if not truth[lo:hi].any():
            false_alarm += 1
    missed = 0
    for s, e in truth_eps:
        lo, hi = max(s - tol, 0), min(e + tol + 1, est.size)
        if not est[lo:hi].any():
            missed += 1
    return {
        "hour_precision": tp / (tp + fp) if tp + fp else float("nan"),
        "hour_recall": tp / (tp + fn) if tp + fn else float("nan"),
        "est_episodes": len(est_eps),
        "true_episodes": len(truth_eps),
        "false_alarm_episodes": false_alarm,
        "missed_episodes": missed,
        "mean_abs_err_rh_surf": float((view["rh_surf_est"] - df["rh_surf"]).abs().mean()),
        "coverage_pct": float(view["coverage_pct"].iloc[0]),
    }
