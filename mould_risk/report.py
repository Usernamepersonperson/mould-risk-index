"""Tenant/landlord-neutral weekly report (jinja2). Data stays on the local device."""

from __future__ import annotations

import numpy as np
import pandas as pd
from jinja2 import Environment, StrictUndefined

from .advice import Advice, Reading, advise
from .alerts import count_alerts
from .i18n import REPORT, tr

TEMPLATE = """# {{ t.title }}

**{{ t.flat }}:** {{ flat }}
**{{ t.period }}:** {{ start }} - {{ end }}

## {{ t.summary }}

| | |
|---|---|
| {{ t.mean_t }} | {{ "%.1f"|format(s.mean_t) }} |
| {{ t.mean_rh }} | {{ "%.0f"|format(s.mean_rh) }} |
| {{ t.hours_over_80 }} | {{ s.hours_over_80 }} |
| {{ t.mould_index }} | {{ "%.2f"|format(s.mould_index) }} |
| {{ t.alerts }} ({{ sev.watch }} / {{ sev.warn }} / {{ sev.critical }}) | {{ s.alerts.watch }} / {{ s.alerts.warn }} / {{ s.alerts.critical }} |
| {{ t.coverage }} | {{ "%.0f"|format(s.coverage) }} |

## {{ t.factors }}

- {{ t.moisture_load }}
- {{ t.surface_temp }}

## {{ t.actions }}

{% for a in advice -%}
- **{{ a.severity }}**: {{ a.text }}
{% endfor %}
---

{{ t.privacy }}

{{ t.disclaimer }}
"""

_env = Environment(undefined=StrictUndefined, autoescape=False, trim_blocks=False)  # noqa: S701 (markdown, not HTML)
_tpl = _env.from_string(TEMPLATE)


def weekly_summary(view: pd.DataFrame, frsi: float, t_out: pd.Series, rh_out: pd.Series) -> dict:
    from .psychro import abs_humidity

    ah_out = abs_humidity(t_out.to_numpy(), rh_out.to_numpy())
    excess = float(np.nanmean(view["ah_in_est"].to_numpy() - ah_out))
    return {
        "mean_t": float(view["t_in_est"].mean()),
        "mean_rh": float(view["rh_in_est"].mean()),
        "hours_over_80": int((view["rh_surf_est"] >= 80.0).sum()),
        "mould_index": float(view["m_est"].iloc[-1]),
        "alerts": count_alerts(view["rh_surf_est"], view["m_est"]),
        "coverage": float(view["coverage_pct"].iloc[0]),
        "moisture_excess": excess,
        "frsi": frsi,
    }


def worst_hour_advice(view: pd.DataFrame, t_out: pd.Series, rh_out: pd.Series, frsi: float) -> list[Advice]:
    if view["rh_surf_est"].notna().sum() == 0:
        return [Advice("check_sensor", "info", {"hours": len(view)})]
    i = int(np.nanargmax(view["rh_surf_est"].to_numpy()))
    over = 0
    srh = view["rh_surf_est"].to_numpy()
    while i - over >= 0 and srh[i - over] >= 80.0:
        over += 1
    r = Reading(
        float(view["t_in_est"].iloc[i]), float(view["rh_in_est"].iloc[i]), float(t_out.iloc[i]), float(rh_out.iloc[i]),
        frsi, float(view["m_est"].iloc[i]), over,
    )
    return advise(r)


def render_weekly(flat: str, view: pd.DataFrame, t_out: pd.Series, rh_out: pd.Series, frsi: float, lang: str) -> str:
    s = weekly_summary(view, frsi, t_out, rh_out)
    advice = worst_hour_advice(view, t_out, rh_out, frsi)
    from .i18n import SEVERITY

    t = {k: tr(REPORT, k, lang) for k in REPORT if k not in ("moisture_load", "surface_temp")}
    t["moisture_load"] = tr(REPORT, "moisture_load", lang, v=s["moisture_excess"])
    t["surface_temp"] = tr(REPORT, "surface_temp", lang, v=s["frsi"])
    adv = [{"severity": SEVERITY[a.severity][lang], "text": a.text(lang)} for a in advice]
    return _tpl.render(
        t=t,
        sev={k: SEVERITY[k][lang] for k in ('watch', 'warn', 'critical')},
        s=s,
        flat=flat,
        start=view.index[0].strftime("%Y-%m-%d"),
        end=view.index[-1].strftime("%Y-%m-%d"),
        advice=adv,
    )
