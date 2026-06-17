"""NOAA CO-OPS loader -- water temperature at Beaufort/Duke Marine Lab (8656483).

Useful as an independent water-temperature comparison near DUML. NOTE: this
station has NO conductivity/salinity sensor. Uses the public CO-OPS Data API
directly via ``requests`` (no extra dependency required).
"""
from __future__ import annotations

import pandas as pd
import requests

_API = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter"


def load_water_temperature(station="8656483", begin_date="20240101",
                           end_date="20241231", units="metric",
                           interval="h", timeout=60):
    """Fetch water temperature for a CO-OPS station -> [datetime, temp_C, station].

    Dates are YYYYMMDD. ``interval='h'`` (hourly) allows up to ~1 year per request;
    the default 6-minute interval caps at ~31 days. For long spans call per-year
    and concatenate (see scripts/fetch_public_data.py).
    """
    params = {
        "product": "water_temperature",
        "application": "trees-to-seas",
        "station": station,
        "begin_date": begin_date,
        "end_date": end_date,
        "datum": "MLLW",
        "time_zone": "gmt",
        "units": units,
        "interval": interval,
        "format": "json",
    }
    r = requests.get(_API, params=params, timeout=timeout)
    r.raise_for_status()
    data = r.json().get("data", [])
    if not data:
        return pd.DataFrame(columns=["datetime", "temp_C", "station"])
    df = pd.DataFrame(data)
    out = pd.DataFrame({
        "datetime": pd.to_datetime(df["t"], errors="coerce"),
        "temp_C": pd.to_numeric(df["v"], errors="coerce"),
    })
    out["station"] = station
    return out.dropna(subset=["datetime"]).reset_index(drop=True)
