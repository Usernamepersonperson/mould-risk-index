"""The measured experiments behind the README numbers. Everything is seeded and reproducible."""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import weather
from .alerts import SETUPS, count_alerts, evaluate_sensing, sensor_view
from .mould import DEFAULT_SENSITIVITY, monthly_mean_rule
from .report import render_weekly
from .sim import BEHAVIOURS, BUILDINGS, AdvicePolicy, airing_minutes_per_day, simulate, summarize

CITY_MAIN = "zurich"
SEEDS = (0, 1, 2)


def _run(city: str, bld: str, beh: str, **kw) -> pd.DataFrame:
    return simulate(weather.load_city(city), BUILDINGS[bld], BEHAVIOURS[beh], **kw)


def main_runs(city: str = CITY_MAIN) -> dict:
    """3 behaviours x 2 building types over the whole heating season."""
    w = weather.load_city(city)
    runs = {}
    for b in BUILDINGS.values():
        for h in BEHAVIOURS.values():
            runs[(b.key, h.key)] = simulate(w, b, h)
    return runs


def table_main(runs: dict) -> list[dict]:
    rows = []
    for (b, h), df in runs.items():
        s = summarize(df)
        s["building"], s["behaviour"] = b, h
        alerts = count_alerts(df["rh_surf"], df["mould_idx"])
        s.update({f"alerts_{k}": v for k, v in alerts.items()})
        months = monthly_mean_rule(df["rh_surf"])
        s["months_failing_80_rule"] = int(months.sum())
        s["months_total"] = int(len(months))
        rows.append(s)
    return rows


def table_cities(cities=None) -> list[dict]:
    rows = []
    for city in cities or weather.CITIES:
        w = weather.load_city(city)
        for b in BUILDINGS.values():
            for h in BEHAVIOURS.values():
                s = summarize(simulate(w, b, h))
                rows.append(
                    {
                        "city": city,
                        "building": b.key,
                        "behaviour": h.key,
                        "mean_t_out": float(w["temp_c"].mean()),
                        "days_m_ge_1": s["days_m_ge_1"],
                        "max_mould_idx": s["max_mould_idx"],
                        "hours_rh_surf_ge_80": s["hours_rh_surf_ge_80"],
                    }
                )
    return rows


def sweeps(city: str = CITY_MAIN) -> list[dict]:
    """How much does more airing or a higher setpoint cut the risk? Baseline = bad habits and typical."""
    w = weather.load_city(city)
    rows = []
    for b in BUILDINGS.values():
        for h_key in ("bad", "typical"):
            h = BEHAVIOURS[h_key]
            for air in (0, 10, 20, 30, 45):
                s = summarize(simulate(w, b, h, extra_air_min_per_day=air))
                rows.append({"building": b.key, "behaviour": h_key, "change": "airing", "value": air,
                             "airing_min_per_day": s["airing_min_per_day"], **_pick(s)})
            for dk in (1.0, 2.0):
                s = summarize(simulate(w, b, h, setpoint_offset=dk))
                rows.append({"building": b.key, "behaviour": h_key, "change": "setpoint", "value": dk,
                             "airing_min_per_day": s["airing_min_per_day"], **_pick(s)})
    return rows


def _pick(s: dict) -> dict:
    return {k: s[k] for k in ("days_m_ge_1", "max_mould_idx", "hours_rh_surf_ge_80", "heating_kwh", "mean_rh_in")}


def advice_loop(city: str = CITY_MAIN) -> list[dict]:
    """Closed loop: sensor -> advice engine -> tenant follows with probability `compliance`."""
    w = weather.load_city(city)
    rows = []
    for b in BUILDINGS.values():
        for h_key in ("bad", "typical"):
            h = BEHAVIOURS[h_key]
            base = summarize(simulate(w, b, h))
            rows.append({"building": b.key, "behaviour": h_key, "policy": "none", "compliance": 0.0, "n_advice": 0, **_pick(base),
                         "airing_min_per_day": base["airing_min_per_day"]})
            for mode in ("corner", "room"):
                for comp in (0.3, 0.7):
                    pol = AdvicePolicy(mode=mode, compliance=comp)
                    s = summarize(simulate(w, b, h, policy=pol))
                    rows.append({"building": b.key, "behaviour": h_key, "policy": mode, "compliance": comp,
                                 "n_advice": pol.n_advice, **_pick(s), "airing_min_per_day": s["airing_min_per_day"]})
    return rows


def sensing(runs: dict) -> list[dict]:
    rows = []
    for (b, h), df in runs.items():
        for setup in SETUPS:
            for seed in SEEDS:
                v = sensor_view(df, BUILDINGS[b].frsi_corner, setup, seed=seed)
                e = evaluate_sensing(df, v)
                rows.append({"building": b, "behaviour": h, "setup": setup, "seed": seed, **e})
    return rows


def sample_reports(runs: dict, out_dir: Path) -> list[str]:
    df = runs[("renovated", "typical")]
    b = BUILDINGS["renovated"]
    week = slice("2026-01-12", "2026-01-18")
    v = sensor_view(df, b.frsi_corner, "corner", seed=0)
    paths = []
    for lang in ("de", "fr", "it", "en"):
        txt = render_weekly(
            "Example flat B-12 (simulated)", v.loc[week], df["t_out"].loc[week], df["rh_out"].loc[week],
            b.frsi_corner, lang,
        )
        p = out_dir / f"example-report.{lang}.md"
        p.write_text(txt, encoding="utf-8")
        paths.append(str(p))
    return paths


def agg_sensing(rows: list[dict]) -> list[dict]:
    d = pd.DataFrame(rows)
    out = []
    months = 5.5
    for setup, g in d.groupby("setup"):
        out.append(
            {
                "setup": setup,
                "hour_precision": float(g["hour_precision"].mean()),
                "hour_recall": float(g["hour_recall"].mean()),
                "false_alarm_per_flat_month": float(g["false_alarm_episodes"].sum() / len(g) / months),
                "missed_per_flat_month": float(g["missed_episodes"].sum() / len(g) / months),
                "mean_abs_err_rh_surf": float(g["mean_abs_err_rh_surf"].mean()),
                "coverage_pct": float(g["coverage_pct"].mean()),
            }
        )
    return out


def run_all(out_dir: Path, quick: bool = False) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = main_runs()
    res: dict = {
        "meta": {
            "weather_source": weather.SOURCE,
            "period": f"{weather.START} to {weather.END}",
            "main_city": CITY_MAIN,
            "sensitivity_class": DEFAULT_SENSITIVITY,
            "simulated": True,
            "airing_min_per_day": {k: airing_minutes_per_day(v) for k, v in BEHAVIOURS.items()},
        },
        "main": table_main(runs),
    }
    res["sensing"] = sensing(runs)
    res["sensing_agg"] = agg_sensing(res["sensing"])
    res["cities"] = table_cities(["zurich", "davos"] if quick else None)
    res["sweeps"] = sweeps()
    res["advice_loop"] = advice_loop()
    res["reports"] = sample_reports(runs, out_dir)
    traj = pd.DataFrame(
        {f"{b}_{h}_mould_idx": df["mould_idx"].resample("D").max() for (b, h), df in runs.items()}
    )
    traj.index = traj.index.strftime("%Y-%m-%d")
    traj.round(4).to_csv(out_dir / "trajectories_zurich_daily.csv")
    (out_dir / "results.json").write_text(json.dumps(res, indent=1, default=float), encoding="utf-8")
    (out_dir / "results.md").write_text(to_markdown(res), encoding="utf-8")
    res["_runs"] = runs
    return res


def _fmt(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "|" + "|".join("---" for _ in cols) + "|"]
    for _, r in df.iterrows():
        cells = []
        for c in cols:
            v = r[c]
            cells.append(f"{v:.2f}" if isinstance(v, float | np.floating) else str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def to_markdown(res: dict) -> str:
    m = res["meta"]
    parts = [
        "# Measured results (simulated flats, real outdoor weather)\n",
        f"Weather: {m['weather_source']}, {m['period']}; main city {m['main_city']}. Mould class: {m['sensitivity_class']}.\n",
        "## 3 behaviours x 2 building types (Zurich)\n",
        _fmt(pd.DataFrame(res["main"])[["building", "behaviour", "days_m_ge_1", "days_m_ge_3", "max_mould_idx", "hours_rh_surf_ge_80",
                                          "days_rule80_7d", "mean_rh_in", "heating_kwh", "alerts_watch", "alerts_warn",
                                          "alerts_critical", "months_failing_80_rule"]]),
        "\n## Cities (days with mould index >= 1)\n",
        _fmt(pd.DataFrame(res["cities"]).pivot_table(index="city", columns=["building", "behaviour"], values="days_m_ge_1").reset_index()
             .pipe(lambda d: d.set_axis(["_".join(c).strip("_") if isinstance(c, tuple) else c for c in d.columns], axis=1))),
        "\n## Airing / setpoint sweeps (Zurich)\n",
        _fmt(pd.DataFrame(res["sweeps"])),
        "\n## Closed loop with the advice engine (Zurich)\n",
        _fmt(pd.DataFrame(res["advice_loop"])),
        "\n## Sensor placement and false alarms (mean over 6 flats x 3 noise seeds)\n",
        _fmt(pd.DataFrame(res["sensing_agg"])),
    ]
    return "\n".join(parts) + "\n"
