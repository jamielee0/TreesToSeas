"""Harmonization & QC: turn heterogeneous loads into one tidy, daily-resampled table.

Keeps the spirit of the survey-design critique honest: we resample to a common
cadence, carry coverage information, and never silently paper over gaps.
"""
from __future__ import annotations

import pandas as pd

from .ty_oysterdata import map_to_canonical

# Plausible physical ranges for a coastal NC estuary (used for light QC clipping).
DEFAULT_QC_RANGES = {
    "temp_C": (-2.0, 45.0),
    "salinity_ppt": (0.0, 45.0),
    "DO_mgL": (0.0, 20.0),
    "pH": (5.0, 9.5),
    "precip_mm": (0.0, 500.0),
}


def to_canonical_columns(df, canonical_vars):
    """Rename raw wide columns to canonical names where a mapping exists."""
    renames = {}
    for col in df.columns:
        canon = map_to_canonical(col, canonical_vars)
        if canon and canon != col:
            renames[col] = canon
    return df.rename(columns=renames)


def qc_clip(df, ranges=None):
    """Set out-of-range physical values to NaN (does not drop rows)."""
    ranges = ranges or DEFAULT_QC_RANGES
    out = df.copy()
    for col, (lo, hi) in ranges.items():
        if col in out.columns:
            bad = (out[col] < lo) | (out[col] > hi)
            out.loc[bad, col] = pd.NA
    return out


def resample_daily(df, datetime_col="datetime", site_col="site", how="mean"):
    """Resample a wide environmental frame to daily means per site.

    Returns a frame with one row per (site, day) and a daily ``datetime`` (the day).
    Non-numeric columns are dropped.
    """
    out = df.copy()
    out[datetime_col] = pd.to_datetime(out[datetime_col], errors="coerce")
    out = out.dropna(subset=[datetime_col])
    if site_col not in out.columns:
        out[site_col] = "all"

    value_cols = [c for c in out.columns
                  if c not in (datetime_col, site_col)
                  and pd.api.types.is_numeric_dtype(out[c])]

    frames = []
    for site, g in out.groupby(site_col):
        g = g.set_index(datetime_col).sort_index()
        daily = getattr(g[value_cols].resample("1D"), how)()
        daily[site_col] = site
        frames.append(daily.reset_index())
    result = pd.concat(frames, ignore_index=True) if frames else out
    return result.sort_values([site_col, datetime_col]).reset_index(drop=True)
