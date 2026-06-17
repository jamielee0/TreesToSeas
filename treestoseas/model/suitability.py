"""Drive the per-species envelopes with environmental time series to produce a
continuous Habitat Suitability Index (HSI) and detect stress events.

This is the engine that turns water from a static backdrop into a dynamic,
predictive habitat layer: HSI(t, site) for each focal species.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .envelopes import factor_suitability, combine_hsi

CANONICAL_FACTORS = ["temp_C", "salinity_ppt", "DO_mgL", "pH"]


def suitability_timeseries(df, species_cfg, combiner="geometric_mean",
                           datetime_col="datetime", site_col="site"):
    """Compute HSI and per-factor suitability for one species over a time series.

    Parameters
    ----------
    df : pandas.DataFrame
        Tidy (wide) environmental data with a datetime column, an optional site
        column, and one column per canonical factor present (``temp_C`` etc).
    species_cfg : dict
        One species entry from ``config/species.yaml`` (must contain ``factors``).
    combiner : str
        HSI combiner passed to :func:`combine_hsi`.

    Returns
    -------
    pandas.DataFrame
        Copy of ``df`` with added ``suit_<factor>`` columns and an ``HSI`` column.
    """
    factors = species_cfg["factors"]
    out = df.copy()

    values = {f: out[f].to_numpy() for f in factors if f in out.columns}
    if not values:
        raise ValueError(
            "No environmental factors found in dataframe. Expected some of "
            f"{list(factors)}; got columns {list(out.columns)}."
        )

    scores = factor_suitability(values, factors)
    for f, s in scores.items():
        out[f"suit_{f}"] = s

    out["HSI"] = combine_hsi(scores, method=combiner)
    return out


def detect_stress_events(hsi_df, threshold=0.2, min_consecutive=3,
                         hsi_col="HSI", datetime_col="datetime", site_col="site"):
    """Find runs where HSI stays below ``threshold`` for >= ``min_consecutive`` rows.

    Assumes rows are (approximately) daily and ordered. Returns one record per
    stress event with start/end timestamps, duration, and minimum HSI reached.
    """
    events = []
    df = hsi_df.copy()
    if site_col not in df.columns:
        df[site_col] = "all"

    for site, g in df.groupby(site_col):
        g = g.sort_values(datetime_col).reset_index(drop=True)
        stressed = (g[hsi_col] < threshold).to_numpy()
        i = 0
        n = len(g)
        while i < n:
            if stressed[i]:
                j = i
                while j + 1 < n and stressed[j + 1]:
                    j += 1
                run_len = j - i + 1
                if run_len >= min_consecutive:
                    window = g.iloc[i:j + 1]
                    events.append({
                        "site": site,
                        "start": window[datetime_col].iloc[0],
                        "end": window[datetime_col].iloc[-1],
                        "duration_rows": int(run_len),
                        "min_HSI": float(np.nanmin(window[hsi_col])),
                        "mean_HSI": float(np.nanmean(window[hsi_col])),
                    })
                i = j + 1
            else:
                i += 1
    return pd.DataFrame(events)
