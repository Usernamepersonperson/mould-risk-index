"""Dark-style figures for the README and the LinkedIn post image."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib import font_manager  # noqa: E402

TZ = "Europe/Zurich"
BG, GRID, TEXT, MUTED = "#16213A", "#2A3750", "#F8FAFC", "#A9B6CB"
ACCENT, GREEN, AMBER, RED, GREY, VIOLET = "#38BDF8", "#34D399", "#FBBF24", "#F87171", "#64748B", "#A78BFA"
BEH_COL = {"bad": RED, "typical": AMBER, "good": GREEN}
BEH_LABEL = {"bad": "bad habits", "typical": "typical", "good": "good airing"}
BLD_LABEL = {"renovated": "renovated, tight", "altbau": "1960s uninsulated"}

_names = {f.name for f in font_manager.fontManager.ttflist}
FONT = "Segoe UI" if "Segoe UI" in _names else "DejaVu Sans"
plt.rcParams.update({"font.family": FONT, "text.color": TEXT, "axes.labelcolor": MUTED, "xtick.color": MUTED,
                     "ytick.color": MUTED, "axes.edgecolor": GRID, "axes.facecolor": BG, "figure.facecolor": BG,
                     "savefig.facecolor": BG, "axes.titlecolor": TEXT, "legend.facecolor": BG, "legend.edgecolor": GRID})


def _style(ax, title=None, size=11):
    ax.set_facecolor(BG)
    ax.grid(True, color=GRID, lw=0.8)
    for s in ax.spines.values():
        s.set_color(GRID)
    ax.tick_params(labelsize=size)
    if title:
        ax.set_title(title, loc="left", fontsize=size + 2, fontweight="bold", color=TEXT)


def post_figure(runs: dict, path: Path):
    """960x700: surface RH of the renovated flat (two weeks) and the mould index over the whole winter."""
    bad, good = runs[("renovated", "bad")], runs[("renovated", "good")]
    fig = plt.figure(figsize=(9.6, 7.0), dpi=100, facecolor=BG)
    fig.text(0.04, 0.945, "Same flat, same winter: bad habits vs good airing", fontsize=14.5, fontweight="bold", color=TEXT)
    fig.text(0.04, 0.912, "Simulated tight renovated flat, Zurich. Outdoor weather: Open-Meteo, Oct 2025 - Mar 2026",
             fontsize=11, color=MUTED)
    ax1 = fig.add_axes([0.085, 0.545, 0.885, 0.29])
    win = slice("2026-01-05", "2026-01-18")
    for df, col, lab in ((bad, RED, "bad habits"), (good, GREEN, "good airing")):
        ax1.plot(df.loc[win].index, df.loc[win, "rh_surf"].clip(upper=100), color=col, lw=2.4, label=f"{lab}")
        ax1.plot(df.loc[win].index, df.loc[win, "rh_in"], color=col, lw=1.2, ls=":", alpha=0.9)
    ax1.axhline(80, color=AMBER, ls="--", lw=1.6, label="80 %: mould can grow")
    ax1.set_ylim(20, 104)
    ax1.set_ylabel("relative humidity, %", fontsize=11)
    ax1.set_title("Cold corner RH (solid) and room RH (dotted), two January weeks", loc="left", fontsize=12, color=TEXT)
    ax1.legend(loc="lower right", fontsize=11, ncol=3, frameon=False, labelcolor=TEXT, columnspacing=1.0, handlelength=1.6)
    _style(ax1)
    ax1.set_title("Cold-corner wall RH (solid) and room RH (dotted), two January weeks", loc="left", fontsize=12, color=TEXT)
    ax1.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b", tz=TZ))
    ax2 = fig.add_axes([0.085, 0.10, 0.885, 0.31])
    ax2.plot(bad.index, bad["mould_idx"], color=RED, lw=2.6)
    ax2.plot(good.index, good["mould_idx"], color=GREEN, lw=2.6)
    ax2.axhline(1, color=AMBER, ls="--", lw=1.4)
    ax2.axhline(3, color=VIOLET, ls="--", lw=1.4)
    ax2.text(bad.index[20], 1.12, "1 = first microscopic growth", color=AMBER, fontsize=11)
    ax2.text(bad.index[20], 3.12, "3 = first visible mould", color=VIOLET, fontsize=11)
    ax2.text(bad.index[-1], bad["mould_idx"].iloc[-1] + 0.1, f"{bad['mould_idx'].iloc[-1]:.1f}", color=RED,
             fontsize=13, fontweight="bold", ha="right", va="bottom")
    ax2.text(good.index[-1], 0.25, f"{good['mould_idx'].max():.2f} max", color=GREEN, fontsize=13, fontweight="bold",
             ha="right")
    ax2.set_ylim(0, 6)
    ax2.set_ylabel("mould index (0-6)", fontsize=11)
    ax2.set_title("VTT mould index over the heating season", loc="left", fontsize=12, color=TEXT)
    _style(ax2)
    ax2.set_title("VTT mould index over the heating season", loc="left", fontsize=12, color=TEXT)
    ax2.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b", tz=TZ))
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)


def main_figure(res: dict, runs: dict, path: Path):
    fig, axs = plt.subplots(2, 2, figsize=(16, 9), dpi=100, facecolor=BG)
    fig.text(0.03, 0.965, "mould-risk-index: simulated flats x real Swiss winter weather", fontsize=19, fontweight="bold", color=TEXT)
    fig.text(0.03, 0.93, "Simulated indoor climate; outdoor data: Open-Meteo (CC BY 4.0), 15 Oct 2025 - 31 Mar 2026",
             fontsize=12, color=MUTED)
    ax = axs[0, 0]
    for (b, h), df in runs.items():
        ax.plot(df.index, df["mould_idx"], color=BEH_COL[h], lw=2.2, ls="-" if b == "renovated" else "--",
                label=f"{BLD_LABEL[b]}, {BEH_LABEL[h]}")
    ax.axhline(1, color=GREY, lw=1)
    ax.set_ylim(0, 6)
    ax.set_ylabel("mould index (0-6)", fontsize=12)
    ax.legend(fontsize=10, ncol=2, loc="upper right", bbox_to_anchor=(1.0, 0.80), frameon=False, labelcolor=TEXT)
    _style(ax, "Mould index, Zurich, 3 behaviours x 2 buildings", 12)
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%b", tz=TZ))

    ax = axs[0, 1]
    c = pd.DataFrame(res["cities"])
    cities = list(dict.fromkeys(c["city"]))
    combos = [("renovated", "bad"), ("renovated", "typical"), ("altbau", "bad")]
    cols = [RED, AMBER, VIOLET]
    w = 0.26
    x = np.arange(len(cities))
    for k, (b, h) in enumerate(combos):
        vals = [int(c[(c.city == ct) & (c.building == b) & (c.behaviour == h)]["days_m_ge_1"].iloc[0]) for ct in cities]
        bars = ax.bar(x + (k - 1) * w, vals, w, color=cols[k], label=f"{BLD_LABEL[b]}, {BEH_LABEL[h]}")
        for r, v in zip(bars, vals, strict=True):
            ax.text(r.get_x() + r.get_width() / 2, v + 3, str(v), ha="center", fontsize=9.5, color=TEXT)
    ax.set_xticks(x, [ct.capitalize() for ct in cities])
    ax.set_ylabel("days with mould index >= 1", fontsize=12)
    ax.set_ylim(0, 215)
    ax.legend(fontsize=10, frameon=False, labelcolor=TEXT, loc="upper center", ncol=3)
    _style(ax, "Cities (good airing: 0 days everywhere)", 12)

    ax = axs[1, 0]
    s = pd.DataFrame(res["sweeps"])
    for (b, h), g in s[s.change == "airing"].groupby(["building", "behaviour"]):
        g = g.sort_values("airing_min_per_day")
        ax.plot(g["airing_min_per_day"], g["days_m_ge_1"], marker="o", lw=2.2, color=BEH_COL[h],
                ls="-" if b == "renovated" else "--", label=f"{BLD_LABEL[b]}, {BEH_LABEL[h]}")
    ax.set_xlabel("airing, minutes per day (cross ventilation)", fontsize=12)
    ax.set_ylabel("days with mould index >= 1", fontsize=12)
    ax.legend(fontsize=10, frameon=False, labelcolor=TEXT)
    _style(ax, "How much airing is enough? (Zurich)", 12)

    ax = axs[1, 1]
    a = pd.DataFrame(res["sensing_agg"]).set_index("setup").loc[["room_generic", "room_known", "corner"]]
    x = np.arange(3)
    ax.bar(x - 0.18, a["false_alarm_per_flat_month"], 0.36, color=AMBER, label="false alarms")
    ax.bar(x + 0.18, a["missed_per_flat_month"], 0.36, color=RED, label="missed events")
    ax.set_xticks(x, ["room sensor\nassumed fRsi 0.70", "room sensor\nknown fRsi", "cold-corner\nsensor"])
    ax.set_ylabel("episodes per flat and month", fontsize=12)
    ax.legend(fontsize=11, frameon=False, labelcolor=TEXT)
    _style(ax, "Sensor placement vs alert quality", 12)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    fig.savefig(path, dpi=100, facecolor=BG)
    plt.close(fig)


def make_figures(res: dict, out_dir: Path):
    out_dir.mkdir(parents=True, exist_ok=True)
    runs = res["_runs"]
    main_figure(res, runs, out_dir / "figure.png")
    post_figure(runs, out_dir / "post-figure.png")
