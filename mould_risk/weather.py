"""Outdoor hourly temperature and relative humidity for Swiss cities.

Source: Open-Meteo Historical Weather API (https://open-meteo.com/en/docs/historical-weather-api),
licence CC BY 4.0, attribution "Weather data by Open-Meteo.com". The archive is built from reanalysis
and numerical weather model data, not from a single station measurement, and is gridded (a city value
is the grid cell around the coordinates, adjusted to the model elevation). Times are stored in UTC.

The CSVs in data/weather/ are committed (small), so the demo runs offline. `python -m mould_risk fetch`
re-downloads them.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "weather"
START = "2025-10-15"
END = "2026-03-31"
API = "https://archive-api.open-meteo.com/v1/archive"

CITIES = {
    "zurich": {"label": "Zurich", "lat": 47.3769, "lon": 8.5417},
    "basel": {"label": "Basel", "lat": 47.5596, "lon": 7.5886},
    "bern": {"label": "Bern", "lat": 46.9480, "lon": 7.4474},
    "geneva": {"label": "Geneva", "lat": 46.2044, "lon": 6.1432},
    "lugano": {"label": "Lugano", "lat": 46.0037, "lon": 8.9511},
    "davos": {"label": "Davos", "lat": 46.8027, "lon": 9.8360},
}
SOURCE = "Open-Meteo Historical Weather API (CC BY 4.0), reanalysis-based"


def fetch_city(key: str, start: str = START, end: str = END, timeout: int = 60) -> pd.DataFrame:
    c = CITIES[key]
    q = urllib.parse.urlencode(
        {
            "latitude": c["lat"],
            "longitude": c["lon"],
            "start_date": start,
            "end_date": end,
            "hourly": "temperature_2m,relative_humidity_2m",
            "timezone": "GMT",
        }
    )
    with urllib.request.urlopen(f"{API}?{q}", timeout=timeout) as r:  # noqa: S310 (fixed https host)
        payload = json.load(r)
    h = payload["hourly"]
    df = pd.DataFrame({"time": h["time"], "temp_c": h["temperature_2m"], "rh_pct": h["relative_humidity_2m"]})
    df.attrs["elevation_m"] = payload.get("elevation")
    return df


def fetch_all(out_dir: Path = DATA_DIR) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    meta = {}
    for key in CITIES:
        df = fetch_city(key)
        df.to_csv(out_dir / f"{key}.csv", index=False)
        meta[key] = {"rows": len(df), "elevation_m": df.attrs.get("elevation_m")}
    (out_dir / "meta.json").write_text(
        json.dumps({"source": SOURCE, "start": START, "end": END, "cities": meta}, indent=1), encoding="utf-8"
    )
    return meta


def load_city(key: str, data_dir: Path = DATA_DIR) -> pd.DataFrame:
    """Hourly outdoor series indexed by Europe/Zurich local time with columns temp_c, rh_pct."""
    path = Path(data_dir) / f"{key}.csv"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing: run `python -m mould_risk fetch`")
    df = pd.read_csv(path)
    idx = pd.to_datetime(df["time"], utc=True).dt.tz_convert("Europe/Zurich")
    df = df.drop(columns="time")
    df.index = idx
    df.index.name = "time"
    if df[["temp_c", "rh_pct"]].isna().any().any():
        df = df.interpolate(limit=6).dropna()
    return df
