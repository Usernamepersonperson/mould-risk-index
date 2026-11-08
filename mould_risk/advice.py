"""Rule-based advice engine: reading in, plain-language actions out (de/fr/it/en).

The engine is deliberately a small, auditable rule set, not a model. Every rule states the physical
reason, and `air_useless` stops it from recommending airing when outdoor air is as moist as indoor air
(which does happen on foggy, mild days).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .i18n import ADVICE, tr
from .psychro import abs_humidity
from .surface import frsi_required, setpoint_raise_needed, surface_rh

SEV_ORDER = {"info": 0, "watch": 1, "warn": 2, "critical": 3}


@dataclass
class Reading:
    t_in: float
    rh_in: float
    t_out: float
    rh_out: float
    frsi: float = 0.70  # assumed temperature factor at the monitored spot
    mould_index: float = 0.0
    hours_over_80: int = 0  # consecutive hours the estimated surface RH has been >= 80 %
    hours_since_data: int = 0
    frsi_measured: float | None = None  # if a surface sensor gives a measured value


@dataclass
class Advice:
    code: str
    severity: str
    params: dict = field(default_factory=dict)

    def text(self, lang: str = "en") -> str:
        return tr(ADVICE, self.code, lang, **self.params)


def surface_rh_of(r: Reading) -> float:
    return float(surface_rh(r.t_in, r.rh_in, r.t_out, r.frsi_measured or r.frsi))


def advise(r: Reading, watch_rh: float = 75.0, warn_rh: float = 80.0) -> list[Advice]:
    """Return advice sorted from most to least severe."""
    out: list[Advice] = []
    if r.hours_since_data > 6:
        out.append(Advice("check_sensor", "info", {"hours": r.hours_since_data}))
        return out
    srh = surface_rh_of(r)
    ah_in = float(abs_humidity(r.t_in, r.rh_in))
    ah_out = float(abs_humidity(r.t_out, r.rh_out))
    excess = ah_in - ah_out
    sev = "warn" if srh >= warn_rh else "watch"
    if r.mould_index >= 1.0 or r.hours_over_80 >= 72:
        sev = "critical"

    if srh < watch_rh and r.mould_index < 1.0:
        return [Advice("ok", "info")]

    # 1. airing: only if it actually removes moisture
    if excess >= 1.0:
        out.append(Advice("air_now", sev, {"minutes": 5 if excess >= 4.0 else 10, "excess": excess}))
    else:
        out.append(Advice("air_useless", "info", {"ah_in": ah_in, "ah_out": ah_out}))

    # 2. heating
    frsi = r.frsi_measured or r.frsi
    dk = setpoint_raise_needed(r.t_in, r.rh_in, r.t_out, frsi, target_rh=watch_rh)
    if dk is None:
        out.append(Advice("heat_not_enough", sev, {"surf_rh": srh}))
    elif dk > 0:
        out.append(Advice("heat_up", sev, {"dk": max(dk, 1.0), "surf_rh": srh}))
    if r.t_in < 17.0:
        out.append(Advice("min_temp", sev, {"t_in": r.t_in}))

    # 3. structural / behavioural context
    if excess >= 5.0:
        out.append(Advice("reduce_moisture", "watch", {"excess": excess}))
    if r.hours_over_80 >= 24:
        out.append(Advice("move_furniture", "watch"))
    if sev == "critical" or (dk is None and r.hours_over_80 >= 24):
        out.append(Advice("notify_manager", "critical"))
    out.sort(key=lambda a: -SEV_ORDER[a.severity])
    return out


def required_frsi(r: Reading, limit: float = 80.0) -> float:
    """Minimum temperature factor that keeps the surface under `limit` % in the current conditions."""
    return float(frsi_required(r.t_in, r.rh_in, r.t_out, limit))
